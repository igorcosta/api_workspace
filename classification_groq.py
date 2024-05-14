#!/usr/bin/env python3
import os
import urllib.parse
import random
from github import Github, GithubException
from groq import Groq, APIConnectionError, APIStatusError
from dotenv import load_dotenv

load_dotenv()

# Initialize GitHub and Groq clients
github_token = os.environ['GITHUB_TOKEN']
groq_api_key = os.environ['GROQ_API_KEY']
repo_name = 'igorcosta/api_workspace'
issue_number = 8

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
                print(f"Failed to create label '{label_name}': {create_error}")
                return None
        else:
            print(f"Failed to get label '{label_name}': {e}")
            return None

# Get classification labels from Groq API
def get_classification_labels(client, issue_content):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You're a helpful project manager and your goal is to triage a GitHub issue by adding respective labels to the issue when they're created or updated.\n\nClassify the issue by checking the appropriate title, body, comments as a whole and the purpose of it. You MUST apply maximum 5 labels with 1 word or max 2 words separated by - or _, you can be creative if you want and add some GitHub supported emojis. Your final response MUST BE only with the list of labels you want to apply, nothing else in the response.",
                },
                {
                    "role": "user",
                    "content": issue_content,
                }
            ],
            model="llama3-8b-8192",
        )
        print("API Response:", chat_completion)
        labels = []
        for chunk in chat_completion.choices:
            content = chunk.message.content.strip()
            if content and len(labels) < 5:
                labels.extend(content.split(','))
        return list(set([label.strip() for label in labels if label]))  # Remove duplicates and trim whitespace
    except (APIConnectionError, APIStatusError) as e:
        print(f"Error with Groq API: {e}")
        return []

# Main script execution
def main():
    issue_content = gather_issue_content(issue)
    client = Groq(api_key=groq_api_key)
    labels = get_classification_labels(client, issue_content)

    if not labels:
        print("No labels generated from Groq API.")
        return

    ensured_labels = [ensure_label_exists(repo, label) for label in labels]
    valid_labels = [label for label in ensured_labels if label]

    if valid_labels:
        issue.add_to_labels(*valid_labels)
        issue.create_comment(f"Issue classified with labels: {', '.join(label.name for label in valid_labels)}")
    else:
        print("No valid labels to add to the issue.")

if __name__ == "__main__":
    main()
