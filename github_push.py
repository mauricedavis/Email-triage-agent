#!/usr/bin/env python3
"""
github_push.py
==============
Run this ONCE from inside the email-triage-agent folder to:
  1. Create the private GitHub repo (mauricedavis/Email-triage-agent)
  2. Initialize git and push all files

Usage:
    cd C:\\Users\\MauriceJDavis\\email-triage-agent
    python github_push.py

You will be prompted to paste your GitHub Personal Access Token.
The token is used only for this session and never stored.
"""

import subprocess
import sys
import json
import urllib.request
import urllib.error
import getpass
import os

GITHUB_USER = "mauricedavis"
REPO_NAME   = "Email-triage-agent"
REPO_DESC   = "AI-powered email triage agent: Outlook + Evernote + Claude AI + Jira auto-ticketing"
LOCAL_PATH  = r"C:\Users\MauriceJDavis\email-triage-agent"


def run(cmd, cwd=None, check=True):
    """Run a shell command and print output."""
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0 and check:
        print(f"  ❌ Error: {result.stderr.strip()}")
        sys.exit(1)
    return result


def create_github_repo(token: str) -> str:
    """Create the private GitHub repo via API. Returns clone URL."""
    print(f"\n📦 Creating GitHub repo: {GITHUB_USER}/{REPO_NAME}...")

    payload = json.dumps({
        "name":        REPO_NAME,
        "description": REPO_DESC,
        "private":     True,
        "auto_init":   False,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.github.com/user/repos",
        data=payload,
        headers={
            "Authorization":  f"token {token}",
            "Accept":         "application/vnd.github.v3+json",
            "Content-Type":   "application/json",
            "User-Agent":     "email-triage-agent-setup",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            url = data["html_url"]
            print(f"  ✅ Repo created: {url}")
            return data["clone_url"]
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode())
        if "already exists" in str(body.get("errors", "")):
            print(f"  ℹ️  Repo already exists — pushing to existing repo")
            return f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"
        print(f"  ❌ GitHub API error {e.code}: {body}")
        sys.exit(1)


def push_to_github(token: str, clone_url: str, local_path: str):
    """Initialize git in local_path and push to GitHub."""
    print(f"\n🗂️  Setting up git in: {local_path}")

    # Embed token in remote URL for auth
    auth_url = clone_url.replace("https://", f"https://{token}@")

    os.makedirs(local_path, exist_ok=True)

    run("git init",                       cwd=local_path)
    run("git checkout -b main",           cwd=local_path, check=False)
    run('git config user.email "mjdavis@attainpartners.com"', cwd=local_path)
    run('git config user.name "Maury Davis"',                 cwd=local_path)
    run("git add .",                      cwd=local_path)
    run('git commit -m "Initial commit: Email Triage Agent — Outlook + Evernote + Claude AI + Jira"',
        cwd=local_path)
    run(f"git remote remove origin",      cwd=local_path, check=False)
    run(f"git remote add origin {auth_url}", cwd=local_path)
    run("git push -u origin main",        cwd=local_path)

    print(f"\n✅ All files pushed to https://github.com/{GITHUB_USER}/{REPO_NAME}")


def main():
    print("=" * 60)
    print("  Email Triage Agent — GitHub Setup")
    print("=" * 60)
    print()
    print("This script will:")
    print(f"  1. Create private repo: github.com/{GITHUB_USER}/{REPO_NAME}")
    print(f"  2. Push all files from: {LOCAL_PATH}")
    print()
    print("You need a GitHub Personal Access Token with 'repo' scope.")
    print("Generate one at: github.com/settings/tokens")
    print()

    token = getpass.getpass("Paste your GitHub PAT (input hidden): ").strip()
    if not token:
        print("❌ No token provided.")
        sys.exit(1)

    clone_url = create_github_repo(token)
    push_to_github(token, clone_url, LOCAL_PATH)

    print()
    print("=" * 60)
    print(f"  🎉 Done! View your repo:")
    print(f"  https://github.com/{GITHUB_USER}/{REPO_NAME}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Revoke this PAT at github.com/settings/tokens (it's no longer needed)")
    print("  2. Follow the setup checklist to configure your .env credentials")
    print("  3. Run: python agent.py --dry-run")


if __name__ == "__main__":
    main()
