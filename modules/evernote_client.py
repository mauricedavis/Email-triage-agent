"""
modules/evernote_client.py
==========================
Evernote API client using the official Python SDK.
Uses a personal Developer Token (no OAuth flow needed for personal accounts).

To get your token:
  1. Log in to Evernote
  2. Go to https://www.evernote.com/api/DeveloperToken.action
  3. Generate token and paste into .env as EVERNOTE_TOKEN

For Business/Teams accounts, contact Evernote for API access.
"""

import sys
import re
from datetime import datetime, timedelta


class EvernoteClient:
    def __init__(self, settings: dict):
        self.token = settings.get("EVERNOTE_TOKEN", "")
        self.notebook_name = settings.get("EVERNOTE_NOTEBOOK", "")
        self.sandbox = settings.get("EVERNOTE_SANDBOX", False)

        if not self.token:
            print("⚠️  EVERNOTE_TOKEN not set — skipping Evernote fetch")
            self._enabled = False
            return

        self._enabled = True
        self._client = self._init_client()

    def _init_client(self):
        try:
            from evernote.api.client import EvernoteClient as _EvernoteSDK
        except ImportError:
            print("❌ evernote3 not installed. Run: pip install evernote3")
            sys.exit(1)

        client = _EvernoteSDK(token=self.token, sandbox=self.sandbox)
        return client

    # ── Note Fetching ─────────────────────────────────────────────

    def fetch_todays_notes(self) -> list[dict]:
        """Fetch notes modified today (or containing today's date in title)."""
        if not self._enabled:
            return []

        try:
            from evernote.api.client import EvernoteClient as _EvernoteSDK
            from evernote.edam.notestore import NoteStore
            from evernote.edam.type import ttypes as Types
        except ImportError:
            return []

        try:
            note_store = self._client.get_note_store()

            # Build filter: notes updated in last 24 hours OR matching today's date in title
            today = datetime.now()
            yesterday_ms = int((today - timedelta(days=1)).timestamp() * 1000)

            note_filter = NoteStore.NoteFilter()
            note_filter.updated = yesterday_ms

            # Optionally filter by notebook
            if self.notebook_name:
                notebook_guid = self._find_notebook_guid(note_store, self.notebook_name)
                if notebook_guid:
                    note_filter.notebookGuid = notebook_guid

            spec = NoteStore.NotesMetadataResultSpec()
            spec.includeTitle = True
            spec.includeUpdated = True
            spec.includeCreated = True
            spec.includeNotebookGuid = True

            result = note_store.findNotesMetadata(
                authenticationToken=self.token,
                filter=note_filter,
                offset=0,
                maxNotes=20,
                resultSpec=spec,
            )

            notes = []
            for meta in result.notes:
                content = self._fetch_note_content(note_store, meta.guid)
                notes.append({
                    "guid": meta.guid,
                    "title": meta.title,
                    "updated": datetime.fromtimestamp(meta.updated / 1000).isoformat() if meta.updated else "",
                    "created": datetime.fromtimestamp(meta.created / 1000).isoformat() if meta.created else "",
                    "content": content,
                    "source": "evernote",
                })

            return notes

        except Exception as e:
            print(f"   ⚠️  Evernote fetch error: {e}")
            return []

    def _fetch_note_content(self, note_store, guid: str) -> str:
        """Fetch and clean note content (strips ENML/HTML tags)."""
        try:
            note = note_store.getNote(
                authenticationToken=self.token,
                guid=guid,
                withContent=True,
                withResourcesData=False,
                withResourcesRecognition=False,
                withResourcesAlternateData=False,
            )
            if note.content:
                return self._strip_enml(note.content)
            return ""
        except Exception:
            return ""

    def _find_notebook_guid(self, note_store, name: str) -> str | None:
        """Find notebook GUID by name."""
        try:
            notebooks = note_store.listNotebooks(self.token)
            for nb in notebooks:
                if nb.name.lower() == name.lower():
                    return nb.guid
        except Exception:
            pass
        return None

    @staticmethod
    def _strip_enml(enml: str) -> str:
        """Strip ENML/HTML tags and clean up whitespace."""
        # Remove XML declaration and DOCTYPE
        text = re.sub(r'<\?xml[^>]+\?>', '', enml)
        text = re.sub(r'<!DOCTYPE[^>]+>', '', text)
        # Convert common block elements to newlines
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</(p|div|li|h[1-6])>', '\n', text, flags=re.IGNORECASE)
        # Remove all remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode basic HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        lines = [l for l in lines if l]
        return '\n'.join(lines)
