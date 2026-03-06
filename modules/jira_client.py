"""
modules/jira_client.py
======================
Jira REST API client for auto-creating and proposing tickets
from email classification results.

Uses HTTP Basic Auth with an Atlassian API token.
Assignee is always set to the configured JIRA_ASSIGNEE_ACCOUNT_ID.

Auto-create:  Tickets created immediately. Briefing shows link + key.
Propose:      Tickets written to pending_tickets.json for approval.
              Run: python approve_tickets.py to create approved ones.
"""

import json
import urllib.request
import urllib.error
import base64
from datetime import datetime
from pathlib import Path


PENDING_FILE = Path("pending_tickets.json")


class JiraClient:
    def __init__(self, settings: dict):
        self.base_url   = settings.get("JIRA_BASE_URL", "").rstrip("/")
        self.email      = settings.get("JIRA_EMAIL", "")
        self.api_token  = settings.get("JIRA_API_TOKEN", "")
        self.assignee   = settings.get("JIRA_ASSIGNEE_ACCOUNT_ID", "")

        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN are all required.")

        # Build Basic Auth header
        credentials = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
        self._auth_header = f"Basic {credentials}"

    # ── Public interface ──────────────────────────────────────────

    def process_tickets(self, briefing: dict) -> list[dict]:
        """
        Walk all category items in the briefing, process any with
        jira.action == 'auto_create' or 'propose'.
        Returns a list of result dicts for inclusion in the briefing.
        """
        results = []
        pending = self._load_pending()

        cats = briefing.get("categories", {})
        for cat_key, items in cats.items():
            for item in items:
                jira_rec = item.get("jira")
                if not jira_rec or jira_rec.get("action") == "none":
                    continue

                action = jira_rec.get("action")
                if action == "auto_create":
                    result = self._create_ticket(jira_rec, item)
                    results.append(result)
                    # Attach result back to briefing item for display
                    item["jira_result"] = result

                elif action == "propose":
                    ticket_id = f"proposed_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(pending)}"
                    proposed = {
                        "id": ticket_id,
                        "proposed_at": datetime.now().isoformat(),
                        "category": cat_key,
                        "item_title": item.get("title", ""),
                        "jira": jira_rec,
                    }
                    pending.append(proposed)
                    result = {"status": "proposed", "ticket_id": ticket_id, "jira": jira_rec}
                    results.append(result)
                    item["jira_result"] = result

        self._save_pending(pending)
        return results

    # ── Ticket creation ───────────────────────────────────────────

    def _create_ticket(self, jira_rec: dict, item: dict) -> dict:
        """Create a Jira issue and return result dict."""
        project_key = jira_rec.get("project_key", "AMS")
        issue_type  = jira_rec.get("issue_type", "Bug")
        priority    = jira_rec.get("priority", "Medium")
        summary     = jira_rec.get("summary", item.get("title", "Issue from email"))

        description = self._build_description(jira_rec, item)

        payload = {
            "fields": {
                "project":   {"key": project_key},
                "summary":   summary,
                "issuetype": {"name": issue_type},
                "priority":  {"name": priority},
                "description": {
                    "type":    "doc",
                    "version": 1,
                    "content": [
                        {
                            "type":    "paragraph",
                            "content": [{"type": "text", "text": description}]
                        }
                    ]
                },
                "labels": ["auto-created", "morning-briefing-agent"],
            }
        }

        # Add assignee if configured
        if self.assignee:
            payload["fields"]["assignee"] = {"accountId": self.assignee}

        try:
            response = self._post("/rest/api/3/issue", payload)
            ticket_key = response.get("key", "")
            ticket_url = f"{self.base_url}/browse/{ticket_key}"
            print(f"   ✅ Created [{project_key}] {ticket_key}: {summary[:50]}")
            return {
                "status":      "created",
                "key":         ticket_key,
                "url":         ticket_url,
                "project_key": project_key,
                "summary":     summary,
                "priority":    priority,
                "issue_type":  issue_type,
                "jira":        jira_rec,
            }
        except Exception as e:
            print(f"   ⚠️  Failed to create ticket for '{summary[:40]}': {e}")
            return {
                "status":  "failed",
                "error":   str(e),
                "summary": summary,
                "jira":    jira_rec,
            }

    def _build_description(self, jira_rec: dict, item: dict) -> str:
        lines = []
        detail = item.get("detail", "")
        if detail:
            lines.append(detail)
            lines.append("")

        from_str = jira_rec.get("source_email_from", "")
        subj     = jira_rec.get("source_email_subject", "")
        if from_str:
            lines.append(f"Reported by: {from_str}")
        if subj:
            lines.append(f"Source email: {subj}")

        lines.append("")
        lines.append(f"Auto-created by Morning Briefing Agent on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)

    # ── Pending ticket store ──────────────────────────────────────

    def _load_pending(self) -> list:
        if PENDING_FILE.exists():
            try:
                return json.loads(PENDING_FILE.read_text())
            except Exception:
                return []
        return []

    def _save_pending(self, pending: list):
        PENDING_FILE.write_text(json.dumps(pending, indent=2))

    # ── HTTP helpers ──────────────────────────────────────────────

    def _post(self, path: str, payload: dict) -> dict:
        url  = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            url, data=body,
            headers={
                "Authorization": self._auth_header,
                "Content-Type":  "application/json",
                "Accept":        "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
