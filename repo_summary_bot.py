#!/usr/bin/env python3
"""
GitHub Repository Summary Bot

Monitors multiple GitHub repositories for changes and generates AI-powered summaries
of commits, pull requests, and other repository activity.
"""

import os
import json
import sqlite3
import requests
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class GitHubRepoBot:
    def __init__(self, db_path: str = "repo_summaries.db"):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.db_path = db_path
        self.base_url = "https://api.github.com"

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = OpenAI(api_key=self.openai_api_key)

        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        self.init_database()

    def init_database(self):
        """Initialize SQLite database for storing repository states and summaries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repo_states (
                repo_name TEXT PRIMARY KEY,
                last_commit_sha TEXT,
                last_check_timestamp TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_name TEXT,
                summary TEXT,
                changes_count INTEGER,
                timestamp TEXT,
                FOREIGN KEY (repo_name) REFERENCES repo_states (repo_name)
            )
        ''')

        conn.commit()
        conn.close()

    def get_repo_commits(self, repo_name: str, since: Optional[str] = None) -> List[Dict]:
        """Fetch commits from a repository since a specific timestamp"""
        url = f"{self.base_url}/repos/{repo_name}/commits"
        params = {}

        if since:
            params["since"] = since

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        return response.json()

    def get_repo_pulls(self, repo_name: str, state: str = "all") -> List[Dict]:
        """Fetch pull requests from a repository"""
        url = f"{self.base_url}/repos/{repo_name}/pulls"
        params = {"state": state, "sort": "updated", "direction": "desc", "per_page": 10}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        return response.json()

    def get_last_check_time(self, repo_name: str) -> Optional[str]:
        """Get the last check timestamp for a repository"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT last_check_timestamp FROM repo_states WHERE repo_name = ?",
            (repo_name,)
        )

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def update_repo_state(self, repo_name: str, last_commit_sha: str):
        """Update the repository state in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.utcnow().isoformat()

        cursor.execute('''
            INSERT OR REPLACE INTO repo_states (repo_name, last_commit_sha, last_check_timestamp)
            VALUES (?, ?, ?)
        ''', (repo_name, last_commit_sha, timestamp))

        conn.commit()
        conn.close()

    def save_summary(self, repo_name: str, summary: str, changes_count: int):
        """Save a generated summary to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.utcnow().isoformat()

        cursor.execute('''
            INSERT INTO summaries (repo_name, summary, changes_count, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (repo_name, summary, changes_count, timestamp))

        conn.commit()
        conn.close()

    def format_changes_for_ai(self, commits: List[Dict], pulls: List[Dict]) -> str:
        """Format repository changes for AI summarization"""
        content = []

        if commits:
            content.append("Recent Commits:")
            for commit in commits[:10]:  # Limit to 10 most recent
                commit_msg = commit["commit"]["message"].split("\n")[0]  # First line only
                author = commit["commit"]["author"]["name"]
                date = commit["commit"]["author"]["date"]
                content.append(f"- {commit_msg} (by {author} on {date})")

        if pulls:
            content.append("\nRecent Pull Requests:")
            for pr in pulls[:5]:  # Limit to 5 most recent
                state = pr["state"]
                title = pr["title"]
                author = pr["user"]["login"]
                updated = pr["updated_at"]
                content.append(f"- [{state.upper()}] {title} (by {author}, updated {updated})")

        return "\n".join(content)

    def generate_summary(self, changes_text: str, repo_name: str) -> str:
        """Generate AI summary of repository changes using OpenAI"""
        prompt = f"""
Please provide a concise summary of the recent activity in the GitHub repository '{repo_name}':

{changes_text}

Focus on:
1. Key features or fixes that were implemented
2. Notable contributors and their contributions
3. Overall development trends or patterns
4. Any significant pull request activity

Keep the summary under 200 words and highlight the most important changes.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def check_repo_for_changes(self, repo_name: str) -> Optional[str]:
        """Check a single repository for changes and generate summary if needed"""
        try:
            print(f"Checking repository: {repo_name}")

            last_check = self.get_last_check_time(repo_name)
            since_param = last_check if last_check else (datetime.utcnow() - timedelta(days=7)).isoformat()

            # Get recent commits and pull requests
            commits = self.get_repo_commits(repo_name, since_param)
            pulls = self.get_repo_pulls(repo_name)

            # Filter pulls updated since last check
            if last_check:
                last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                pulls = [pr for pr in pulls if datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00')) > last_check_dt]

            total_changes = len(commits) + len(pulls)

            if total_changes == 0:
                print(f"No new changes found for {repo_name}")
                return None

            print(f"Found {len(commits)} commits and {len(pulls)} pull request updates")

            # Format changes and generate summary
            changes_text = self.format_changes_for_ai(commits, pulls)
            summary = self.generate_summary(changes_text, repo_name)

            # Update database
            if commits:
                self.update_repo_state(repo_name, commits[0]["sha"])
            else:
                # Update timestamp even if no commits (for PR-only changes)
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO repo_states (repo_name, last_commit_sha, last_check_timestamp)
                    VALUES (?, COALESCE((SELECT last_commit_sha FROM repo_states WHERE repo_name = ?), ''), ?)
                ''', (repo_name, repo_name, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()

            self.save_summary(repo_name, summary, total_changes)

            print(f"Generated summary for {repo_name}:")
            print("-" * 50)
            print(summary)
            print("-" * 50)

            return summary

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {repo_name}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {repo_name}: {e}")
            return None

    def check_all_repos(self, repo_list: List[str]):
        """Check all repositories for changes"""
        print(f"Starting repository check at {datetime.now()}")

        for repo_name in repo_list:
            self.check_repo_for_changes(repo_name)

        print(f"Completed repository check at {datetime.now()}")

    def get_recent_summaries(self, repo_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Retrieve recent summaries from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if repo_name:
            cursor.execute('''
                SELECT repo_name, summary, changes_count, timestamp
                FROM summaries
                WHERE repo_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (repo_name, limit))
        else:
            cursor.execute('''
                SELECT repo_name, summary, changes_count, timestamp
                FROM summaries
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

        results = cursor.fetchall()
        conn.close()

        return [
            {
                "repo_name": row[0],
                "summary": row[1],
                "changes_count": row[2],
                "timestamp": row[3]
            }
            for row in results
        ]

def main():
    # Load repository configuration
    config_file = os.getenv("REPO_CONFIG_FILE", "repos.json")

    if not os.path.exists(config_file):
        print(f"Creating sample configuration file: {config_file}")
        sample_config = {
            "repositories": [
                "octocat/Hello-World",
                "microsoft/vscode"
            ],
            "schedule_hours": [9, 17],  # Check at 9 AM and 5 PM
            "timezone": "UTC"
        }

        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)

        print(f"Please edit {config_file} to add your repositories")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    repositories = config.get("repositories", [])
    schedule_hours = config.get("schedule_hours", [9, 17])

    if not repositories:
        print("No repositories configured. Please add repositories to repos.json")
        return

    bot = GitHubRepoBot()

    # Schedule regular checks
    for hour in schedule_hours:
        schedule.every().day.at(f"{hour:02d}:00").do(
            lambda: bot.check_all_repos(repositories)
        )

    print(f"Bot initialized. Monitoring {len(repositories)} repositories.")
    print(f"Scheduled checks at: {', '.join(f'{h}:00' for h in schedule_hours)}")
    print("Press Ctrl+C to stop.")

    # Run initial check
    bot.check_all_repos(repositories)

    # Keep the bot running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()