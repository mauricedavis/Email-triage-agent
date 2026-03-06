#!/usr/bin/env python3
"""
Morning Briefing Agent
======================
Pulls from Outlook (Microsoft Graph API) + Evernote API,
classifies everything with Claude, auto-creates or proposes
Jira tickets for bugs/errors, and outputs a structured daily
briefing to console, HTML file, Evernote (Daily Journal), and Slack.

Usage:
    python agent.py                  # Run briefing now
    python agent.py --slack          # Also post to Slack
    python agent.py --days 2         # Look back 2 days of email
    python agent.py --dry-run        # Test without live API calls
    python agent.py --no-jira        # Skip Jira ticket creation
"""

import argparse
from datetime import datetime
from modules.outlook import OutlookClient
from modules.evernote_client import EvernoteClient
from modules.classifier import classify_with_claude
from modules.jira_client import JiraClient
from modules.formatter import format_briefing_html, format_briefing_text
from modules.slack_poster import post_to_slack
from config.settings import load_settings


def main():
    parser = argparse.ArgumentParser(description="Morning Briefing Agent")
    parser.add_argument("--slack",      action="store_true", help="Post briefing to Slack")
    parser.add_argument("--days",       type=int, default=1, help="Days of email to look back (default: 1)")
    parser.add_argument("--dry-run",    action="store_true", help="Use mock data, skip live API calls")
    parser.add_argument("--no-jira",    action="store_true", help="Skip Jira ticket creation entirely")
    parser.add_argument("--no-evernote-out", action="store_true", help="Skip writing briefing note to Evernote")
    parser.add_argument("--output-dir", default="output", help="Directory for HTML output")
    args = parser.parse_args()

    settings = load_settings()
    print(f"\n{'='*60}")
    print(f"  Morning Briefing Agent — {datetime.now().strftime('%A, %B %d %Y')}")
    print(f"{'='*60}\n")

    # ── 1. FETCH EMAILS ──────────────────────────────────────────
    print("📬 Fetching Outlook emails...")
    if args.dry_run:
        from modules.mock_data import MOCK_EMAILS
        emails = MOCK_EMAILS
    else:
        outlook = OutlookClient(settings)
        emails = outlook.fetch_recent_emails(days=args.days)
    print(f"   → {len(emails)} emails retrieved\n")

    # ── 2. FETCH EVERNOTE ────────────────────────────────────────
    print("📓 Fetching Evernote notes...")
    if args.dry_run:
        from modules.mock_data import MOCK_NOTES
        notes = MOCK_NOTES
    else:
        evernote = EvernoteClient(settings)
        notes = evernote.fetch_todays_notes()
    print(f"   → {len(notes)} notes retrieved\n")

    # ── 3. CLASSIFY WITH CLAUDE ───────────────────────────────────
    print("🤖 Classifying with Claude...")
    briefing = classify_with_claude(emails=emails, notes=notes, settings=settings)
    print("   → Classification complete\n")

    # ── 4. JIRA TICKET PROCESSING ─────────────────────────────────
    if not args.no_jira and settings.get("JIRA_BASE_URL"):
        print("🎫 Processing Jira tickets...")
        if args.dry_run:
            from modules.mock_data import MOCK_JIRA_RESULT
            briefing["jira_results"] = MOCK_JIRA_RESULT
        else:
            jira = JiraClient(settings)
            jira_results = jira.process_tickets(briefing)
            briefing["jira_results"] = jira_results
            auto_count = len([r for r in jira_results if r.get("status") == "created"])
            prop_count = len([r for r in jira_results if r.get("status") == "proposed"])
            print(f"   → {auto_count} ticket(s) auto-created, {prop_count} proposed for approval\n")
    else:
        briefing["jira_results"] = []

    # ── 5. CONSOLE + HTML OUTPUT ──────────────────────────────────
    text_output = format_briefing_text(briefing)
    print(text_output)

    import os
    os.makedirs(args.output_dir, exist_ok=True)
    html_output = format_briefing_html(briefing)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    html_path = f"{args.output_dir}/briefing_{timestamp}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"\n✅ HTML briefing saved: {html_path}")

    # ── 6. EVERNOTE NOTE OUTPUT ───────────────────────────────────
    journal_notebook = settings.get("EVERNOTE_JOURNAL_NOTEBOOK", "Daily Journal")
    if not args.no_evernote_out and not args.dry_run and settings.get("EVERNOTE_TOKEN"):
        print(f"\n📓 Creating Evernote note in '{journal_notebook}'...")
        evernote_out = EvernoteClient(settings)
        guid = evernote_out.create_morning_note(briefing, output_notebook=journal_notebook)
        if guid:
            print(f"   → Note created successfully")
        else:
            print(f"   → Note creation failed (check notebook name in .env)")
    elif args.dry_run:
        print(f"\n📓 Evernote note: skipped in --dry-run mode")

    # ── 7. SLACK OUTPUT ───────────────────────────────────────────
    if args.slack:
        if not settings.get("SLACK_BOT_TOKEN") or not settings.get("SLACK_CHANNEL_ID"):
            print("⚠️  Slack not configured — skipping")
        else:
            print("\n📤 Posting to Slack...")
            post_to_slack(briefing, settings)
            print("   → Posted successfully")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
