# 🦛 Hippo Water Reminder Bot

Hippo is a Telegram bot that helps you stay hydrated by sending friendly water reminders with cute themed cartoons and poems. Track your hydration habits, choose your favorite cartoon theme, and watch your hippo's mood change based on your water-drinking success!

## ✨ Features

### 🎨 **4 Themed Cartoon Styles**
- **Bluey**: Cool blue tones (default)
- **Desert**: Warm sandy colors
- **Spring**: Fresh green nature
- **Vivid**: Bright and colorful

Each theme shows 6 different hydration states from dehydrated to perfectly hydrated!

### 📊 **Reactive Hydration Tracking**
- **6-Level System**: From 😵 Dehydrated to 🤩 Perfect hydration
- **Rolling Average**: Based on your last 6 reminders for immediate feedback
- **Daily Stats**: Track confirmations, misses, and success rates
- **Real-time Updates**: Watch your hippo's mood change with your habits!

### ⏰ **Smart Reminder System**
- **Timezone Support**: Accurate local time with Singapore default
- **Waking Hours**: Customizable schedule (6 AM - 9 PM, etc.)
- **Flexible Intervals**: 1 minute (testing) to 2 hours
- **Auto-Expiration**: Previous reminders expire when new ones arrive

### 💬 **Engaging Content**
- **20 Unique Poems**: Varied water-themed poems with anti-repetition logic
- **Status in Reminders**: See your current level and daily progress
- **Confirmation Messages**: Encouraging feedback based on hydration level

### 🛠️ **User Management**
- **Easy Setup**: Guided configuration for all preferences
- **Complete Reset**: `/reset` command to wipe data and start fresh
- **Persistent Settings**: Your preferences are saved across sessions

## 🚀 Quick Start

1. **Start a chat** with the bot on Telegram
2. **Run `/start`** to create your account
3. **Configure settings** with `/setup`:
   - Choose your timezone
   - Set waking hours
   - Pick reminder frequency
   - Select your favorite theme
4. **Enjoy hydration reminders** with stats and cute cartoons!

## 📱 Commands

- `/start` - Welcome message and setup check
- `/setup` - Configure your reminder preferences
- `/stats` - View your hydration statistics
- `/reset` - Delete all your data and start fresh
- `/help` - Show available commands

## 🏗️ Technical Features

- **Python 3.11** with async/await architecture
- **SQLite Database** with aiosqlite for data persistence
- **Docker Support** for easy deployment
- **Timezone Handling** with pytz
- **Rolling Statistics** for reactive feedback
- **Theme Management** with organized asset structure

## 🐳 Deployment

```bash
# Clone and navigate to project
git clone <repo-url>
cd hippo

# Configure bot token
cp config.env.example config.env
# Edit config.env and add your Telegram bot token

# Deploy with Docker
docker-compose up --build -d
```

## 📁 Project Structure

```
hippo/
├── src/
│   ├── bot/           # Bot logic and handlers
│   ├── database/      # SQLite models and operations  
│   └── content/       # Poems and content management
├── assets/            # Themed cartoon images
│   ├── bluey/         # 6 hydration state images
│   ├── desert/        # 6 hydration state images
│   ├── spring/        # 6 hydration state images
│   └── vivid/         # 6 hydration state images
├── tests/             # Comprehensive test suite
├── scripts/           # Development and maintenance scripts
├── Makefile           # Development workflow automation
├── docker-compose.yml # Docker deployment config
└── requirements.txt   # Python dependencies
```

## 🎯 Hydration Levels

The bot tracks 6 hydration levels based on your recent reminder responses:

- **Level 0** 😵 Dehydrated (0/6 confirmed)
- **Level 1** 😟 Low hydration (1/6 confirmed)
- **Level 2** 😐 Moderate hydration (2/6 confirmed)
- **Level 3** 😊 Good hydration (3/6 confirmed)
- **Level 4** 😄 Great hydration (4+/6 confirmed)
- **Level 5** 🤩 Perfect hydration (5-6/6 confirmed)

## 🛠️ Makefile Commands

This project includes a comprehensive Makefile for streamlined development and deployment:

### **Quick Start**
```bash
make dev-setup    # Complete development environment setup
make test         # Run all tests
make run          # Start the bot
make logs         # View logs
```

### **Development Workflow**
```bash
make install      # Install Python dependencies
make install-dev  # Install with development tools (black, flake8, etc.)
make format       # Format code with black and isort
make lint         # Run code linting
make validate     # Run linting + tests (full validation)
```

### **Testing**
```bash
make test              # All tests (unit + integration)
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-coverage     # Tests with HTML coverage report
make quick-test        # Fast unit test run
make ci-test          # CI/CD pipeline tests
```

### **Docker Operations**
```bash
make build         # Build both production and test images
make build-prod    # Build production image only
make build-test    # Build test image only
```

### **Application Management**
```bash
make run           # Start bot in background (Docker Compose)
make run-dev       # Start bot in foreground (development mode)
make stop          # Stop the bot
make restart       # Restart the bot
make status        # Check bot health and status
make logs          # Follow live logs
make logs-tail     # View last 100 log lines
```

### **Database Operations**
```bash
make db-debug      # Run database analysis and debug info
make db-shell      # Open SQLite shell for database
make db-backup     # Backup database with timestamp
make db-restore BACKUP_FILE=path/to/backup.db  # Restore from backup
```

### **Maintenance**
```bash
make clean         # Clean Docker containers and images
make clean-all     # Deep clean including volumes
make reset         # Reset everything and rebuild
make version       # Show version and status information
```

### **Deployment**
```bash
make deploy        # Run tests and prepare for deployment
make all          # Complete build and test cycle
```

**Get Help:**
```bash
make help         # Show all available commands with descriptions
```

## 🔧 Development

See [CLAUDE.md](CLAUDE.md) for detailed development instructions and architecture notes.

---

*Stay hydrated and let your hippo friend help you build better water-drinking habits! 🦛💧*
