#!/usr/bin/env python3
"""
scheduler.py
============
Runs the morning briefing agent on a schedule.
Run this in the background and it will trigger agent.py each morning.

Usage:
    python scheduler.py                    # Default: 7:00 AM daily
    python scheduler.py --time 06:30       # Run at 6:30 AM
    python scheduler.py --time 07:00 --slack   # Run at 7 AM and post to Slack

Alternatively, use your OS scheduler instead:
    macOS/Linux cron: 0 7 * * 1-5 cd /path/to/agent && python agent.py --slack
    Windows Task Scheduler: point to agent.py with desired args
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Morning Briefing Scheduler")
    parser.add_argument("--time", default="07:00", help="Time to run daily (HH:MM, 24h format)")
    parser.add_argument("--slack", action="store_true", help="Pass --slack to agent")
    parser.add_argument("--days", type=int, default=1, help="Days of email to look back")
    args = parser.parse_args()

    try:
        hour, minute = map(int, args.time.split(":"))
    except ValueError:
        print(f"❌ Invalid time format: {args.time}. Use HH:MM (e.g. 07:30)")
        sys.exit(1)

    agent_args = [sys.executable, "agent.py", f"--days={args.days}"]
    if args.slack:
        agent_args.append("--slack")

    print(f"🕐 Scheduler running — will trigger briefing at {args.time} daily")
    print(f"   Command: {' '.join(agent_args)}")
    print("   Press Ctrl+C to stop\n")

    last_run_date = None

    while True:
        now = datetime.now()
        today = now.date()

        if (now.hour == hour and now.minute == minute and last_run_date != today):
            print(f"\n⏰ {now.strftime('%H:%M')} — Triggering morning briefing...")
            try:
                result = subprocess.run(agent_args, check=True)
                last_run_date = today
                print(f"✅ Briefing complete at {datetime.now().strftime('%H:%M:%S')}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Agent failed with exit code {e.returncode}")

        time.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    main()
