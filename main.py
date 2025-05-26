#!/usr/bin/env python3
"""
Hippo - Telegram Water Reminder Bot
Main entry point for the application.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.bot.hippo_bot import HippoBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    # Load environment variables
    config_path = Path(__file__).parent / "config.env"
    if not config_path.exists():
        logger.error("config.env file not found. Please copy config.env.example to config.env and configure it.")
        sys.exit(1)
    
    load_dotenv(config_path)
    
    # Get required configuration
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in config.env")
        sys.exit(1)
    
    # Initialize and start the bot
    bot = HippoBot(bot_token)
    
    try:
        logger.info("Starting Hippo bot...")
        bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()