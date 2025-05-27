# Hippo - Telegram Bot Design Document

## Overview

Hippo is a Telegram bot that helps you stay hydrated by sending friendly water reminders with cute themed cartoons and poems. It features reactive hydration tracking, multiple cartoon themes, and intelligent reminder management.

## Core Concept

* **Smart Reminders**: Users receive water reminders with themed cartoons, poems, and real-time hydration stats
* **Reactive Tracking**: Hydration levels update based on the last 6 reminders for immediate feedback
* **Theme Selection**: 4 cartoon themes (bluey, desert, spring, vivid) with 6 hydration states each
* **Timezone Support**: Accurate local time handling for global users
* **Auto-Expiration**: Previous reminders automatically expire when new ones arrive
* **Comprehensive Stats**: Daily progress and rolling averages displayed in each reminder

## Implementation ✅ COMPLETED

### Technical Stack
* **Language**: Python 3.11 with async/await architecture
* **Bot Framework**: python-telegram-bot v20.7 with job queue
* **Database**: SQLite with aiosqlite for async operations
* **Timezone**: pytz for accurate local time handling
* **Deployment**: Docker containers with docker-compose
* **Dependencies**: Minimal set (no PIL/Pillow needed)

### Content Management ✅ IMPLEMENTED
* **Cartoon Themes**: 4 complete themes with 6 hydration states each
  - bluey/ (cool blue tones - default)
  - desert/ (warm sandy colors)
  - spring/ (fresh green nature)
  - vivid/ (bright and colorful)
* **Image Mapping**: tile_0_0 → tile_1_2 mapped to hydration levels 0-5
* **Poems**: 20 unique water-themed poems with anti-repetition logic
* **Smart Selection**: Recent poem tracking prevents immediate repeats

### User Experience ✅ ENHANCED
* **Guided Setup**: Comprehensive onboarding with timezone, waking hours, intervals, themes
* **Rich Reminders**: Each reminder includes:
  - Themed cartoon reflecting current hydration level
  - Unique poem with variety
  - Current hydration status (😵 to 🤩)
  - Daily progress stats (3✅ 1❌ 75%)
* **Visual Feedback**: Expired reminders show "⏰ Expired - Missed this reminder"
* **Reset Option**: Complete data wipe with `/reset` command
* **Slash Commands**: Auto-completion support for better UX

### Hydration Tracking ✅ REACTIVE SYSTEM
* **6 Hydration Levels**: Based on rolling average of last 6 reminders
  - Level 0: 😵 Dehydrated (0/6 confirmed)
  - Level 1: 😟 Low hydration (1/6 confirmed) 
  - Level 2: 😐 Moderate hydration (2/6 confirmed)
  - Level 3: 😊 Good hydration (3/6 confirmed)
  - Level 4: 😄 Great hydration (4+/6 confirmed)
  - Level 5: 🤩 Perfect hydration (5-6/6 confirmed)
* **Immediate Feedback**: Miss reminders → level drops quickly
* **Quick Recovery**: Confirm reminders → level improves fast

### Database Schema ✅ COMPLETE
```sql
users: user_id, settings, timezone(Asia/Singapore), theme(bluey)
hydration_events: user_id, event_type(confirmed/missed), reminder_id, timestamp
active_reminders: user_id, reminder_id, message_id, chat_id, expires_at
```

### Commands ✅ FULL FEATURE SET
* `/start` - Welcome and setup check
* `/setup` - Configure timezone, waking hours, intervals, themes
* `/stats` - Comprehensive hydration statistics
* `/reset` - Complete data wipe with confirmation
* `/help` - Command reference

### Key Features Delivered
* ✅ **4 Cartoon Themes** with user selection
* ✅ **Reactive Hydration Levels** (6-reminder rolling average)
* ✅ **Enhanced Reminders** with stats and status
* ✅ **Timezone Support** with global compatibility
* ✅ **Smart Content** with 20 unique poems
* ✅ **Visual Expiration** feedback for missed reminders
* ✅ **Complete Reset** functionality
* ✅ **Slash Command** completions
* ✅ **Auto-Expiration** of old reminders
* ✅ **Persistent Settings** across sessions

## Architecture

### Modular Design
* `src/bot/` - Telegram bot handlers and UI logic
* `src/database/` - SQLite models and data operations
* `src/content/` - Poem and theme management
* `assets/` - Organized theme folders with cartoon images

### Async Architecture
* Non-blocking database operations with aiosqlite
* Job queue for scheduled reminders
* Proper cleanup and resource management

### Docker Deployment
* Single-container deployment with docker-compose
* Volume persistence for database
* Asset bundling for theme images

---

**Status**: 🎉 **PRODUCTION READY** - Full feature set implemented and tested
