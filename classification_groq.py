#!/usr/bin/env python3
import os
import argparse
import json
import logging
import random
import sys
import urllib.parse
from github import Github, GithubException
from groq import Groq, APIConnectionError, APIStatusError
from dotenv import load_dotenv

load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Command-line arguments parser
parser = argparse.ArgumentParser(description='Process GitHub issue.')
parser.add_argument('--fix-typos-comment', type=bool, default=False, help='Add comment with fixed typos')
parser.add_argument('--issue-number', type=int, required=True, help='GitHub issue number')
parser.add_argument('--repo-name', type=str, required=True, help='GitHub repository name (owner/repo)')
args = parser.parse_args()

# Ensure required arguments are provided
if not args.issue_number:
    logging.error('GitHub issue number is required')
    sys.exit(1)

if not args.repo_name:
    logging.error('GitHub repository name is required')
    sys.exit(1)

# Initialize GitHub and Groq clients
github_token = os.environ['GITHUB_TOKEN']
groq_api_key = os.environ['GROQ_API_KEY']
repo_name = args.repo_name
issue_number = args.issue_number

g = Github(github_token)
repo = g.get_repo(repo_name)
issue = repo.get_issue(number=issue_number)

# Gather issue content, including comments
def gather_issue_content(issue):
    content = issue.title + '\n\n' + issue.body
    comments = issue.get_comments()
    for comment in comments:
        content += '\n\n' + comment.body
    return content

# Generate a random hex color
def generate_random_color():
    return ''.join(random.choices('0123456789ABCDEF', k=6))

# Ensure the label exists or create a new one if it doesn't
def ensure_label_exists(repo, label_name):
    label_name = label_name[:50]  # Ensure label name does not exceed 50 characters
    try:
        return repo.get_label(label_name)
    except GithubException as e:
        if e.status == 404:
            try:
                return repo.create_label(name=label_name, color=generate_random_color())
            except GithubException as create_error:
                logging.error(f"Failed to create label '{label_name}': {create_error}")
                return None
        else:
            logging.error(f"Failed to get label '{label_name}': {e}")
            return None

# Get classification labels and corrected text from Groq API
def get_classification_labels_and_corrected_text(client, issue_content):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a helpful project manager. Your goals are:\n"
                        "1. Triage a GitHub issue by adding appropriate labels based on the issue's title, body, and comments. "
                        "Apply a maximum of 5 labels with 1 or 2 words separated by hyphens or underscores. You can be creative and "
                        "use GitHub-supported emojis. Your final response should only include the list of labels you want to apply, separated by commas, and nothing else.\n"
                        "2. Validate and fix any grammar issues in the issue title and body, removing typos and ensuring it is in valid GitHub-flavored markdown format.\n"
                        "3. Provide an alternative text for the issue body with corrections and improved formatting. Respond with a JSON object containing 'labels' and 'corrected_text'."
                    ),
                },
                {
                    "role": "user",
                    "content": issue_content,
                }
            ],
            model="llama3-8b-8192",
        )
        logging.info("API Response received")
        response = chat_completion.choices[0].message.content.strip()
        response_json = json.loads(response)
        labels = response_json.get('labels', [])
        corrected_text = response_json.get('corrected_text', None)
        return labels, corrected_text
    except (APIConnectionError, APIStatusError) as e:
        logging.error(f"Error with Groq API: {e}")
        return [], None
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON response: {e}")
        return [], None

# Check if a matching comment already exists
def comment_exists(issue, comment_content):
    for comment in issue.get_comments():
        if comment_content in comment.body:
            return True
    return False

# Add a collapsible comment with the corrected text
def add_collapsible_comment(issue, corrected_text):
    collapsible_comment = (
        "<details>\n"
        "<summary>Suggested improvements for the issue</summary>\n\n"
        f"{corrected_text}\n"
        "</details>"
    )
    if not comment_exists(issue, "Suggested improvements for the issue"):
        issue.create_comment(collapsible_comment)

# Main script execution
def main():
    issue_content = gather_issue_content(issue)
    client = Groq(api_key=groq_api_key)
    labels, corrected_text = get_classification_labels_and_corrected_text(client, issue_content)

    if not labels:
        logging.info("No labels generated from Groq API.")
        return

    ensured_labels = [ensure_label_exists(repo, label) for label in labels]
    valid_labels = [label for label in ensured_labels if label]

    if valid_labels:
        issue.add_to_labels(*valid_labels)
        comment_content = f"Issue classified with labels: {', '.join(label.name for label in valid_labels)}"
        if not comment_exists(issue, "Issue classified with labels"):
            issue.create_comment(comment_content)

    if corrected_text:
        issue.edit(title=corrected_text['title'])
        if args.fix_typos_comment:
            add_collapsible_comment(issue, corrected_text['body'])
    else:
        logging.info("No corrected text provided by Groq API.")

if __name__ == "__main__":
    main()
