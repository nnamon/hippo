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

* The project should be implemented as a Python project.
