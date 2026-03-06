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

    # ── Note Creation ─────────────────────────────────────────────

    def create_morning_note(self, briefing: dict, output_notebook: str = "Daily Journal") -> str | None:
        """
        Create a morning briefing note in Evernote.
        Returns the note GUID if successful, None otherwise.
        """
        if not self._enabled:
            return None

        try:
            from evernote.edam.type import ttypes as Types
        except ImportError:
            return None

        try:
            note_store = self._client.get_note_store()

            # Find the target notebook
            notebook_guid = self._find_notebook_guid(note_store, output_notebook)
            if not notebook_guid:
                print(f"   ⚠️  Notebook '{output_notebook}' not found — note created in default notebook")

            title = f"Morning Briefing -- {briefing.get('date', datetime.now().strftime('%A, %B %d %Y'))}"
            content = self._build_enml(briefing)

            note = Types.Note()
            note.title = title
            note.content = content
            if notebook_guid:
                note.notebookGuid = notebook_guid

            created_note = note_store.createNote(authenticationToken=self.token, note=note)
            print(f"   OK Evernote note created: '{title}'")
            return created_note.guid

        except Exception as e:
            print(f"   WARNING Evernote note creation failed: {e}")
            return None

    def _build_enml(self, briefing: dict) -> str:
        """Build ENML (Evernote Markup Language) content from briefing data."""
        from modules.classifier import CATEGORIES

        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">')
        lines.append('<en-note>')

        # Summary
        summary = briefing.get("summary", "")
        if summary:
            lines.append(f'<p><i>{self._esc(summary)}</i></p>')
            lines.append('<hr/>')

        # Categories
        cats = briefing.get("categories", {})
        for key, label in CATEGORIES.items():
            items = cats.get(key, [])
            if not items:
                continue
            lines.append(f'<h2>{self._esc(label)} ({len(items)})</h2>')
            for item in items:
                lines.append(f'<p><b>{self._esc(item.get("title", ""))}</b></p>')
                client = item.get("client", "")
                if client and client not in ("N/A", ""):
                    lines.append(f'<p style="margin-left:20px;color:#666;">Client: {self._esc(client)}</p>')
                from_str = item.get("from", "")
                if from_str:
                    lines.append(f'<p style="margin-left:20px;color:#666;">From: {self._esc(from_str)}</p>')
                detail = item.get("detail", "")
                if detail:
                    lines.append(f'<p style="margin-left:20px;">{self._esc(detail)}</p>')
                jr = item.get("jira_result")
                if jr and jr.get("status") == "created":
                    url = jr.get("url", "")
                    key_str = jr.get("key", "")
                    prio = jr.get("priority", "")
                    lines.append(f'<p style="margin-left:20px;">Jira: <a href="{url}">{key_str}</a> ({prio})</p>')
                elif jr and jr.get("status") == "proposed":
                    lines.append(f'<p style="margin-left:20px;">Jira ticket proposed -- run approve_tickets.py</p>')

        # Jira Summary
        jira_results = briefing.get("jira_results", [])
        created_tickets  = [r for r in jira_results if r.get("status") == "created"]
        proposed_tickets = [r for r in jira_results if r.get("status") == "proposed"]
        if created_tickets or proposed_tickets:
            lines.append('<hr/>')
            lines.append(f'<h2>Jira Tickets ({len(created_tickets) + len(proposed_tickets)})</h2>')
            for r in created_tickets:
                url = r.get("url", "")
                key_str = r.get("key", "")
                prio = r.get("priority", "")
                summary_str = r.get("summary", "")
                lines.append(f'<p>Created: <a href="{url}">{key_str}</a> ({prio}) -- {self._esc(summary_str)}</p>')
            for r in proposed_tickets:
                jira = r.get("jira", {})
                lines.append(f'<p>Proposed [{self._esc(jira.get("project_key",""))}] {self._esc(jira.get("summary",""))}</p>')

        # To-Dos with Evernote checkboxes
        todos = briefing.get("todos", [])
        if todos:
            lines.append('<hr/>')
            lines.append(f'<h2>To-Dos ({len(todos)})</h2>')
            lines.append('<ul>')
            for t in todos:
                lines.append(f'<li><en-todo checked="false"/> [{self._esc(t.get("client",""))}] {self._esc(t.get("task",""))}</li>')
            lines.append('</ul>')

        # Schedule
        schedule = briefing.get("schedule", [])
        if schedule:
            lines.append('<hr/>')
            lines.append('<h2>Schedule</h2>')
            for s in schedule:
                note_str = f' -- {self._esc(s["note"])}' if s.get("note") else ""
                lines.append(f'<p><b>{self._esc(s.get("time",""))}</b> -- {self._esc(s.get("event",""))}{note_str}</p>')

        # Flags
        flags = briefing.get("flags", {})
        overdue   = flags.get("overdue", [])
        waiting   = flags.get("waiting_on", [])
        followups = flags.get("follow_ups", [])
        if overdue or waiting or followups:
            lines.append('<hr/>')
            lines.append('<h2>Flags</h2>')
            for f in overdue:
                lines.append(f'<p>OVERDUE: {self._esc(f)}</p>')
            for f in waiting:
                lines.append(f'<p>WAITING ON: {self._esc(f)}</p>')
            for f in followups:
                lines.append(f'<p>FOLLOW UP: {self._esc(f)}</p>')

        # Footer
        meta = briefing.get("meta", {})
        lines.append('<hr/>')
        lines.append(f'<p style="color:#999;font-size:small;">Generated {self._esc(meta.get("generated_at",""))} '
                     f'| {meta.get("email_count",0)} emails, {meta.get("note_count",0)} Evernote notes '
                     f'| Email Triage Agent</p>')

        lines.append('</en-note>')
        return '\n'.join(lines)

    @staticmethod
    def _esc(text: str) -> str:
        """Escape special XML characters for ENML."""
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
