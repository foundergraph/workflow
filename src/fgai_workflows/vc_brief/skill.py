"""OpenClaw skill: VC Daily Brief."""

from . import __version__
from .vc_brief import VCBrief

SKILL_NAME = "vc_brief"
SKILL_DESCRIPTION = "Daily VC briefing synthesized from subscribed newsletters"
SKILL_AUTHOR = "FounderGraph AI"
SKILL_VERSION = __version__

# Configuration schema (for OpenClaw manifest)
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "gmail_credentials": {"type": "string", "description": "Path to Gmail service account credentials JSON"},
        "monitor_email": {"type": "string", "description": "Mailbox to read newsletters from"},
        "recipient_email": {"type": "string", "description": "Where to send the daily brief"},
        "openai_api_key": {"type": "string", "description": "OpenAI API key for summarization (optional)"},
        "lookback_hours": {"type": "integer", "description": "Hours to look back for newsletters", "default": 24}
    },
    "required": ["gmail_credentials", "monitor_email", "recipient_email"]
}

def init(config: dict):
    """Initialize the skill (validate config)."""
    required = CONFIG_SCHEMA["required"]
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing config keys: {missing}")
    return True

def get_subscribers():
    """Return list of events this skill handles (none, it's a daily run)."""
    return []

def handle(action: str, params: dict, context: dict):
    """Handle explicit invocation (e.g., run now)."""
    if action != "run":
        raise ValueError(f"Unsupported action: {action}")
    vc = VCBrief(
        lookback_hours=params.get("lookback_hours", 24)
    )
    # Inject config from params or environment
    vc.credentials = params.get("gmail_credentials") or config.get("gmail_credentials")
    vc.monitor_email = params.get("monitor_email") or config.get("monitor_email")
    vc.recipient = params.get("recipient_email") or config.get("recipient_email")
    vc.openai_key = params.get("openai_api_key") or config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
    result = vc.run()
    return {"status": "completed", "brief": result}

# For direct testing
if __name__ == "__main__":
    import os
    cfg = {
        "gmail_credentials": os.getenv("FGAI_GMAIL_CREDENTIALS", "credentials.json"),
        "monitor_email": os.getenv("FGAI_GMAIL_MONITOR_EMAIL", "jessie@foundergraphai.com"),
        "recipient_email": os.getenv("FGAI_BRIEF_RECIPIENT", "yuchuanxu@hotmail.com"),
        "openai_api_key": os.getenv("OPENAI_API_KEY")
    }
    init(cfg)
    print(handle("run", {}, cfg))