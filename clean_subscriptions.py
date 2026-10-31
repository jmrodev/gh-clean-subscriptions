#!/usr/bin/env python3
"""
Clean GitHub Subscriptions & Notifications
Keeps only TECDA-related repositories and personal (jmrodev) repositories.
Unwatches third-party external repositories and removes notifications directly (Done/Archive).
"""

import argparse
import json
import subprocess
import sys

DEFAULT_KEEP_PREFIXES = [
    "jmrodev/",
    "3rotecda2026/",
    "tecdron/",
    "tecda-maniqui-factory/",
    "ecommerce-economia-empresarial-tecda/",
]

def run_gh(args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        return None, result.stderr.strip()
    return result.stdout.strip(), None

def is_kept(repo_name, keep_prefixes):
    lower = repo_name.lower()
    if "tecda" in lower:
        return True
    return any(lower.startswith(p.lower()) for p in keep_prefixes)

def main():
    parser = argparse.ArgumentParser(
        description="Filter GitHub subscriptions and manage notification inbox."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without unsubscribing or removing notifications."
    )
    parser.add_argument(
        "--keep",
        nargs="*",
        default=[],
        help="Additional repository prefixes to keep."
    )
    parser.add_argument(
        "--clear-all",
        action="store_true",
        help="Eliminate ALL notifications from inbox (mark all as Done, including TECDA/jmrodev)."
    )
    args = parser.parse_args()

    keep_prefixes = DEFAULT_KEEP_PREFIXES + args.keep

    print("🔍 Fetching subscribed repositories from GitHub...")
    out, err = run_gh(["api", "user/subscriptions", "--paginate"])
    if err:
        print(f"❌ Error fetching subscriptions: {err}", file=sys.stderr)
        sys.exit(1)

    try:
        repos = json.loads(out)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse GitHub API response: {e}", file=sys.stderr)
        sys.exit(1)

    to_keep = []
    to_unwatch = []

    for r in repos:
        full_name = r.get("full_name", "")
        if is_kept(full_name, keep_prefixes):
            to_keep.append(full_name)
        else:
            to_unwatch.append(full_name)

    print(f"\n✅ Repositories to keep ({len(to_keep)}):")
    for k in to_keep:
        print(f"   • {k}")

    print(f"\n🧹 Repositories to unwatch ({len(to_unwatch)}):")
    for u in to_unwatch:
        print(f"   • {u}")

    if not to_unwatch:
        print("\n✨ All subscriptions already match the allowed list. Nothing to unwatch.")
    else:
        if args.dry_run:
            print("\n[DRY RUN] No subscription changes were made.")
        else:
            print(f"\n🚀 Unwatching {len(to_unwatch)} repositories...")
            for repo in to_unwatch:
                print(f"   → Unwatching {repo}...")
                run_gh(["api", "-X", "DELETE", f"repos/{repo}/subscription"])

    # Process notifications inbox
    print("\n📬 Fetching notifications from inbox...")
    notifs_out, _ = run_gh(["api", "notifications", "--paginate"])
    if notifs_out:
        try:
            notifs = json.loads(notifs_out)
        except Exception:
            notifs = []
    else:
        notifs = []

    to_delete = []
    for n in notifs:
        repo_name = n.get("repository", {}).get("full_name", "")
        thread_id = n.get("id")
        title = n.get("subject", {}).get("title", "")
        if args.clear_all:
            to_delete.append((thread_id, repo_name, title))
        elif not is_kept(repo_name, keep_prefixes):
            to_delete.append((thread_id, repo_name, title))

    if not to_delete:
        print("✨ No notifications to eliminate.")
    else:
        action_msg = "Eliminating ALL notifications (--clear-all active)" if args.clear_all else f"Eliminating {len(to_delete)} external notifications"
        print(f"\n🗑️  {action_msg}...")
        for thread_id, repo_name, title in to_delete:
            if args.dry_run:
                print(f"   [DRY RUN] Would delete thread {thread_id} ({repo_name}: {title})")
            else:
                print(f"   → Eliminating: {repo_name} -> {title}")
                run_gh(["api", "-X", "DELETE", f"notifications/threads/{thread_id}"])

    print("\n🎉 Done! Everything up to date.")

if __name__ == "__main__":
    main()
