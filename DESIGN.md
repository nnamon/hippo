# Hippo - Telegram Bot Design Document

## Overview

Hippo is a Telegram bot that reminds you to drink water on a regular interval with a cute cartoon and a poem.

## Core Concept

* Users subscribe to the Telegram Bot, opening a channel that the bot can use to send reminders to drink water on a schedule the user requests.
* The user can edit the schedule. This schedule may be on a regular interval such as every 15 mins or on a regular schedule such as the 18th minute on every hour.
* When a reminder is sent, the user can acknowledge the reminder and confirm that they drank water.
* User configuration and water drinking metrics are persisted server side.
* Reminders include a cute poem and a cartoon image.
* This cartoon image is based on how hydrated the user is based on their water drinking metrics. There are 6 states ranging from dehydrated to fully engorged.
* The cartoon comes in sets of 6 corresponding to the 6 states, the user can choose a theme for the cartoons which selects from cartoon sets.

## Implementation

### Technical Stack
* **Language**: Python 3.9+
* **Bot Framework**: python-telegram-bot with async support and job queue
* **Database**: SQLite for simplicity
* **Deployment**: Docker containers for Digital Ocean droplet

### Content Management
* **Cartoon Images**: 6-state hydration system (0%, 20%, 40%, 60%, 80%, 100%)
* **Image Organization**: Theme-based arrays with placeholder support initially
* **Poems**: Predefined poems for MVP, extensible for future API integration
* **Themes**: Starting with 'default' theme, expandable architecture

### User Experience
* **Reminder Scheduling**: Interval-based (every X minutes) during custom waking hours
* **Hydration Tracking**: Simple acknowledgment buttons with 30-minute expiration
* **Missed Tracking**: Expired reminders count as missed for statistics
* **Onboarding Flow**: Welcome → waking hours setup → start reminders

### MVP Features (Version 1.0)
* User registration and onboarding
* Custom waking hours configuration
* Interval-based water reminders
* Acknowledgment buttons with expiration logic
* 6-level hydration state tracking
* Basic statistics via /stats command
* Placeholder content system

### Future Enhancements
* Multiple cartoon themes
* Advanced scheduling options
* Detailed hydration analytics
* Web interface for configuration
* External poem API integration
