"""Utilities for Gmail access and email sending."""

import os
import base64
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta


def get_gmail_service(credentials_file: str, user_email: str, scopes: List[str]):
    """Authenticate and return Gmail service."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=scopes
    )
    delegated = creds.with_subject(user_email)
    return build('gmail', 'v1', credentials=delegated, cache_discovery=False)


def fetch_gmail_messages(service, query: str, max_results: int = 20) -> List[Dict]:
    """Fetch message metadata matching query."""
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = []
    for msg_meta in results.get('messages', []):
        msg = service.users().messages().get(userId='me', id=msg_meta['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
        headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
        messages.append({
            'id': msg['id'],
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'date': headers.get('Date', '')
        })
    return messages


def get_message_body(service, message_id: str) -> str:
    """Get full plain text body of a message."""
    full = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    body = ""
    payload = full.get('payload', {})
    parts = payload.get('parts', [])
    if parts:
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    else:
        data = payload.get('body', {}).get('data', '')
        if data:
            body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return body


def send_email(to_email: str, subject: str, body: str, credentials_file: str, monitor_email: str):
    """Send email via Gmail API using service account."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    delegated = creds.with_subject(monitor_email)
    service = build('gmail', 'v1', credentials=delegated, cache_discovery=False)

    message = f"""From: {monitor_email}
To: {to_email}
Subject: {subject}
Content-Type: text/plain; charset="UTF-8"

{body}"""
    encoded = base64.urlsafe_b64encode(message.encode('utf-8')).decode('utf-8')
    service.users().messages().send(userId='me', body={'raw': encoded}).execute()


def summarize_text(text: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    """Quick summarization via OpenAI (fallback to extractive if no key)."""
    if not api_key:
        # simple extractive fallback
        return text[:500] + "..."
    import openai
    openai.api_key = api_key
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a VC analyst. Extract funding rounds, startup launches, and business model innovations."},
            {"role": "user", "content": f"Summarize key points:\n\n{text[:4000]}"}
        ],
        temperature=0.3,
        max_tokens=500
    )
    return resp.choices[0].message.content.strip()