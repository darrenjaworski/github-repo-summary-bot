#!/usr/bin/env python3
"""
Command Line Interface for GitHub Repository Summary Bot
"""

import argparse
import json
import os
import sys
from datetime import datetime
from repo_summary_bot import GitHubRepoBot

def init_config(args):
    """Initialize configuration files"""
    config_file = args.config or "repos.json"
    env_file = ".env"

    # Create .env file if it doesn't exist
    if not os.path.exists(env_file):
        with open(".env.example", "r") as example:
            content = example.read()

        with open(env_file, "w") as f:
            f.write(content)

        print(f"Created {env_file} - please edit it to add your GitHub token")

    # Create repos.json if it doesn't exist
    if not os.path.exists(config_file):
        sample_config = {
            "repositories": [
                "microsoft/vscode",
                "facebook/react"
            ],
            "schedule_hours": [9, 17],
            "timezone": "UTC"
        }

        with open(config_file, "w") as f:
            json.dump(sample_config, f, indent=2)

        print(f"Created {config_file} - please edit it to add your repositories")

    print("Configuration files ready!")

def check_single(args):
    """Check a single repository"""
    try:
        bot = GitHubRepoBot()
        summary = bot.check_repo_for_changes(args.repo)

        if summary:
            print(f"\nSummary for {args.repo}:")
            print("=" * 50)
            print(summary)
        else:
            print(f"No new changes found in {args.repo}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def check_all(args):
    """Check all configured repositories"""
    config_file = args.config or "repos.json"

    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found. Run 'python cli.py init' first.")
        sys.exit(1)

    try:
        with open(config_file, "r") as f:
            config = json.load(f)

        repositories = config.get("repositories", [])

        if not repositories:
            print(f"No repositories configured in {config_file}")
            sys.exit(1)

        bot = GitHubRepoBot()
        bot.check_all_repos(repositories)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def show_summaries(args):
    """Show recent summaries"""
    try:
        bot = GitHubRepoBot()
        summaries = bot.get_recent_summaries(args.repo, args.limit)

        if not summaries:
            repo_msg = f" for {args.repo}" if args.repo else ""
            print(f"No summaries found{repo_msg}")
            return

        for summary in summaries:
            print(f"\n{'='*60}")
            print(f"Repository: {summary['repo_name']}")
            print(f"Changes: {summary['changes_count']}")
            print(f"Date: {summary['timestamp']}")
            print(f"{'='*60}")
            print(summary['summary'])

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def run_daemon(args):
    """Run the bot in daemon mode"""
    config_file = args.config or "repos.json"

    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found. Run 'python cli.py init' first.")
        sys.exit(1)

    try:
        # Import here to avoid import errors if schedule not needed
        import schedule
        import time

        with open(config_file, "r") as f:
            config = json.load(f)

        repositories = config.get("repositories", [])
        schedule_hours = config.get("schedule_hours", [9, 17])

        if not repositories:
            print(f"No repositories configured in {config_file}")
            sys.exit(1)

        bot = GitHubRepoBot()

        # Schedule regular checks
        for hour in schedule_hours:
            schedule.every().day.at(f"{hour:02d}:00").do(
                lambda: bot.check_all_repos(repositories)
            )

        print(f"Bot started in daemon mode")
        print(f"Monitoring {len(repositories)} repositories")
        print(f"Scheduled checks at: {', '.join(f'{h}:00' for h in schedule_hours)}")
        print("Press Ctrl+C to stop")

        # Run initial check
        if not args.no_initial:
            print("\nRunning initial check...")
            bot.check_all_repos(repositories)

        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)

    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="GitHub Repository Summary Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py init                          # Initialize configuration
  python cli.py check microsoft/vscode       # Check single repository
  python cli.py check-all                    # Check all configured repos
  python cli.py summaries -l 5               # Show 5 recent summaries
  python cli.py daemon                       # Run in scheduled mode
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize configuration files")
    init_parser.add_argument("--config", help="Configuration file path (default: repos.json)")
    init_parser.set_defaults(func=init_config)

    # Check single repository
    check_parser = subparsers.add_parser("check", help="Check a single repository")
    check_parser.add_argument("repo", help="Repository name (owner/repo)")
    check_parser.set_defaults(func=check_single)

    # Check all repositories
    check_all_parser = subparsers.add_parser("check-all", help="Check all configured repositories")
    check_all_parser.add_argument("--config", help="Configuration file path (default: repos.json)")
    check_all_parser.set_defaults(func=check_all)

    # Show summaries
    summaries_parser = subparsers.add_parser("summaries", help="Show recent summaries")
    summaries_parser.add_argument("--repo", help="Show summaries for specific repository only")
    summaries_parser.add_argument("-l", "--limit", type=int, default=10, help="Number of summaries to show (default: 10)")
    summaries_parser.set_defaults(func=show_summaries)

    # Daemon mode
    daemon_parser = subparsers.add_parser("daemon", help="Run bot in scheduled daemon mode")
    daemon_parser.add_argument("--config", help="Configuration file path (default: repos.json)")
    daemon_parser.add_argument("--no-initial", action="store_true", help="Skip initial check on startup")
    daemon_parser.set_defaults(func=run_daemon)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main()