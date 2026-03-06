"""
modules/formatter.py — HTML + text briefing formatter with Jira results
"""

from datetime import datetime
from modules.classifier import CATEGORIES


def format_briefing_text(briefing: dict) -> str:
    lines = []
    lines.append(f"\n📋 MORNING BRIEFING — {briefing.get('date','')}")
    lines.append("─" * 60)
    lines.append(f"\n{briefing.get('summary','')}\n")

    cats = briefing.get("categories", {})
    for key, label in CATEGORIES.items():
        items = cats.get(key, [])
        if not items:
            continue
        lines.append(f"\n{label} ({len(items)})")
        lines.append("─" * 40)
        for item in items:
            lines.append(f"  • {item.get('title','')}")
            client = item.get("client","")
            if client and client not in ("N/A",""):
                lines.append(f"    Client: {client}")
            lines.append(f"    {item.get('detail','')}")
            jr = item.get("jira_result")
            if jr:
                if jr.get("status") == "created":
                    lines.append(f"    🎫 Jira: [{jr.get('key','')}] {jr.get('url','')} ({jr.get('priority','')})")
                elif jr.get("status") == "proposed":
                    lines.append(f"    📋 Jira proposed → run: python approve_tickets.py")

    todos = briefing.get("todos", [])
    if todos:
        lines.append(f"\n📝 TO-DO'S ({len(todos)})")
        lines.append("─" * 40)
        for t in todos:
            icon = {"high":"❗","medium":"◦","low":"·"}.get(t.get("priority","medium"),"◦")
            lines.append(f"  {icon} [{t.get('client','')}] {t.get('task','')}")

    schedule = briefing.get("schedule", [])
    if schedule:
        lines.append(f"\n📅 SCHEDULE")
        lines.append("─" * 40)
        for s in schedule:
            lines.append(f"  {s.get('time','')} — {s.get('event','')}")
            if s.get("note"):
                lines.append(f"    {s['note']}")

    # Jira summary block
    jira_results = briefing.get("jira_results", [])
    created  = [r for r in jira_results if r.get("status") == "created"]
    proposed = [r for r in jira_results if r.get("status") == "proposed"]
    failed   = [r for r in jira_results if r.get("status") == "failed"]

    if created or proposed or failed:
        lines.append(f"\n🎫 JIRA TICKETS")
        lines.append("─" * 40)
        for r in created:
            lines.append(f"  ✅ [{r.get('key','')}] {r.get('summary','')[:55]} ({r.get('priority','')})")
            lines.append(f"     {r.get('url','')}")
        for r in proposed:
            jira = r.get("jira",{})
            lines.append(f"  📋 PROPOSED [{jira.get('project_key','')}] {jira.get('summary','')[:55]}")
        for r in failed:
            lines.append(f"  ❌ FAILED: {r.get('summary','')[:55]} — {r.get('error','')}")
        if proposed:
            lines.append(f"\n  → Run 'python approve_tickets.py' to review proposed tickets")

    flags = briefing.get("flags", {})
    overdue  = flags.get("overdue", [])
    waiting  = flags.get("waiting_on", [])
    followups = flags.get("follow_ups", [])
    if overdue or waiting or followups:
        lines.append(f"\n🚩 FLAGS")
        lines.append("─" * 40)
        for f in overdue:   lines.append(f"  ⏰ OVERDUE: {f}")
        for f in waiting:   lines.append(f"  ⏳ WAITING ON: {f}")
        for f in followups: lines.append(f"  🔁 FOLLOW UP: {f}")

    meta = briefing.get("meta", {})
    lines.append(f"\n{'─'*60}")
    lines.append(f"Generated: {meta.get('generated_at','')}  |  {meta.get('email_count',0)} emails · {meta.get('note_count',0)} notes")
    return "\n".join(lines)


def format_briefing_html(briefing: dict) -> str:
    date     = briefing.get("date", datetime.now().strftime("%A, %B %d %Y"))
    summary  = briefing.get("summary","")
    cats     = briefing.get("categories",{})
    todos    = briefing.get("todos",[])
    schedule = briefing.get("schedule",[])
    flags    = briefing.get("flags",{})
    meta     = briefing.get("meta",{})
    jira_results = briefing.get("jira_results",[])

    color_map = {
        "urgent_action":"#ef4444","client":"#f97316",
        "internal":"#eab308","vendor_tools":"#3b82f6","fyi":"#9ca3af",
    }

    cat_html = ""
    for key, label in CATEGORIES.items():
        items = cats.get(key,[])
        if not items: continue
        accent = color_map.get(key,"#6b7280")
        items_html = ""
        for item in items:
            client_badge = f'<span class="badge">{item.get("client","")}</span>' if item.get("client") and item.get("client") != "N/A" else ""
            jr = item.get("jira_result")
            jira_tag = ""
            if jr:
                if jr.get("status") == "created":
                    jira_tag = f'<a class="jira-tag auto" href="{jr.get("url","")}" target="_blank">🎫 {jr.get("key","")} ({jr.get("priority","")})</a>'
                elif jr.get("status") == "proposed":
                    jira_tag = '<span class="jira-tag proposed">📋 Proposed ticket</span>'

            items_html += f"""
            <div class="card">
              <div class="card-header">
                <span class="card-title">{item.get('title','')}</span>
                {client_badge}{jira_tag}
              </div>
              <div class="card-from">From: {item.get('from','')}</div>
              <div class="card-detail">{item.get('detail','')}</div>
            </div>"""

        cat_html += f"""
        <section class="category" style="--accent:{accent}">
          <h2 class="category-title">{label} <span class="count">{len(items)}</span></h2>
          {items_html}
        </section>"""

    # Jira summary section
    created  = [r for r in jira_results if r.get("status") == "created"]
    proposed = [r for r in jira_results if r.get("status") == "proposed"]
    jira_html = ""
    if created or proposed:
        rows = ""
        for r in created:
            rows += f"""
            <div class="jira-row">
              <span class="jira-status created">✅ Created</span>
              <a class="jira-key" href="{r.get('url','')}" target="_blank">{r.get('key','')}</a>
              <span class="jira-priority prio-{r.get('priority','Medium').lower()}">{r.get('priority','')}</span>
              <span class="jira-summary">{r.get('summary','')}</span>
            </div>"""
        for r in proposed:
            jira = r.get("jira",{})
            rows += f"""
            <div class="jira-row">
              <span class="jira-status proposed">📋 Proposed</span>
              <span class="jira-key">{jira.get('project_key','')}</span>
              <span class="jira-priority prio-{jira.get('priority','Medium').lower()}">{jira.get('priority','')}</span>
              <span class="jira-summary">{jira.get('summary','')}</span>
            </div>"""
        approve_note = '<div class="approve-note">→ Run <code>python approve_tickets.py</code> to review proposed tickets</div>' if proposed else ""
        jira_html = f"""
        <section class="category" style="--accent:#8b5cf6">
          <h2 class="category-title">🎫 Jira Tickets <span class="count">{len(created)+len(proposed)}</span></h2>
          <div class="jira-list">{rows}</div>
          {approve_note}
        </section>"""

    # Todos
    todo_html = ""
    if todos:
        prio_colors = {"high":"#ef4444","medium":"#f97316","low":"#9ca3af"}
        rows = ""
        for t in todos:
            color = prio_colors.get(t.get("priority","medium"),"#9ca3af")
            rows += f"<tr><td><span class='dot' style='background:{color}'></span>{t.get('priority','')}</td><td>{t.get('client','')}</td><td>{t.get('task','')}</td><td class='source-tag'>{t.get('source','')}</td></tr>"
        todo_html = f"""
        <section class="category" style="--accent:#8b5cf6">
          <h2 class="category-title">📝 To-Do's <span class="count">{len(todos)}</span></h2>
          <table class="todo-table">
            <thead><tr><th>Priority</th><th>Client</th><th>Task</th><th>Source</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </section>"""

    # Schedule
    sched_html = ""
    if schedule:
        events = ""
        for s in schedule:
            note = f'<div class="sched-note">{s["note"]}</div>' if s.get("note") else ""
            events += f'<div class="sched-row"><div class="sched-time">{s.get("time","")}</div><div class="sched-content"><div class="sched-event">{s.get("event","")}</div>{note}</div></div>'
        sched_html = f"""
        <section class="category" style="--accent:#10b981">
          <h2 class="category-title">📅 Schedule</h2>{events}
        </section>"""

    # Flags
    flags_html = ""
    overdue   = flags.get("overdue",[])
    waiting   = flags.get("waiting_on",[])
    followups = flags.get("follow_ups",[])
    if overdue or waiting or followups:
        flag_items = "".join(
            [f'<div class="flag overdue">⏰ OVERDUE: {f}</div>' for f in overdue] +
            [f'<div class="flag waiting">⏳ WAITING ON: {f}</div>' for f in waiting] +
            [f'<div class="flag followup">🔁 FOLLOW UP: {f}</div>' for f in followups]
        )
        flags_html = f"""
        <section class="category" style="--accent:#ec4899">
          <h2 class="category-title">🚩 Flags</h2>{flag_items}
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Morning Briefing — {date}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--bg:#0f1117;--surface:#1a1d27;--surface2:#22263a;--border:#2d3148;--text:#e2e8f0;--muted:#64748b;--mono:'IBM Plex Mono',monospace;--sans:'IBM Plex Sans',sans-serif}}
  body{{font-family:var(--sans);background:var(--bg);color:var(--text);min-height:100vh;padding:2rem 1rem}}
  .container{{max-width:900px;margin:0 auto}}
  header{{border-left:4px solid #6366f1;padding:1.5rem 1.5rem 1.5rem 2rem;background:var(--surface);border-radius:0 12px 12px 0;margin-bottom:2rem}}
  .date-line{{font-family:var(--mono);font-size:.75rem;color:#6366f1;letter-spacing:.15em;text-transform:uppercase;margin-bottom:.5rem}}
  header h1{{font-size:1.8rem;font-weight:600;margin-bottom:1rem;letter-spacing:-.02em}}
  .summary{{color:#94a3b8;font-size:.95rem;line-height:1.7;font-weight:300}}
  .meta{{font-family:var(--mono);font-size:.7rem;color:var(--muted);margin-top:1rem}}
  .category{{margin-bottom:1.5rem;border:1px solid var(--border);border-top:3px solid var(--accent);border-radius:8px;overflow:hidden}}
  .category-title{{font-size:.8rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;padding:.75rem 1.25rem;background:var(--surface);color:var(--accent);display:flex;align-items:center;gap:.75rem;border-bottom:1px solid var(--border)}}
  .count{{background:var(--accent);color:#000;font-family:var(--mono);font-size:.65rem;padding:.1rem .5rem;border-radius:999px}}
  .card{{padding:1rem 1.25rem;border-bottom:1px solid var(--border);background:var(--surface2)}}
  .card:last-child{{border-bottom:none}}
  .card:hover{{background:#252940}}
  .card-header{{display:flex;align-items:center;gap:.75rem;margin-bottom:.35rem;flex-wrap:wrap}}
  .card-title{{font-weight:600;font-size:.9rem}}
  .badge{{font-family:var(--mono);font-size:.65rem;padding:.1rem .6rem;background:var(--surface);border:1px solid var(--border);border-radius:4px;color:var(--muted)}}
  .jira-tag{{font-family:var(--mono);font-size:.65rem;padding:.15rem .6rem;border-radius:4px;text-decoration:none}}
  .jira-tag.auto{{background:#1e2d4a;color:#60a5fa;border:1px solid #3b5a8a}}
  .jira-tag.proposed{{background:#2a1e4a;color:#a78bfa;border:1px solid #5b3a8a}}
  .card-from{{font-size:.75rem;color:var(--muted);font-family:var(--mono);margin-bottom:.35rem}}
  .card-detail{{font-size:.85rem;color:#94a3b8;line-height:1.5}}
  .jira-list{{padding:.5rem 0}}
  .jira-row{{display:flex;align-items:center;gap:1rem;padding:.65rem 1.25rem;border-bottom:1px solid var(--border);background:var(--surface2);flex-wrap:wrap}}
  .jira-row:last-child{{border-bottom:none}}
  .jira-status{{font-size:.75rem;white-space:nowrap}}
  .jira-key{{font-family:var(--mono);font-size:.8rem;color:#60a5fa;text-decoration:none;white-space:nowrap}}
  .jira-key:hover{{text-decoration:underline}}
  .jira-summary{{font-size:.85rem;color:#94a3b8}}
  .jira-priority{{font-family:var(--mono);font-size:.65rem;padding:.1rem .5rem;border-radius:4px;white-space:nowrap}}
  .prio-highest,.prio-high{{background:#3d1515;color:#fca5a5}}
  .prio-medium{{background:#3d2e15;color:#fcd34d}}
  .prio-low{{background:#1e2d4a;color:#93c5fd}}
  .approve-note{{padding:.75rem 1.25rem;font-size:.8rem;color:#a78bfa;background:var(--surface);font-family:var(--mono)}}
  .approve-note code{{background:#1e1e30;padding:.1rem .4rem;border-radius:3px}}
  .todo-table{{width:100%;border-collapse:collapse;font-size:.85rem}}
  .todo-table th{{text-align:left;padding:.6rem 1.25rem;background:var(--surface);color:var(--muted);font-family:var(--mono);font-size:.7rem;letter-spacing:.05em;border-bottom:1px solid var(--border)}}
  .todo-table td{{padding:.75rem 1.25rem;border-bottom:1px solid var(--border);background:var(--surface2);vertical-align:middle}}
  .todo-table tr:last-child td{{border-bottom:none}}
  .dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:.5rem;vertical-align:middle}}
  .source-tag{{font-family:var(--mono);font-size:.7rem;color:var(--muted)}}
  .sched-row{{display:flex;gap:1.5rem;padding:.85rem 1.25rem;border-bottom:1px solid var(--border);background:var(--surface2)}}
  .sched-row:last-child{{border-bottom:none}}
  .sched-time{{font-family:var(--mono);font-size:.75rem;color:#10b981;white-space:nowrap;min-width:80px;padding-top:2px}}
  .sched-event{{font-size:.9rem;font-weight:500}}
  .sched-note{{font-size:.8rem;color:var(--muted);margin-top:.2rem}}
  .flag{{padding:.75rem 1.25rem;border-bottom:1px solid var(--border);font-size:.85rem;background:var(--surface2)}}
  .flag:last-child{{border-bottom:none}}
  .flag.overdue{{color:#fca5a5}}
  .flag.waiting{{color:#fcd34d}}
  .flag.followup{{color:#a5b4fc}}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="date-line">Morning Briefing</div>
    <h1>{date}</h1>
    <div class="summary">{summary}</div>
    <div class="meta">Generated {meta.get('generated_at','')} &nbsp;·&nbsp; {meta.get('email_count',0)} emails &nbsp;·&nbsp; {meta.get('note_count',0)} Evernote notes</div>
  </header>
  {cat_html}
  {jira_html}
  {todo_html}
  {sched_html}
  {flags_html}
</div>
</body>
</html>"""
