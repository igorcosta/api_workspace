#!/usr/bin/env python3
import os
import argparse
import json
import logging
import random
import sys
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

# Generate a random hex color
def generate_random_color():
    return ''.join(random.choices('0123456789ABCDEF', k=6))

# Ensure the label exists or create a new one if it doesn't
def ensure_label_exists(repo, label_name, color=None):
    label_name = label_name[:50]  # Ensure label name does not exceed 50 characters
    if not color:
        color = generate_random_color()
    try:
        return repo.get_label(label_name)
    except GithubException as e:
        if e.status == 404:
            try:
                return repo.create_label(name=label_name, color=color)
            except GithubException as create_error:
                logging.error(f"Failed to create label '{label_name}': {create_error}")
                return None
        else:
            logging.error(f"Failed to get label '{label_name}': {e}")
            return None

# Extract JSON part from Groq API response
def extract_json_from_response(response):
    try:
        start_idx = response.index('{')
        end_idx = response.rindex('}') + 1
        json_str = response[start_idx:end_idx]
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        logging.error(f"Error extracting JSON from response: {e}")
        return None

# Get classification labels and corrected text from Groq API
def get_classification_labels_and_corrected_text(client, issue_data):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful project manager. Your goals are:\n"
                        "1. Triage a GitHub issue by adding appropriate labels based on the issue's title and body, including comments. "
                        "Apply a maximum of 5 labels with 1 or 2 words separated by hyphens or underscores. Your response should include only the list of labels you want to apply, separated by commas.\n"
                        "2. Act as a document reviewer focusing on fixing any grammar issues and typos in the issue title and body, ensuring they are in valid GitHub-flavored markdown format.\n"
                        "3. Provide corrected text for the issue body and title with improved formatting. Respond with a JSON object containing 'labels', 'corrected_text', and 'title'.\n"
                        "4. For the title, you MUST keep the same wording, correcting ONLY typos and grammar issues, if there's a word that you don't have in your knowledge don't rewrite, it must be special and always starts with Upper case, just leave it alone. If there are no corrections, return the original title, but NEVER change the title wording.\n"
                        "If there are no labels to apply, return an empty object. Here is an example of the expected JSON response:\n"
                        "{\n"
                        '  "labels": "label1, label2, label3",\n'
                        '  "corrected_text": "Here is the corrected issue body.",\n'
                        '  "title": "Corrected Issue Title"\n'
                        "}"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(issue_data),
                }
            ],
            model="llama3-8b-8192",
        )
        logging.info("API Response received")
        response = chat_completion.choices[0].message.content.strip()
        
        # Log the raw response for debugging purposes
        logging.info(f"Raw API response: {response}")
        
        response_json = extract_json_from_response(response)
        if response_json:
            labels = response_json.get('labels', '').split(', ') if response_json.get('labels') else []
            corrected_text = response_json.get('corrected_text', None)
            title = response_json.get('title', None)
        else:
            labels = []
            corrected_text = None
            title = None
        return labels, corrected_text, title
    except (APIConnectionError, APIStatusError) as e:
        logging.error(f"Error with Groq API: {e}")
        sys.exit(1)

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
    issue_data = {
        "title": issue.title,
        "body": issue.body,
        "comments": [comment.body for comment in issue.get_comments()]
    }

    client = Groq(api_key=groq_api_key)
    labels, corrected_text, title = get_classification_labels_and_corrected_text(client, issue_data)

    if not labels:
        logging.info("No labels generated from Groq API. Applying default 'Triage' label.")
        labels = ['triage']
        color = generate_random_color()
    else:
        color = None

    ensured_labels = [ensure_label_exists(repo, label, color) for label in labels]
    valid_labels = [label for label in ensured_labels if label]

    if valid_labels:
        issue.add_to_labels(*valid_labels)
        comment_content = f"Issue classified with labels: {', '.join(label.name for label in valid_labels)}"
        if not comment_exists(issue, "Issue classified with labels"):
            issue.create_comment(comment_content)

    if title:
        issue.edit(title=title)
    if corrected_text:
        issue.edit(body=corrected_text)
        if args.fix_typos_comment:
            add_collapsible_comment(issue, corrected_text)
    else:
        logging.info("No corrected text or title provided by Groq API.")
        sys.exit(1)

if __name__ == "__main__":
    main()
