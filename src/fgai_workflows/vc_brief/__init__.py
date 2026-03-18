"""VC Daily Brief — newsletter synthesis for founders & investors."""

from datetime import datetime, timedelta
from typing import List, Dict
import os
import json
import requests
from .utils import fetch_gmail_messages, summarize_text, send_email

# Newsletter senders we track (domain or full address)
NEWSLETTER_SENDERS = {
    "techcrunch@inside.com": "TechCrunch Daily Crunch",
    "newsletter@theinformation.com": "The Information",
    "ben@benedictevans.com": "Benedict Evans",
    "note@stratechery.com": "Stratechery",
    "newsletter@thegeneralist.co": "The Generalist",
    "hello@future.com": "Future (Felix Salmon)",
    "batch@deeplearning.ai": "The Batch (Andrew Ng)",
    "alphasignal@cbinsights.com": "AlphaSignal"
}

class VCBrief:
    """
    Fetch recent newsletters from Gmail, synthesize into a daily brief.

    Environment config:
    - FGAI_GMAIL_CREDENTIALS: path to credentials.json
    - FGAI_GMAIL_MONITOR_EMAIL: the monitored mailbox (jessie@foundergraphai.com)
    - FGAI_BRIEF_RECIPIENT: where to send the digest (user's personal email)
    - OPENAI_API_KEY: for summarization (or use Claude via openclaw)
    """

    def __init__(self, lookback_hours: int = 24):
        self.lookback = timedelta(hours=lookback_hours)
        self.credentials = os.getenv("FGAI_GMAIL_CREDENTIALS", "/home/ubuntu/.openclaw/email-assistant/credentials.json")
        self.monitor_email = os.getenv("FGAI_GMAIL_MONITOR_EMAIL", "jessie@foundergraphai.com")
        self.recipient = os.getenv("FGAI_BRIEF_RECIPIENT", "yuchuanxu@hotmail.com")
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def run(self) -> str:
        """Main entry: fetch, synthesize, send."""
        # 1. Fetch newsletter messages from past 24h
        messages = self._fetch_newsletter_messages()

        # 2. Summarize each and collect insights
        summaries = []
        for msg in messages:
            content = self._extract_content(msg)
            if not content:
                continue
            summary = self._synthesize_article(content, msg['From'], msg['Subject'])
            summaries.append(summary)

        # 3. Compile daily brief
        brief = self._compile_brief(summaries)

        # 4. Send to recipient
        self._send_brief(brief)

        return brief

    def _fetch_newsletter_messages(self) -> List[Dict]:
        """Query Gmail for unread messages from tracked newsletter senders within lookback window."""
        # Reuse Gmail API from email_bridge (avoid reinventing)
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            self.credentials,
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        delegated = creds.with_subject(self.monitor_email)
        service = build('gmail', 'v1', credentials=delegated, cache_discovery=False)

        # Build query: from:(@newsletter_senders) after:timestamp
        after = (datetime.utcnow() - self.lookback).timestamp()
        query_parts = [f"after:{int(after)}"]
        # OR together sender patterns
        sender_patterns = [f"from:{sender}" for sender in NEWSLETTER_SENDERS.keys()]
        query_parts.append("(" + " OR ".join(sender_patterns) + ")")
        query = " ".join(query_parts)

        results = service.users().messages().list(userId='me', q=query, maxResults=20).execute()
        messages = []
        for msg_meta in results.get('messages', []):
            msg = service.users().messages().get(userId='me', id=msg_meta['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            messages.append({
                'Id': msg['id'],
                'From': headers.get('From', ''),
                'Subject': headers.get('Subject', ''),
                'Date': headers.get('Date', '')
            })
        return messages

    def _extract_content(self, message: Dict) -> str:
        """Get plain text body of the email."""
        # Fetch full message
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_file(
            self.credentials,
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        delegated = creds.with_subject(self.monitor_email)
        service = build('gmail', 'v1', credentials=delegated, cache_discovery=False)
        full = service.users().messages().get(userId='me', id=message['Id'], format='full').execute()
        # Extract body (simplified)
        body = ""
        parts = full.get('payload', {}).get('parts', [])
        if parts:
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        import base64
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            data = full.get('payload', {}).get('body', {}).get('data', '')
            if data:
                import base64
                body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return body[:10000]  # limit size

    def _synthesize_article(self, content: str, sender: str, subject: str) -> Dict:
        """Use LLM to extract: funding rounds, startup names, business model insights."""
        prompt = f"""Extract from the following newsletter content:

1. Funding rounds: company name, amount, round, investors (if any)
2. New startup launches: name, tagline, sector
3. Business model innovations or notable trends

If none found, write "None notable".

Content:
---
{content[:2000]}
---

Respond in JSON:
{{
  "source": "{sender}",
  "subject": "{subject}",
  "funding": [{{"company":"...", "amount":"...", "round":"...", "investors":"..."}}],
  "startups": [{{"name":"...", "tagline":"...", "sector":"..."}}],
  "trends": ["..."]
}}"""
        # Call OpenAI or Claude
        # For now, return placeholder
        return {
            "source": sender,
            "subject": subject,
            "funding": [],
            "startups": [],
            "trends": []
        }

    def _compile_brief(self, summaries: List[Dict]) -> str:
        """Aggregate summaries into a formatted brief."""
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📊 VC Daily Brief — {today}\n"]
        # Group by type
        funding = []
        startups = []
        trends = []
        for s in summaries:
            funding.extend(s.get('funding', []))
            startups.extend(s.get('startups', []))
            trends.extend(s.get('trends', []))
        if funding:
            lines.append("💰 Funding Rounds")
            for f in funding:
                lines.append(f"- {f['company']}: {f['amount']} ({f['round']}) — {f['investors']}")
            lines.append("")
        if startups:
            lines.append("🚀 New Startups")
            for s in startups:
                lines.append(f"- {s['name']}: {s['tagline']} ({s['sector']})")
            lines.append("")
        if trends:
            lines.append("💡 Trends & Innovations")
            for t in trends:
                lines.append(f"- {t}")
            lines.append("")
        lines.append("Sources: " + ", ".join(NEWSLETTER_SENDERS.values()))
        return "\n".join(lines)

    def _send_brief(self, brief_text: str):
        """Email the brief to the recipient."""
        subject = f"VC Daily Brief — {datetime.now().strftime('%Y-%m-%d')}"
        send_email(
            to_email=self.recipient,
            subject=subject,
            body=brief_text,
            credentials_file=self.credentials,
            monitor_email=self.monitor_email
        )

def main():
    vc = VCBrief()
    brief = vc.run()
    print(brief)

if __name__ == "__main__":
    main()