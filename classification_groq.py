#!/usr/bin/env python3
import os
import urllib.parse
from github import Github, GithubException
from groq import Groq, APIConnectionError, APIStatusError

g = Github(os.environ['GITHUB_TOKEN'])
repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
issue = repo.get_issue(number=int(os.environ['ISSUE_NUMBER']))

# Gather issue content, including comments
issue_content = issue.title + '\n\n' + issue.body
comments = issue.get_comments()
for comment in comments:
    issue_content += '\n\n' + comment.body

def ensure_label_exists(repo, label_name):
    label_name = label_name[:50]  # Ensure label name does not exceed 50 characters
    try:
        return repo.get_label(label_name)
    except GithubException.UnknownObjectException:
        try:
            return repo.create_label(name=label_name, color='000000')
        except GithubException as e:
            print(f"Failed to create label '{label_name}': {e}")
            return None

client = Groq(api_key=os.environ['GROQ_API_KEY'])

try:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You're a helpful project manager and your goal is to triage GitHub issues by adding respective labels to the issues as they're updated.\n\nClassify each issue by checking the appropriate title, body and description, comments as a whole and propose of it. Apply maximum 5 labels with 1 word or max 2 words separated by - or _, you can be creative if you will and add some GitHub supported emojis, you MUST answer with ONLY!!! the labels you want to apply, nothing else",
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
            labels.append(content)

    labels = list(set(labels))  # Remove duplicates
    ensured_labels = [ensure_label_exists(repo, label) for label in labels if label]
    issue.add_to_labels(*[label for label in ensured_labels if label])
    issue.create_comment(f"Issue classified with labels: {', '.join(label.name for label in ensured_labels if label)}")
except APIConnectionError as e:
    print("Failed to connect to Groq API:", e)
except APIStatusError as e:
    print(f"API Error {e.status_code}: {e.response}")
