#!/usr/bin/env python3
import os
import re
from openai import OpenAI, OpenAIError
import logging
import json

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SESSION_SUMMARY_TEMPLATE = """You are a proficient writer and summarizer. Generate a short summary of the following conversation between Alice and Bob.
Even if there are various messages from both the user and the assistant, always format your response in the following form:\n

### Alice: [inquired about, asked for, was interested in] [...]\n
### Bob: [answered with, provided, replied with] [...]\n\n

Please restrict yourself to at most two sentences for Alice and two sentences for Bob, there is no need to replicate source code blocks, only their description suffice.
"""

def format_into_alice_and_bob(messages):
    formatted_messages = []
    for message in [msg for msg in messages if isinstance(msg, dict) and 'role' in msg]:
        role = "**user**" if message['role'] == "user" else "**assistant**"
        formatted_messages.append(f"{role}: {message['content']}")
    return "\n".join(formatted_messages)

def format_into_user_and_assistant(messages):
    formatted_messages = []
    for message in [msg for msg in messages if isinstance(msg, dict) and 'role' in msg]:
        role = "**User**" if message['role'] == "user" else "**Assistant**"
        content = message['content'].replace('\n', ' ')
        formatted_messages.append(f"{role}: {content}")
    return "\n\n".join(formatted_messages)

def generate_summary(session):
    # Check if summary already exists
    if 'summary' in session:
        return session['summary']

    try:
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": SESSION_SUMMARY_TEMPLATE},
                {"role": "user", "content": format_into_alice_and_bob(session.get('messages', []))}
            ],
            "max_tokens": 120,
            "temperature": 0.7
        }
        response = client.chat.completions.create(**payload)
        summary = response.choices[0].message.content or ''

        summary.replace("### Alice", "**User**").replace("### Bob", "\n**Assistant**")

    except OpenAIError as err:
        logging.error("OpenAIError: %s", err)

    summary_text = summary.strip()
    return summary_text


def save_session(session):
    with open('sessions.jsonl', 'a') as file:
        file.write(json.dumps(session) + '\n')


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], 'r') as f:
        jsonl = [json.loads(line) for line in f.read().split('\n')]
        for o in jsonl:
            generate_summary(o.messages)
            save_session(o)
