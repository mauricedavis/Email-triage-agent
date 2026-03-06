"""
modules/slack_poster.py
=======================
Posts the morning briefing to a Slack channel using
the Slack Web API (Block Kit for rich formatting).
"""

import json
import urllib.request
import urllib.error
from modules.classifier import CATEGORIES


def post_to_slack(briefing: dict, settings: dict):
    token = settings.get("SLACK_BOT_TOKEN", "")
    channel = settings.get("SLACK_CHANNEL_ID", "")

    if not token or not channel:
        return

    blocks = _build_blocks(briefing)

    payload = {
        "channel": channel,
        "text": f"Morning Briefing — {briefing.get('date', '')}",
        "blocks": blocks,
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            if not result.get("ok"):
                print(f"   ⚠️  Slack error: {result.get('error', 'unknown')}")
    except urllib.error.HTTPError as e:
        print(f"   ⚠️  Slack HTTP error: {e.code}")


def _build_blocks(briefing: dict) -> list:
    blocks = []
    date = briefing.get("date", "")
    summary = briefing.get("summary", "")
    cats = briefing.get("categories", {})
    todos = briefing.get("todos", [])
    flags = briefing.get("flags", {})

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"📋 Morning Briefing — {date}"}
    })

    # Summary
    if summary:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"_{summary}_"}
        })

    blocks.append({"type": "divider"})

    # Categories
    emoji_map = {
        "urgent_action": "🔴",
        "client": "🟠",
        "internal": "🟡",
        "vendor_tools": "🔵",
        "fyi": "⚪",
    }

    for key, label in CATEGORIES.items():
        items = cats.get(key, [])
        if not items:
            continue

        emoji = emoji_map.get(key, "•")
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{emoji} {label}* ({len(items)})"}
        })

        for item in items[:5]:  # Slack has block limits, cap at 5 per category
            client = item.get("client", "")
            client_str = f" `{client}`" if client and client != "N/A" else ""
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{item.get('title','')}*{client_str}\n{item.get('from','')} — {item.get('detail','')}"
                }
            })

        if len(items) > 5:
            blocks.append({
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"_+ {len(items) - 5} more — see HTML briefing_"}]
            })

        blocks.append({"type": "divider"})

    # Todos
    if todos:
        todo_text = "\n".join([
            f"{'❗' if t.get('priority')=='high' else '◦'} [{t.get('client','')}] {t.get('task','')}"
            for t in todos[:10]
        ])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*📝 To-Do's ({len(todos)})*\n```{todo_text}```"}
        })
        blocks.append({"type": "divider"})

    # Flags
    overdue = flags.get("overdue", [])
    waiting = flags.get("waiting_on", [])
    followups = flags.get("follow_ups", [])

    flag_lines = []
    for f in overdue:
        flag_lines.append(f"⏰ OVERDUE: {f}")
    for f in waiting:
        flag_lines.append(f"⏳ Waiting on: {f}")
    for f in followups:
        flag_lines.append(f"🔁 Follow up: {f}")

    if flag_lines:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*🚩 Flags*\n" + "\n".join(flag_lines)}
        })

    return blocks
