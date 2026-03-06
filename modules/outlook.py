"""
modules/outlook.py
==================
Microsoft Graph API client using MSAL device-code flow.
No Azure app client secret needed for delegated auth — just a
Client ID from an Azure App Registration (free, 5 min setup).

First run: opens browser for Microsoft login → saves token cache.
Subsequent runs: uses cached token silently (no re-login needed).
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


class OutlookClient:
    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    SCOPES = ["Mail.Read", "User.Read"]

    def __init__(self, settings: dict):
        self.settings = settings
        self.token_cache_path = Path(settings["MS_TOKEN_CACHE"])
        self._app = None
        self._access_token = None
        self._authenticate()

    # ── Authentication ────────────────────────────────────────────

    def _authenticate(self):
        try:
            import msal
        except ImportError:
            print("❌ msal not installed. Run: pip install msal")
            sys.exit(1)

        cache = msal.SerializableTokenCache()
        if self.token_cache_path.exists():
            cache.deserialize(self.token_cache_path.read_text())

        self._app = msal.PublicClientApplication(
            client_id=self.settings["MS_CLIENT_ID"],
            authority=f"https://login.microsoftonline.com/{self.settings['MS_TENANT_ID']}",
            token_cache=cache,
        )

        # Try silent auth first (cached token)
        accounts = self._app.get_accounts()
        result = None
        if accounts:
            result = self._app.acquire_token_silent(self.SCOPES, account=accounts[0])

        # Fall back to device-code flow (first run or expired)
        if not result:
            flow = self._app.initiate_device_flow(scopes=self.SCOPES)
            if "user_code" not in flow:
                raise ValueError(f"Device flow failed: {flow.get('error_description')}")
            print(f"\n🔐 Outlook Auth Required:")
            print(f"   {flow['message']}\n")
            result = self._app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            raise ValueError(f"Auth failed: {result.get('error_description', 'Unknown error')}")

        self._access_token = result["access_token"]

        # Persist cache
        if cache.has_state_changed:
            self.token_cache_path.write_text(cache.serialize())

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _get(self, url: str, params: dict = None) -> dict:
        import urllib.request
        import urllib.parse

        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())

    # ── Email Fetching ────────────────────────────────────────────

    def fetch_recent_emails(self, days: int = 1) -> list[dict]:
        """Fetch emails from inbox (and optionally other folders) within the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

        emails = []
        folders = self.settings.get("EMAIL_FOLDERS", ["inbox"])
        max_fetch = self.settings.get("EMAIL_MAX_FETCH", 50)

        for folder in folders:
            folder = folder.strip()
            url = f"{self.GRAPH_BASE}/me/mailFolders/{folder}/messages"
            params = {
                "$select": "subject,from,toRecipients,ccRecipients,receivedDateTime,bodyPreview,isRead,importance,hasAttachments,flag",
                "$filter": f"receivedDateTime ge {cutoff_str}",
                "$orderby": "receivedDateTime desc",
                "$top": str(max_fetch),
            }

            try:
                data = self._get(url, params)
                for msg in data.get("value", []):
                    emails.append(self._normalize_email(msg, folder))
            except Exception as e:
                print(f"   ⚠️  Could not fetch folder '{folder}': {e}")

        return emails

    def _normalize_email(self, msg: dict, folder: str) -> dict:
        """Normalize Graph API message to a clean dict."""
        sender = msg.get("from", {}).get("emailAddress", {})
        to_list = [r["emailAddress"]["address"] for r in msg.get("toRecipients", [])]
        cc_list = [r["emailAddress"]["address"] for r in msg.get("ccRecipients", [])]

        return {
            "id": msg.get("id", ""),
            "subject": msg.get("subject", "(No Subject)"),
            "from_name": sender.get("name", ""),
            "from_email": sender.get("address", ""),
            "to": to_list,
            "cc": cc_list,
            "received": msg.get("receivedDateTime", ""),
            "preview": msg.get("bodyPreview", "")[:500],  # First 500 chars
            "is_read": msg.get("isRead", False),
            "importance": msg.get("importance", "normal"),  # low / normal / high
            "has_attachments": msg.get("hasAttachments", False),
            "flagged": msg.get("flag", {}).get("flagStatus") == "flagged",
            "folder": folder,
            "source": "outlook",
        }
