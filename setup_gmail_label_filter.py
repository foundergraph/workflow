#!/usr/bin/env python3
"""
Setup Gmail label and filter for VC newsletters.
Requires service account with Domain-Wide Delegation and these scopes:
- https://www.googleapis.com/auth/gmail.settings.basic
- https://www.googleapis.com/auth/gmail.labels
"""

import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Paths
CREDENTIALS_PATH = os.getenv("FGAI_GMAIL_CREDENTIALS", "/home/ubuntu/.openclaw/email-assistant/credentials.json")
MONITOR_EMAIL = os.getenv("FGAI_GMAIL_MONITOR_EMAIL", "jessie@foundergraphai.com")
LABEL_NAME = "VC-Newsletters"

SCOPES = [
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.labels'
]

def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"Error: credentials not found at {CREDENTIALS_PATH}")
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=SCOPES
    )
    delegated = creds.with_subject(MONITOR_EMAIL)

    service = build('gmail', 'v1', credentials=delegated, cache_discovery=False)

    # 1. Check existing labels; create if needed
    labels_resp = service.users().labels().list(userId='me').execute()
    labels = labels_resp.get('labels', [])
    label_id = None
    for l in labels:
        if l['name'] == LABEL_NAME:
            label_id = l['id']
            print(f"Label '{LABEL_NAME}' exists (id: {label_id})")
            break

    if not label_id:
        label_body = {
            "name": LABEL_NAME,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        }
        created = service.users().labels().create(userId='me', body=label_body).execute()
        label_id = created['id']
        print(f"Created label '{LABEL_NAME}' (id: {label_id})")

    # 2. Create filter
    senders = [
        "techcrunch@inside.com",
        "newsletter@theinformation.com",
        "ben@benedictevans.com",
        "note@stratechery.com",
        "newsletter@thegeneralist.co",
        "hello@future.com",
        "batch@deeplearning.ai",
        "alphasignal@cbinsights.com"
    ]
    from_clause = " OR ".join(senders)
    filter_body = {
        "criteria": {
            "from": f"({from_clause})"
        },
        "action": {
            "addLabelIds": [label_id],
            # "markImportant": True,  # optional
            # "removeLabelIds": ["INBOX"]  # optional, to skip inbox
        }
    }

    # Check if filter already exists (by criteria) — skip if present
    filters_resp = service.users().settings().filters().list(userId='me').execute()
    filters = filters_resp.get('filter', [])
    for f in filters:
        crit = f.get('criteria', {})
        if crit.get('from') == filter_body['criteria']['from']:
            print(f"Filter already exists (id: {f['id']})")
            print("Done.")
            return

    # Create filter
    created = service.users().settings().filters().create(userId='me', body=filter_body).execute()
    print(f"Created filter (id: {created.get('id')})")
    print("Done.")

if __name__ == "__main__":
    main()