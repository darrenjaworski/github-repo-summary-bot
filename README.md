# GitHub Repository Summary Bot

A Python bot that monitors multiple GitHub repositories for changes and generates AI-powered summaries of commits, pull requests, and repository activity using Ollama.

## Features

- **Multi-repository monitoring**: Track changes across multiple GitHub repositories
- **AI-powered summaries**: Generate intelligent summaries using local Ollama models
- **Persistent storage**: SQLite database to track repository states and store summaries
- **Scheduled checks**: Configurable schedule for automatic repository monitoring
- **Change detection**: Only generates summaries when new activity is detected

## Setup

### Prerequisites

1. **GitHub Token**: Create a personal access token at https://github.com/settings/tokens
2. **Ollama**: Install and run Ollama locally with a model (e.g., `ollama pull llama3.2`)

### Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create your environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your GitHub token:
   ```
   GITHUB_TOKEN=your_actual_github_token_here
   ```

4. Create your repository configuration:
   ```bash
   cp repos.json.example repos.json
   ```
   Edit `repos.json` to include the repositories you want to monitor:
   ```json
   {
     "repositories": [
       "owner/repo-name",
       "microsoft/vscode",
       "facebook/react"
     ],
     "schedule_hours": [9, 17],
     "timezone": "UTC"
   }
   ```

## Usage

### Run the bot

```bash
python repo_summary_bot.py
```

The bot will:
1. Create a sample `repos.json` if it doesn't exist
2. Perform an initial check of all configured repositories
3. Schedule regular checks based on your configuration
4. Generate summaries for repositories with new activity

### Manual repository check

You can also import and use the bot programmatically:

```python
from repo_summary_bot import GitHubRepoBot

bot = GitHubRepoBot()

# Check a single repository
summary = bot.check_repo_for_changes("microsoft/vscode")

# Check multiple repositories
repositories = ["facebook/react", "nodejs/node"]
bot.check_all_repos(repositories)

# Get recent summaries
recent = bot.get_recent_summaries(limit=5)
for summary in recent:
    print(f"{summary['repo_name']}: {summary['summary'][:100]}...")
```

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: Your GitHub personal access token (required)
- `OLLAMA_MODEL`: Ollama model to use for summaries (default: llama3.2)
- `REPO_CONFIG_FILE`: Path to repository configuration file (default: repos.json)

### Repository Configuration (repos.json)

- `repositories`: List of GitHub repositories in "owner/name" format
- `schedule_hours`: Hours of the day (24-hour format) to run checks
- `timezone`: Timezone for scheduling (default: UTC)

## Database

The bot uses SQLite to store:
- Repository states (last commit SHA, last check timestamp)
- Generated summaries with metadata

Database file: `repo_summaries.db` (created automatically)

## Requirements

- Python 3.7+
- GitHub personal access token
- Ollama running locally
- Required Python packages (see requirements.txt)

## License

This project is open source. Use it however you'd like!