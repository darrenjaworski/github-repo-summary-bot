# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GitHub Repository Summary Bot that monitors multiple GitHub repositories for changes and generates AI-powered summaries of commits and pull requests using OpenAI. The bot stores repository state and summaries in a SQLite database and can run on a schedule.

## Architecture

- **`repo_summary_bot.py`**: Core `GitHubRepoBot` class containing all business logic for GitHub API integration, change detection, AI summarization, and database operations
- **`cli.py`**: Command-line interface that wraps the bot functionality with subcommands for different operations
- **Configuration**: Uses `.env` for secrets and `repos.json` for repository list and schedule configuration
- **Database**: SQLite database (`repo_summaries.db`) with tables for repository states and generated summaries

## Development Setup

This project uses a virtual environment for Python dependencies:

```bash
# Set up virtual environment and dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Common Commands

### Initialize configuration
```bash
python cli.py init
```
Creates `.env` and `repos.json` configuration files with sample content.

### Test single repository
```bash
source venv/bin/activate
python cli.py check microsoft/vscode
```

### Check all configured repositories
```bash
source venv/bin/activate
python cli.py check-all
```

### View recent summaries
```bash
source venv/bin/activate
python cli.py summaries -l 5
```

### Test Slack connection
```bash
source venv/bin/activate
python cli.py test-slack
```

### Run in daemon mode (scheduled checks)
```bash
source venv/bin/activate
python cli.py daemon
```

### Direct module usage
```bash
source venv/bin/activate
python repo_summary_bot.py
```

## Configuration Requirements

The bot requires:
1. **GitHub Token**: Set `GITHUB_TOKEN` in `.env` file (get from https://github.com/settings/tokens)
2. **OpenAI API Key**: Set `OPENAI_API_KEY` in `.env` file (get from https://platform.openai.com/api-keys)
3. **Repository List**: Configure repositories to monitor in `repos.json`

### Optional Slack Notifications

To receive summaries in Slack:
1. **Slack Webhook URL**: Set `SLACK_WEBHOOK_URL` in `.env` file (get from https://api.slack.com/messaging/webhooks)
2. **Slack Channel** (optional): Set `SLACK_CHANNEL` in `.env` file (e.g., `#repo-updates` or `@username`)

## Database Schema

The SQLite database has two main tables:
- `repo_states`: Tracks last commit SHA and check timestamp for each repository
- `summaries`: Stores generated summaries with metadata (repo name, change count, timestamp)

## Key Classes and Methods

- `GitHubRepoBot.__init__()`: Initializes with GitHub token, OpenAI API key, and database setup
- `GitHubRepoBot.check_repo_for_changes()`: Main method that checks a repository, generates summaries if changes found
- `GitHubRepoBot.generate_summary()`: Uses OpenAI to create AI summaries from repository changes
- `GitHubRepoBot.get_recent_summaries()`: Retrieves stored summaries from database

## Git Commit Guidelines

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification. When committing code, use the following format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Examples

```bash
# Feature addition
git commit -m "feat: add support for webhook notifications"

# Bug fix
git commit -m "fix: resolve database connection timeout issue"

# Documentation update
git commit -m "docs: add API usage examples to README"

# Refactoring
git commit -m "refactor: extract summary generation logic into separate module"

# Breaking change
git commit -m "feat!: change API response format for summaries

BREAKING CHANGE: summary API now returns structured data instead of plain text"
```