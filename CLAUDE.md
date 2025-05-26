# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hippo is a Telegram bot that reminds users to drink water with cute cartoons and poems. The bot operates on user-configurable schedules and tracks hydration metrics to generate personalized cartoon states (6 hydration levels from dehydrated to fully engorged).

## Architecture

This is a Python-based Telegram bot project with the following core components:

- **User Management**: Handle Telegram user subscriptions and configuration
- **Scheduling System**: Support both interval-based (every 15 mins) and time-based (18th minute every hour) reminders
- **Hydration Tracking**: Persist user water drinking metrics and calculate hydration states
- **Content Generation**: Generate poems and select appropriate cartoon images based on hydration state
- **Cartoon Theming**: Support multiple cartoon sets with 6 states each, user-selectable themes

## Implementation Notes

- The project is implemented in Python 3.9+ using python-telegram-bot framework
- SQLite database for user data and hydration metrics persistence
- Cartoon images organized in themed arrays of 6 hydration states (0%, 20%, 40%, 60%, 80%, 100%)
- Bot uses async architecture with job queue for scheduled reminders
- Deployment via Docker containers on Digital Ocean

## Commands for Development

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

**Run the Bot:**
```bash
python main.py
```

**Project Structure:**
```
src/
├── bot/           # Bot logic and handlers
├── database/      # SQLite models and operations  
└── content/       # Poems and image management
assets/
└── images/        # Cartoon image files
```

## Configuration

- Copy `config.env.example` to `config.env` and add your Telegram bot token
- Bot token obtained from @BotFather on Telegram
- Database file (`hippo.db`) created automatically on first run

## Development Workflow

**CRITICAL: Always use feature branches and pull requests. NEVER commit directly to main.**

### Required Workflow
1. **Create feature branch**: `git checkout -b feature/description-of-work`
2. **Implement changes** on the feature branch
3. **Test functionality**: Test the bot implementation as appropriate
4. **Commit changes** to feature branch with descriptive messages
5. **Push branch**: `git push -u origin feature/branch-name`
6. **Test with running bot**: Before creating a PR, ask the user to verify the changes work with the running bot
7. **Create Pull Request**: Use `gh pr create` with proper title and description ONLY after user confirms the implementation works
8. **Only merge** after review/approval

### Important Development Practices

#### Commit Frequently
**Save progress often with commits** to enable easy rollback of changes:
- Commit working states before making major changes
- Use descriptive commit messages that explain what was changed
- This allows you to revert to a known-good state if something breaks
- Example: `git commit -m "Add user hydration tracking before refactoring reminder system"`

### Branch Naming Convention
- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates

## MCP Tools Note

- The MCP Puppeteer tool runs inside a Docker container
- When accessing local services with Puppeteer, use `http://host.docker.internal:PORT` instead of `http://localhost:PORT`
- This allows the Docker container to access the host machine's services