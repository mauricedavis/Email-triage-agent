#!/usr/bin/env python3
"""
approve_tickets.py
==================
Interactive approval tool for proposed Jira tickets.
Run this after reviewing your morning briefing to approve
or reject tickets that Claude flagged as ambiguous.

Usage:
    python approve_tickets.py           # Interactive mode
    python approve_tickets.py --all     # Approve all pending
    python approve_tickets.py --list    # Just list pending, no action
    python approve_tickets.py --clear   # Clear all pending (reject all)
"""

import argparse
import json
from pathlib import Path
from modules.jira_client import JiraClient, PENDING_FILE
from config.settings import load_settings


def main():
    parser = argparse.ArgumentParser(description="Approve proposed Jira tickets")
    parser.add_argument("--all",   action="store_true", help="Approve all pending tickets")
    parser.add_argument("--list",  action="store_true", help="List pending tickets without acting")
    parser.add_argument("--clear", action="store_true", help="Reject and clear all pending tickets")
    args = parser.parse_args()

    if not PENDING_FILE.exists() or PENDING_FILE.read_text().strip() == "[]":
        print("\n✅ No pending tickets to review.\n")
        return

    pending = json.loads(PENDING_FILE.read_text())
    print(f"\n{'='*60}")
    print(f"  Proposed Jira Tickets ({len(pending)} pending)")
    print(f"{'='*60}\n")

    for i, ticket in enumerate(pending, 1):
        jira = ticket.get("jira", {})
        print(f"  [{i}] {jira.get('project_key','?')} / {jira.get('issue_type','Bug')} / {jira.get('priority','Medium')}")
        print(f"      Summary:  {jira.get('summary','')}")
        print(f"      From:     {jira.get('source_email_from','')}")
        print(f"      Subject:  {jira.get('source_email_subject','')}")
        print(f"      Proposed: {ticket.get('proposed_at','')[:16]}")
        print()

    if args.list:
        return

    if args.clear:
        PENDING_FILE.write_text("[]")
        print(f"🗑️  Cleared {len(pending)} pending ticket(s).\n")
        return

    settings = load_settings()
    jira_client = JiraClient(settings)
    approved = []
    rejected = []

    if args.all:
        approved = pending
        print(f"🚀 Approving all {len(pending)} ticket(s)...\n")
    else:
        # Interactive mode
        print("For each ticket, enter Y (approve), N (reject), or Q (quit):\n")
        for i, ticket in enumerate(pending, 1):
            jira = ticket.get("jira", {})
            summary = jira.get("summary", "")
            project = jira.get("project_key", "?")
            answer = input(f"  [{i}/{len(pending)}] [{project}] {summary[:55]} → ").strip().upper()
            if answer == "Y":
                approved.append(ticket)
            elif answer == "Q":
                print("\n  Stopped. Remaining tickets stay pending.\n")
                # Save unapproved ones back
                remaining = pending[i:]
                PENDING_FILE.write_text(json.dumps(rejected + remaining, indent=2))
                break
            else:
                rejected.append(ticket)

    # Create approved tickets
    created_count = 0
    failed_count  = 0
    for ticket in approved:
        result = jira_client._create_ticket(ticket["jira"], {"title": ticket.get("item_title",""), "detail": ""})
        if result.get("status") == "created":
            created_count += 1
        else:
            failed_count += 1

    # Clear approved from pending
    remaining_ids = {t["id"] for t in rejected}
    remaining = [t for t in pending if t.get("id") in remaining_ids]
    PENDING_FILE.write_text(json.dumps(remaining, indent=2))

    print(f"\n{'='*60}")
    print(f"  ✅ Created: {created_count}  ❌ Failed: {failed_count}  🗑️  Rejected: {len(rejected)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
