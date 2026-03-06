"""
config/settings.py
==================
Loads configuration from .env file.
"""

import os
from pathlib import Path


def load_settings() -> dict:
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print(f"⚠️  No .env file found at {env_path}")
        print("   Copy .env.example to .env and add your credentials.\n")
    else:
        _load_dotenv(env_path)

    settings = {
        # Anthropic
        "ANTHROPIC_API_KEY":  os.getenv("ANTHROPIC_API_KEY", ""),

        # Microsoft Graph / Outlook
        "MS_CLIENT_ID":       os.getenv("MS_CLIENT_ID", ""),
        "MS_TENANT_ID":       os.getenv("MS_TENANT_ID", "common"),
        "MS_TOKEN_CACHE":     os.getenv("MS_TOKEN_CACHE", ".ms_token_cache.json"),

        # Evernote
        "EVERNOTE_TOKEN":     os.getenv("EVERNOTE_TOKEN", ""),
        "EVERNOTE_NOTEBOOK":  os.getenv("EVERNOTE_NOTEBOOK", ""),
        "EVERNOTE_SANDBOX":   os.getenv("EVERNOTE_SANDBOX", "false").lower() == "true",

        # Jira
        "JIRA_BASE_URL":               os.getenv("JIRA_BASE_URL", ""),
        "JIRA_EMAIL":                  os.getenv("JIRA_EMAIL", ""),
        "JIRA_API_TOKEN":              os.getenv("JIRA_API_TOKEN", ""),
        "JIRA_ASSIGNEE_ACCOUNT_ID":    os.getenv("JIRA_ASSIGNEE_ACCOUNT_ID", "618d7b2af1ff560069e000d6"),

        # Slack (optional)
        "SLACK_BOT_TOKEN":    os.getenv("SLACK_BOT_TOKEN", ""),
        "SLACK_CHANNEL_ID":   os.getenv("SLACK_CHANNEL_ID", ""),

        # Behavior
        "EMAIL_MAX_FETCH":    int(os.getenv("EMAIL_MAX_FETCH", "50")),
        "EMAIL_FOLDERS":      os.getenv("EMAIL_FOLDERS", "inbox").split(","),
        "YOUR_NAME":          os.getenv("YOUR_NAME", ""),
        "YOUR_CLIENTS":       os.getenv("YOUR_CLIENTS", "").split(","),
    }

    _validate(settings)
    return settings


def _validate(settings: dict):
    if not settings["ANTHROPIC_API_KEY"]:
        print("❌ ANTHROPIC_API_KEY is required.")
        raise SystemExit(1)

    warnings = []
    if not settings["MS_CLIENT_ID"]:
        warnings.append("MS_CLIENT_ID (Outlook won't work)")
    if not settings["EVERNOTE_TOKEN"]:
        warnings.append("EVERNOTE_TOKEN (Evernote won't work)")
    if not settings["JIRA_BASE_URL"]:
        warnings.append("JIRA_BASE_URL (Jira integration disabled)")
    if settings["JIRA_BASE_URL"] and not settings["JIRA_API_TOKEN"]:
        warnings.append("JIRA_API_TOKEN (required when JIRA_BASE_URL is set)")

    for w in warnings:
        print(f"⚠️  Missing: {w}")
    if warnings:
        print()


def _load_dotenv(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
