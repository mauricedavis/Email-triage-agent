"""
modules/mock_data.py — Sample data for --dry-run mode
"""

MOCK_EMAILS = [
    {
        "id": "mock_001",
        "subject": "Michigan SBDC - County Map LWC - D3 Tooltip Throwing JS Error",
        "from_name": "Sarah Chen",
        "from_email": "schen@michigansbdc.org",
        "to": ["maury@attainpartners.com"],
        "cc": [],
        "received": "2025-03-03T07:42:00Z",
        "preview": "Hi Maury, we reviewed the county impact map and it's throwing a 'Cannot read property of undefined' JS exception on the tooltip component. The error appears in console on every county hover. Board demo is tomorrow at 2pm — need this fixed ASAP.",
        "is_read": False,
        "importance": "high",
        "has_attachments": False,
        "flagged": True,
        "folder": "inbox",
        "source": "outlook",
    },
    {
        "id": "mock_002",
        "subject": "Darden - Transfer Registration LWC - Step 2 Financial Summary Not Loading",
        "from_name": "James Whitfield",
        "from_email": "jwhitfield@darden.virginia.edu",
        "to": ["maury@attainpartners.com"],
        "cc": [],
        "received": "2025-03-03T08:15:00Z",
        "preview": "Maury, the financial summary panel in Step 2 of the transfer registration component is completely blank. No error in console but the data just isn't rendering. Students are reporting this since this morning. Please take a look.",
        "is_read": False,
        "importance": "high",
        "has_attachments": False,
        "flagged": False,
        "folder": "inbox",
        "source": "outlook",
    },
    {
        "id": "mock_003",
        "subject": "UPenn Student Success - Salesforce Login Page Broken for SSO Users",
        "from_name": "Dr. Monica Reyes",
        "from_email": "mreyes@upenn.edu",
        "to": ["maury@attainpartners.com"],
        "cc": [],
        "received": "2025-03-03T06:30:00Z",
        "preview": "We're getting reports that SSO login is failing for about 40% of students since this morning. They're seeing a '500 internal server error' after the redirect. This is blocking access to all student resources.",
        "is_read": False,
        "importance": "high",
        "has_attachments": False,
        "flagged": True,
        "folder": "inbox",
        "source": "outlook",
    },
    {
        "id": "mock_004",
        "subject": "Attain Team Standup - Agenda for Today",
        "from_name": "Taylor Brooks",
        "from_email": "tbrooks@attainpartners.com",
        "to": ["team@attainpartners.com"],
        "cc": [],
        "received": "2025-03-03T07:00:00Z",
        "preview": "Team, standup is at 9:30 AM today. Please come prepared with status on active tickets. Reminder: biweekly huddle dashboard needs to be updated before Thursday.",
        "is_read": False,
        "importance": "normal",
        "has_attachments": False,
        "flagged": False,
        "folder": "inbox",
        "source": "outlook",
    },
    {
        "id": "mock_005",
        "subject": "MIDAS - Beatrice Hahn - Data Export Behaving Oddly",
        "from_name": "Phil Nakamura",
        "from_email": "pnakamura@midas.org",
        "to": ["maury@attainpartners.com"],
        "cc": [],
        "received": "2025-03-03T07:55:00Z",
        "preview": "Maury, the quarterly data export is behaving oddly — it seems like some records are missing from the output but we're not sure if it's a config issue or a bug. Not urgent but would love your eyes on it this week.",
        "is_read": False,
        "importance": "normal",
        "has_attachments": False,
        "flagged": False,
        "folder": "inbox",
        "source": "outlook",
    },
    {
        "id": "mock_006",
        "subject": "Salesforce Spring '25 Release Notes Now Available",
        "from_name": "Salesforce",
        "from_email": "noreply@salesforce.com",
        "to": ["maury@attainpartners.com"],
        "cc": [],
        "received": "2025-03-02T18:00:00Z",
        "preview": "The Spring '25 release notes are available. Key highlights: Flow improvements, LWC enhancements, Einstein features.",
        "is_read": True,
        "importance": "low",
        "has_attachments": False,
        "flagged": False,
        "folder": "inbox",
        "source": "outlook",
    },
]

MOCK_NOTES = [
    {
        "guid": "mock_note_001",
        "title": "Daily Schedule - March 3, 2025",
        "updated": "2025-03-03T06:30:00",
        "created": "2025-03-03T06:30:00",
        "content": """Daily Schedule - Monday March 3

9:30 AM - Team Standup (Attain Internal)
11:00 AM - Michigan SBDC County Map QA Review Call
2:00 PM - Darden UAT Review with James
4:00 PM - Focus Block: Impact Record Flow Refactor

To-Do Today:
- Fix D3 tooltip JS error (Michigan SBDC) - URGENT
- Investigate Darden financial summary blank panel
- Look into UPenn SSO 500 error - production blocking
- Update biweekly huddle dashboard before Thursday
- Check Mogli v4.2 release notes""",
        "source": "evernote",
    },
]

MOCK_JIRA_RESULT = [
    {
        "status": "created",
        "key": "MSBDC-142",
        "url": "https://attainpartners.atlassian.net/browse/MSBDC-142",
        "project_key": "MSBDC",
        "summary": "County Map LWC D3 tooltip throwing JS exception on hover",
        "priority": "Highest",
        "issue_type": "Bug",
    },
    {
        "status": "created",
        "key": "DARDENEXED-89",
        "url": "https://attainpartners.atlassian.net/browse/DARDENEXED-89",
        "project_key": "DARDENEXED",
        "summary": "Transfer Registration Step 2 financial summary not rendering",
        "priority": "High",
        "issue_type": "Bug",
    },
    {
        "status": "created",
        "key": "USS-34",
        "url": "https://attainpartners.atlassian.net/browse/USS-34",
        "project_key": "USS",
        "summary": "SSO login 500 error blocking 40% of student users",
        "priority": "Highest",
        "issue_type": "Bug",
    },
    {
        "status": "proposed",
        "ticket_id": "proposed_20250303_0755_0",
        "jira": {
            "summary": "MIDAS data export missing records — investigate",
            "project_key": "AMS",
            "priority": "Medium",
            "issue_type": "Task",
        },
    },
]
