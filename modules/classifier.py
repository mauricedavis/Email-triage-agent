"""
modules/classifier.py
=====================
Sends email + note data to Claude and returns a structured
morning briefing including Jira ticket recommendations.
"""

import json
import sys
import urllib.request
from datetime import datetime

CATEGORIES = {
    "urgent_action": "🔴 Urgent / Action Required",
    "client":        "🟠 Client",
    "internal":      "🟡 Internal / Team",
    "vendor_tools":  "🔵 Vendor & Tools",
    "fyi":           "⚪ FYI / No Action Needed",
}

# Client name → Jira project key mapping
CLIENT_PROJECT_MAP = {
    "seed foundation":              "SEED",
    "seed":                         "SEED",
    "michigan sbdc":                "MSBDC",
    "msbdc":                        "MSBDC",
    "gvsu":                         "MSBDC",
    "upenn":                        "USS",
    "upenn student success":        "USS",
    "uss":                          "USS",
    "aaum":                         "AMS",
    "aaum managed services":        "AMS",
    "midas":                        "AMS",      # primary; agent will also flag MIDAS Board
    "beatrice hahn":                "AMS",
    "darden":                       "DARDENEXED",
    "darden execed":                "DARDENEXED",
    "darden school of business":    "DARDENEXED",
    "attain":                       "AMS",
    "attain partners":              "AMS",
    "internal":                     "AMS",
}


def classify_with_claude(emails: list, notes: list, settings: dict) -> dict:
    api_key = settings.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY missing")
        sys.exit(1)

    your_name    = settings.get("YOUR_NAME", "")
    your_clients = [c.strip() for c in settings.get("YOUR_CLIENTS", []) if c.strip()]
    jira_enabled = bool(settings.get("JIRA_BASE_URL"))

    system_prompt = _build_system_prompt(your_name, your_clients, jira_enabled)
    user_content  = _build_user_content(emails, notes)

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 5000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_content}]
    }

    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ Anthropic API error {e.code}: {e.read().decode()}")
        sys.exit(1)

    raw_text = result["content"][0]["text"]
    return _parse_briefing_response(raw_text, emails, notes)


def _build_system_prompt(name: str, clients: list, jira_enabled: bool) -> str:
    client_list = ", ".join(clients) if clients else "various clients"
    name_line   = f"You are assisting {name}." if name else "You are a professional executive assistant."

    project_map_str = json.dumps(CLIENT_PROJECT_MAP, indent=2)

    jira_instructions = ""
    if jira_enabled:
        jira_instructions = f"""

## Jira Ticket Recommendations

For every email, evaluate whether it warrants a Jira ticket using these rules:

**AUTO-CREATE** (action="auto_create") — clear, unambiguous evidence of:
- A system error, exception, crash, or failure
- A broken feature or integration
- An explicit bug report
- Words/phrases: "error", "broken", "failing", "exception", "500", "crash", "not loading",
  "stopped working", "production issue", "incident"

**PROPOSE** (action="propose") — ambiguous signals that may need a ticket:
- "not working as expected", "issue with", "problem", "behaving oddly", "unexpected behavior"
- Unclear whether it's a bug or a configuration/user issue

**NONE** (action="none") — general requests, FYI, questions, feature ideas, action items
  that don't indicate an existing defect or error

For each auto_create or propose ticket, populate these fields:
- summary: Concise action-verb ticket title, max 10 words, no brackets
- description: 2-3 sentences — what is broken, who reported it, what impact
- issue_type: "Bug" for errors/failures, "Task" for unclear issues
- priority: "Highest" (production/blocking), "High" (client-facing), "Medium" (internal/non-blocking), "Low"
- project_key: Map the client to a Jira project key using this mapping:
{project_map_str}
  If no client match, use "AMS" as the default.
- source_email_subject: The original email subject
- source_email_from: The sender's name and email

Each email should have AT MOST ONE jira recommendation. Only include jira if action is
auto_create or propose — omit the field entirely if action is none.
"""

    return f"""{name_line} You are an expert executive assistant and Salesforce solution architect.
Your job is to review emails and notes and produce a crisp, actionable morning briefing.

The person is a Salesforce Solution Architect/Engineer at Attain Partners working with clients: {client_list}.
{jira_instructions}

You MUST respond with a valid JSON object ONLY. No markdown fences, no preamble. Just the JSON.

JSON structure:
{{
  "date": "Day, Month DD YYYY",
  "summary": "2-3 sentence overview of the day's priorities",
  "categories": {{
    "urgent_action": [
      {{
        "title": "Short action title (verb phrase)",
        "from": "Sender name or source",
        "detail": "What needs to be done, by when if known",
        "source": "outlook|evernote",
        "client": "Client name or 'Internal' or 'N/A'",
        "jira": {{
          "action": "auto_create|propose|none",
          "summary": "Ticket title",
          "description": "Ticket description",
          "issue_type": "Bug|Task",
          "priority": "Highest|High|Medium|Low",
          "project_key": "MSBDC|DARDENEXED|USS|SEED|AMS",
          "source_email_subject": "Original subject",
          "source_email_from": "Sender name <email>"
        }}
      }}
    ],
    "client": [...],
    "internal": [...],
    "vendor_tools": [...],
    "fyi": [...]
  }},
  "todos": [
    {{
      "task": "Task description",
      "source": "evernote|email",
      "priority": "high|medium|low",
      "client": "Client name or 'Internal'"
    }}
  ],
  "schedule": [
    {{
      "time": "9:00 AM",
      "event": "Event description",
      "note": "Optional context"
    }}
  ],
  "flags": {{
    "overdue": [],
    "waiting_on": [],
    "follow_ups": []
  }}
}}

Omit the "jira" field on items where action would be "none".

Classification rules:
- urgent_action: Requires response/action TODAY. Deadlines, approvals, escalations, direct requests.
- client: Client emails — informational or not yet urgent.
- internal: Attain Partners internal communications.
- vendor_tools: Salesforce releases, Mogli, vendor/tool notifications.
- fyi: Newsletters, automated notifications, CC'd items — no action needed.

For todos: extract checklist items, task mentions, to-do items from Evernote AND emails.
For schedule: extract time-specific events from Evernote notes.
Keep titles under 8 words. Keep details under 2 sentences."""


def _build_user_content(emails: list, notes: list) -> str:
    today = datetime.now().strftime("%A, %B %d %Y")
    lines = [f"Today is {today}. Please classify the following:\n"]

    lines.append(f"## EMAILS ({len(emails)} total)\n")
    for i, email in enumerate(emails, 1):
        lines.append(f"--- Email {i} ---")
        lines.append(f"From: {email.get('from_name','')} <{email.get('from_email','')}>")
        lines.append(f"Subject: {email.get('subject','')}")
        lines.append(f"Received: {email.get('received','')}")
        lines.append(f"Importance: {email.get('importance','normal')}")
        lines.append(f"Flagged: {email.get('flagged',False)}")
        lines.append(f"Preview: {email.get('preview','')}")
        lines.append("")

    lines.append(f"\n## EVERNOTE NOTES ({len(notes)} total)\n")
    for i, note in enumerate(notes, 1):
        lines.append(f"--- Note {i}: {note.get('title','Untitled')} ---")
        lines.append(f"Updated: {note.get('updated','')}")
        lines.append(f"Content:\n{note.get('content','')[:1500]}")
        lines.append("")

    return "\n".join(lines)


def _parse_briefing_response(raw: str, emails: list, notes: list) -> dict:
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        briefing = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"⚠️  Could not parse Claude response as JSON: {e}")
        briefing = {
            "date": datetime.now().strftime("%A, %B %d %Y"),
            "summary": "Classification failed.",
            "categories": {k: [] for k in CATEGORIES},
            "todos": [], "schedule": [],
            "flags": {"overdue": [], "waiting_on": [], "follow_ups": []},
        }

    briefing["meta"] = {
        "email_count": len(emails),
        "note_count": len(notes),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return briefing
