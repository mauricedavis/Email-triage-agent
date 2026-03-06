# Email Triage Agent

> **AI-powered morning briefing:** Pulls from Microsoft Outlook + Evernote, classifies everything with Claude AI, auto-creates Jira tickets for bugs and errors, and delivers a structured daily briefing via HTML file and Slack.

---

## Overview

The Email Triage Agent is a Python automation tool built for Salesforce Solution Architects and managed services professionals who need to start each day with a clear, prioritized view of their inbox and tasks — without manually sorting through dozens of emails.

Every morning it:

1. **Fetches** your Outlook inbox (Microsoft Graph API)
2. **Reads** your daily schedule and to-do notes from Evernote
3. **Classifies** everything with Claude AI — categorized by urgency, client, and type
4. **Creates Jira tickets** automatically for explicit bugs/errors; proposes tickets for ambiguous issues
5. **Delivers** a polished HTML briefing and optional Slack message

---

## Architecture

```
email-triage-agent/
├── agent.py                    # Main orchestrator — run this daily
├── approve_tickets.py          # Interactive Jira ticket approval tool
├── scheduler.py                # Background daily scheduler
├── requirements.txt            # Python dependencies
├── .env.example                # Credential template
│
├── config/
│   └── settings.py             # .env loader + validation
│
└── modules/
    ├── outlook.py              # Microsoft Graph API (MSAL device-code auth)
    ├── evernote_client.py      # Evernote API (developer token)
    ├── classifier.py           # Claude AI — classification + Jira recommendations
    ├── jira_client.py          # Atlassian REST API — auto-create + propose tickets
    ├── formatter.py            # HTML + console output
    ├── slack_poster.py         # Slack Block Kit delivery
    └── mock_data.py            # Sample data for --dry-run testing
```

---

## Features

### Email Classification
Emails are categorized into five groups using Claude AI:

| Category | Description |
|---|---|
| 🔴 Urgent / Action Required | Needs response or action TODAY |
| 🟠 Client | Client emails — informational or non-urgent |
| 🟡 Internal / Team | Attain Partners internal communications |
| 🔵 Vendor & Tools | Salesforce releases, Mogli, vendor notifications |
| ⚪ FYI / No Action | Newsletters, CC's, automated notifications |

### Jira Auto-Ticketing
Claude evaluates every email for bug/error signals:

| Signal | Action |
|---|---|
| `error`, `broken`, `failing`, `exception`, `500`, `crash` | **Auto-create** Bug ticket immediately |
| `issue with`, `not working as expected`, `behaving oddly` | **Propose** ticket → awaits your approval |
| Feature requests, questions, FYI | No ticket created |

All tickets are assigned to `mjdavis@attainpartners.com` by default.

### Client → Jira Project Mapping

| Client | Jira Project Key |
|---|---|
| SEED Foundation | `SEED` |
| Michigan SBDC / GVSU | `MSBDC` |
| UPenn Student Success | `USS` |
| AAUM Managed Services | `AMS` |
| MIDAS / Beatrice Hahn | `AMS` |
| Darden / Darden ExecEd | `DARDENEXED` |
| Attain Partners / Internal | `AMS` |

To add a new client, edit `CLIENT_PROJECT_MAP` in `modules/classifier.py`.

### Briefing Output
- **Console** — clean text summary with emoji category headers
- **HTML file** — polished dark-theme briefing saved to `output/briefing_YYYYMMDD_HHMM.html`
- **Slack** — rich Block Kit message with ticket links (optional, requires `--slack` flag)

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure credentials
```bash
cp .env.example .env
# Edit .env with your credentials — see setup guide below
```

### 3. Test with mock data (no credentials needed)
```bash
python agent.py --dry-run
```

### 4. Run for real
```bash
python agent.py
```

---

## Usage

```bash
# Standard run — today's emails + Evernote notes updated today
python agent.py

# Look back 2 days (useful on Monday mornings)
python agent.py --days 2

# Post briefing to Slack
python agent.py --slack

# Monday mode — 3 days back + Slack
python agent.py --days 3 --slack

# Skip Jira ticket creation
python agent.py --no-jira

# Test with mock data
python agent.py --dry-run

# Review and approve proposed Jira tickets
python approve_tickets.py

# Approve all pending tickets
python approve_tickets.py --all
```

---

## Credential Setup

### Required: Anthropic API Key
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key → paste as `ANTHROPIC_API_KEY` in `.env`

### Microsoft Outlook (Azure App Registration)
**One-time setup (~5 minutes):**
1. Go to [portal.azure.com](https://portal.azure.com) → **Azure Active Directory** → **App registrations** → **New registration**
2. Name: `Email Triage Agent` | Account types: **Accounts in any org + personal accounts**
3. Click **Register** → copy the **Application (client) ID** → paste as `MS_CLIENT_ID`
4. **Authentication** → Add platform → **Mobile and desktop** → check `http://localhost` → Save
5. **API permissions** → Add → Microsoft Graph → Delegated → add `Mail.Read` and `User.Read`

First run opens a browser for Microsoft login. Token is cached silently after that (~90 day expiry).

### Evernote Developer Token
1. Go to [evernote.com/api/DeveloperToken.action](https://www.evernote.com/api/DeveloperToken.action)
2. Generate token → paste as `EVERNOTE_TOKEN` in `.env`
3. Set `EVERNOTE_NOTEBOOK` to the name of your daily notes notebook

### Jira (Atlassian API Token)
1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create API token → paste as `JIRA_API_TOKEN` in `.env`
3. `JIRA_ASSIGNEE_ACCOUNT_ID` is pre-configured for `mjdavis@attainpartners.com`

### Slack (Optional)
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. **OAuth & Permissions** → Bot Token Scopes → add `chat:write`
3. Install to workspace → copy **Bot User OAuth Token** → paste as `SLACK_BOT_TOKEN`
4. `/invite @Email Triage Agent` in your target channel → copy Channel ID → paste as `SLACK_CHANNEL_ID`

---

## Scheduling (Automated Daily Runs)

### macOS / Linux — Cron (Recommended)
```bash
crontab -e

# Add (runs Mon-Fri at 7:00 AM):
0 7 * * 1-5 cd /path/to/email-triage-agent && python3 agent.py --slack >> logs/briefing.log 2>&1

# Monday: look back 3 days to catch weekend email
0 7 * * 1 cd /path/to/email-triage-agent && python3 agent.py --slack --days 3 >> logs/briefing.log 2>&1
```

### Windows — Task Scheduler
1. **Create Basic Task** → trigger: Daily at 7:00 AM (Mon-Fri)
2. Action: `python.exe` | Arguments: `C:\Users\MauriceJDavis\email-triage-agent\agent.py --slack`
3. Start in: `C:\Users\MauriceJDavis\email-triage-agent`

### Built-in Scheduler (keep terminal open)
```bash
python scheduler.py --time 07:00 --slack
```

---

## Configuration Reference (`.env`)

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Outlook
MS_CLIENT_ID=your-azure-app-client-id
MS_TENANT_ID=common                        # or your org tenant ID for work accounts

# Evernote
EVERNOTE_TOKEN=your-evernote-token
EVERNOTE_NOTEBOOK=Daily Notes

# Jira
JIRA_BASE_URL=https://attainpartners.atlassian.net
JIRA_EMAIL=mjdavis@attainpartners.com
JIRA_API_TOKEN=your-atlassian-api-token
JIRA_ASSIGNEE_ACCOUNT_ID=618d7b2af1ff560069e000d6

# Slack (optional)
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C0XXXXXXXXX

# Behavior
YOUR_NAME=Maury
YOUR_CLIENTS=SEED Foundation,Michigan SBDC,UPenn Student Success,AAUM,MIDAS,Darden,Attain Partners
EMAIL_MAX_FETCH=50
EMAIL_FOLDERS=inbox
```

---

## Approving Proposed Jira Tickets

When Claude flags an email as ambiguous (possible but not definitive bug), it saves a proposed ticket to `pending_tickets.json`. Review and act on these with:

```bash
python approve_tickets.py          # Interactive Y/N for each
python approve_tickets.py --all    # Approve everything
python approve_tickets.py --list   # View pending without acting
python approve_tickets.py --clear  # Reject and clear all
```

---

## Maintenance

| Item | Frequency | Action |
|---|---|---|
| Outlook token re-auth | Every ~90 days | One browser click on next run |
| Evernote token renewal | Annually | Regenerate at evernote.com |
| Add new client | As needed | Edit `CLIENT_PROJECT_MAP` in `modules/classifier.py` |
| Agent runs itself | Every weekday | No action needed |

---

## Dependencies

```
msal>=1.28.0        # Microsoft authentication
evernote3>=1.25.4   # Evernote SDK (Python 3 compatible)
```

All HTTP calls use Python stdlib (`urllib`) — no `requests` or `httpx` required.

---

## Project Context

Built for **Maury Davis**, Salesforce Solution Architect at **Attain Partners**, managing multiple client engagements including Michigan SBDC, Darden School of Business, UPenn Student Success, SEED Foundation, AAUM, and MIDAS.

---

## License

Private — Attain Managed Services. Not for redistribution.
