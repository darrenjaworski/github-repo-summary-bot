# GitHub Repository Summary Bot

A Python bot that monitors multiple GitHub repositories for changes and generates AI-powered summaries of commits, pull requests, and repository activity using OpenAI.

## Features

- **Multi-repository monitoring**: Track changes across multiple GitHub repositories
- **AI-powered summaries**: Generate intelligent summaries using OpenAI models
- **Slack notifications**: Send summaries directly to Slack channels via webhooks
- **Persistent storage**: SQLite database to track repository states and store summaries
- **Scheduled checks**: Configurable schedule for automatic repository monitoring
- **Change detection**: Only generates summaries when new activity is detected

## Setup

### Prerequisites

1. **GitHub Token**: Create a personal access token at https://github.com/settings/tokens
2. **OpenAI API Key**: Get an API key from https://platform.openai.com/api-keys
3. **Slack Webhook** (optional): For notifications, set up a webhook at https://api.slack.com/messaging/webhooks

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
   Edit `.env` and add your tokens:
   ```
   GITHUB_TOKEN=your_actual_github_token_here
   OPENAI_API_KEY=your_openai_api_key_here

   # Optional: For Slack notifications
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   SLACK_CHANNEL=#repo-updates
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

### Setup Virtual Environment

```bash
# Set up virtual environment and dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### CLI Commands

#### Initialize configuration
```bash
python cli.py init
```
Creates `.env` and `repos.json` configuration files with sample content.

#### Test single repository
```bash
source venv/bin/activate
python cli.py check microsoft/vscode
```

#### Check all configured repositories
```bash
source venv/bin/activate
python cli.py check-all
```

#### View recent summaries
```bash
source venv/bin/activate
python cli.py summaries -l 5
```

#### Test Slack connection
```bash
source venv/bin/activate
python cli.py test-slack
```

#### Run in daemon mode (scheduled checks)
```bash
source venv/bin/activate
python cli.py daemon
```

### Direct Module Usage

```bash
source venv/bin/activate
python repo_summary_bot.py
```

The bot will:
1. Create a sample `repos.json` if it doesn't exist
2. Perform an initial check of all configured repositories
3. Schedule regular checks based on your configuration
4. Generate summaries for repositories with new activity

### Programmatic Usage

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
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: OpenAI model to use for summaries (default: gpt-4o-mini)
- `REPO_CONFIG_FILE`: Path to repository configuration file (default: repos.json)
- `SLACK_WEBHOOK_URL`: Slack webhook URL for notifications (optional)
- `SLACK_CHANNEL`: Slack channel for notifications (optional, defaults to webhook's configured channel)

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
- OpenAI API key
- Optional: Slack workspace with webhook access
- Required Python packages (see requirements.txt)

## Slack Setup

To receive notifications in Slack:

1. **Create a Slack App**:
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name your app and select your workspace

2. **Enable Incoming Webhooks**:
   - In your app settings, go to "Incoming Webhooks"
   - Toggle "Activate Incoming Webhooks" to On
   - Click "Add New Webhook to Workspace"
   - Select the channel where you want notifications
   - Copy the webhook URL

3. **Configure the Bot**:
   - Add the webhook URL to your `.env` file as `SLACK_WEBHOOK_URL`
   - Optionally specify a channel with `SLACK_CHANNEL` (overrides webhook default)
   - Test the connection: `python cli.py test-slack`

## License

This project is open source. Use it however you'd like!