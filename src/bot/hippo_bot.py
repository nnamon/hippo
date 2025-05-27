"""
Hippo Bot - Main bot class for handling Telegram interactions.
"""

import logging
import uuid
import pytz
from datetime import datetime, timedelta, time
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    JobQueue,
)

from src.database.models import DatabaseManager
from src.content.manager import ContentManager
from src.bot.reminder_system import ReminderSystem

logger = logging.getLogger(__name__)


class HippoBot:
    """Main Hippo bot class."""
    
    def __init__(self, token: str):
        """Initialize the bot with the given token."""
        self.token = token
        self.application: Optional[Application] = None
        self.database: Optional[DatabaseManager] = None
        self.content_manager: Optional[ContentManager] = None
        self.job_queue: Optional[JobQueue] = None
        self.reminder_system: Optional[ReminderSystem] = None
        
    def start(self):
        """Start the bot."""
        # Build application
        self.application = Application.builder().token(self.token).build()
        self.job_queue = self.application.job_queue
        
        # Add handlers
        self._add_handlers()
        
        # Start background jobs
        self._schedule_background_jobs()
        
        # Initialize database and other components when the bot starts
        self.application.post_init = self._post_init
        
        # Start the bot with polling (this handles the event loop)
        self.application.run_polling()
    
    async def _post_init(self, application):
        """Initialize components after the application starts."""
        # Initialize database
        self.database = DatabaseManager()
        await self.database.initialize()
        
        # Initialize content manager
        self.content_manager = ContentManager()
        
        # Initialize reminder system
        self.reminder_system = ReminderSystem(self.database, self.content_manager)
        
        # Start reminders for existing users (schedule for after startup)
        self.job_queue.run_once(
            self._start_user_reminders_delayed,
            when=10,  # Start after 10 seconds
            name="start_user_reminders"
        )
        
        # Set bot commands (schedule for after startup)
        self.job_queue.run_once(
            self._set_bot_commands_delayed,
            when=2,  # Set commands after 2 seconds
            name="set_bot_commands"
        )
        
    async def _start_user_reminders_delayed(self, context: ContextTypes.DEFAULT_TYPE):
        """Start reminders for all existing users (called after startup)."""
        await self.reminder_system.start_all_user_reminders(self.job_queue)
    
    async def _set_bot_commands_delayed(self, context: ContextTypes.DEFAULT_TYPE):
        """Set bot commands for slash command completions."""
        try:
            commands = [
                BotCommand("start", "Start the bot and check setup"),
                BotCommand("setup", "Configure reminder preferences"),
                BotCommand("stats", "View your hydration statistics"),
                BotCommand("reset", "Delete all your data and start fresh"),
                BotCommand("help", "Show help and available commands")
            ]
            
            await self.application.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
    
    async def stop(self):
        """Stop the bot (called automatically by run_polling)."""
        if self.reminder_system and self.job_queue:
            self.reminder_system.stop_all_reminders(self.job_queue)
            
        if self.database:
            await self.database.close()
    
    def _add_handlers(self):
        """Add command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("setup", self.setup_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("poem", self.poem_command))
        self.application.add_handler(CommandHandler("reset", self.reset_command))
        
        # Callback query handler for buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler for general messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def _schedule_background_jobs(self):
        """Schedule background jobs for reminder management."""
        # Check for expired reminders every 5 minutes
        self.job_queue.run_repeating(
            self._process_expired_reminders,
            interval=300,  # 5 minutes
            first=10,      # Start after 10 seconds
            name="expired_reminders_check"
        )
    
    async def _process_expired_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Process expired reminders and mark them as missed."""
        try:
            expired_reminders = await self.database.get_expired_reminders()
            
            for reminder in expired_reminders:
                # Edit the message to show it's expired
                await self.reminder_system._mark_reminder_as_expired(
                    context, reminder['chat_id'], reminder['message_id']
                )
                
                # Mark as missed
                await self.database.record_hydration_event(
                    reminder['user_id'], 'missed', reminder['reminder_id']
                )
                
                # Remove from active reminders
                await self.database.remove_active_reminder(reminder['reminder_id'])
                
                logger.info(f"Processed expired reminder {reminder['reminder_id']} for user {reminder['user_id']}")
                
        except Exception as e:
            logger.error(f"Error processing expired reminders: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        # Create or update user in database
        await self.database.create_user(
            user.id, user.username, user.first_name, user.last_name
        )
        
        # Check if user exists and is configured
        user_data = await self.database.get_user(user.id)
        
        welcome_text = f"🦛 Welcome to Hippo, {user.first_name}!\n\n"
        welcome_text += "I'm your friendly water reminder bot. I'll help you stay hydrated with cute cartoons and poems!\n\n"
        
        if user_data and user_data.get('waking_start_hour') is not None:
            welcome_text += "You're all set up! I'll send you reminders during your waking hours.\n\n"
            welcome_text += "Use /help to see all available commands."
        else:
            welcome_text += "Let's get you set up! Please use /setup to configure your reminder preferences."
        
        await update.message.reply_text(welcome_text)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🦛 *Hippo Bot Commands*

/start - Welcome message and setup check
/setup - Configure your reminder preferences
/stats - View your hydration statistics
/poem - Get a random water reminder poem
/reset - Delete all your data and start fresh
/help - Show this help message

I'll send you friendly reminders to drink water with cute cartoons and poems during your waking hours!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def setup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setup command."""
        user_id = update.effective_user.id
        
        # Create setup keyboard
        keyboard = [
            [InlineKeyboardButton("🌍 Set Timezone", callback_data="setup_timezone")],
            [InlineKeyboardButton("🌅 Set Waking Hours", callback_data="setup_waking_hours")],
            [InlineKeyboardButton("⏰ Set Reminder Interval", callback_data="setup_interval")],
            [InlineKeyboardButton("🎨 Choose Theme", callback_data="setup_theme")],
            [InlineKeyboardButton("✅ Finish Setup and View Settings", callback_data="setup_complete")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        setup_text = "🛠️ *Setup Your Hippo Bot*\n\n"
        setup_text += "Let's configure your water reminder preferences:\n\n"
        setup_text += "• **Timezone**: Your local timezone for accurate reminders\n"
        setup_text += "• **Waking Hours**: When you want to receive reminders\n"
        setup_text += "• **Reminder Interval**: How often to remind you\n"
        setup_text += "• **Theme**: Visual style for your reminders\n\n"
        setup_text += "Choose an option below to get started:"
        
        await update.message.reply_text(
            setup_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        user_id = update.effective_user.id
        
        # Get user stats
        stats = await self.database.get_user_hydration_stats(user_id, days=7)
        hydration_level = await self.database.calculate_hydration_level(user_id)
        
        # Calculate percentages
        total_events = stats['confirmed'] + stats['missed']
        if total_events > 0:
            success_rate = (stats['confirmed'] / total_events) * 100
        else:
            success_rate = 0
        
        # Hydration level descriptions
        level_descriptions = [
            "😵 Dehydrated - Drink water now!",
            "😟 Low hydration - Need more water",
            "😐 Moderate hydration - Doing okay", 
            "😊 Good hydration - Keep it up!",
            "😄 Great hydration - Excellent work!",
            "🤩 Perfect hydration - You're amazing!"
        ]
        
        stats_text = f"📊 *Your Hydration Stats (Last 7 Days)*\n\n"
        stats_text += f"💧 Water confirmations: {stats['confirmed']}\n"
        stats_text += f"❌ Missed reminders: {stats['missed']}\n"
        stats_text += f"📈 Success rate: {success_rate:.1f}%\n\n"
        stats_text += f"Current hydration level:\n{level_descriptions[hydration_level]}"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def poem_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /poem command."""
        try:
            # Check if content manager is initialized
            if not self.content_manager:
                logger.error("Content manager not initialized")
                await update.message.reply_text(
                    "❌ Bot is still starting up. Please try again in a moment!"
                )
                return
            
            user_id = update.effective_user.id
            
            # Get user's current hydration level and theme
            hydration_level = await self.database.calculate_hydration_level(user_id)
            user = await self.database.get_user(user_id)
            theme = user.get('theme', 'bluey') if user else 'bluey'
            
            # Get a random poem from the content manager (async version for better performance)
            poem = await self.content_manager.get_random_poem_async()
            
            # Get the appropriate image for the current hydration level
            image_path = self.content_manager.get_image_for_hydration_level(hydration_level, theme)
            
            # Hydration level descriptions
            level_descriptions = [
                "😵 Dehydrated - Drink water now!",
                "😟 Low hydration - Need more water", 
                "😐 Moderate hydration - Doing okay",
                "🙂 Good hydration - Keep it up!",
                "😊 Great hydration - Well done!",
                "🤩 Fully hydrated - Amazing!"
            ]
            
            # Format the response with hydration status
            poem_text = f"🎭 *Here's a water reminder poem for you:*\n\n{poem}\n\n"
            poem_text += f"💧 *Current Hydration:* {level_descriptions[hydration_level]}\n\n"
            poem_text += "Remember to stay hydrated! 🦛"
            
            # Send the image with the poem
            with open(f"assets/{image_path}", 'rb') as image_file:
                await update.message.reply_photo(
                    photo=image_file,
                    caption=poem_text,
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            logger.error(f"Error handling poem command: {e}")
            await update.message.reply_text(
                "❌ Sorry, I couldn't fetch a poem right now. Please try again later!"
            )
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reset command with confirmation."""
        user_id = update.effective_user.id
        
        # Create confirmation keyboard
        keyboard = [
            [InlineKeyboardButton("⚠️ Yes, Delete Everything", callback_data="reset_confirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="reset_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        reset_text = "⚠️ *Reset Your Hippo Bot Session*\n\n"
        reset_text += "This will **permanently delete**:\n"
        reset_text += "• All your settings and preferences\n"
        reset_text += "• Your hydration history and statistics\n"
        reset_text += "• All active reminders\n"
        reset_text += "• Your user account\n\n"
        reset_text += "You'll need to run `/start` again to use the bot.\n\n"
        reset_text += "⚠️ **This action cannot be undone!**\n\n"
        reset_text += "Are you sure you want to proceed?"
        
        await update.message.reply_text(
            reset_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("confirm_water_"):
            await self._handle_water_confirmation(query)
        elif query.data == "expired_reminder":
            await query.answer("This reminder has expired. A new one will be sent soon!", show_alert=True)
        elif query.data == "reset_confirm":
            await self._handle_reset_confirm(query)
        elif query.data == "reset_cancel":
            await self._handle_reset_cancel(query)
        elif query.data.startswith("setup_"):
            await self._handle_setup_callback(query)
        elif query.data.startswith("waking_"):
            await self._handle_waking_hours_selection(query)
        elif query.data.startswith("interval_"):
            await self._handle_interval_selection(query)
        elif query.data.startswith("timezone_"):
            await self._handle_timezone_selection(query)
        elif query.data.startswith("theme_"):
            await self._handle_theme_selection(query)
        else:
            await query.edit_message_text("Unknown button action")
    
    async def _handle_water_confirmation(self, query):
        """Handle water drinking confirmation."""
        try:
            # Extract reminder ID from callback data
            reminder_id = query.data.replace("confirm_water_", "")
            user_id = query.from_user.id
            
            # Record the confirmation
            await self.database.record_hydration_event(user_id, 'confirmed', reminder_id)
            
            # Remove from active reminders
            await self.database.remove_active_reminder(reminder_id)
            
            # Get updated hydration level and stats
            hydration_level = await self.database.calculate_hydration_level(user_id)
            daily_stats = await self.database.get_user_hydration_stats(user_id, days=1)
            
            # Calculate daily progress
            total_today = daily_stats['confirmed'] + daily_stats['missed']
            success_rate = (daily_stats['confirmed'] / total_today * 100) if total_today > 0 else 0
            
            # Hydration level descriptions with emojis
            level_descriptions = [
                "😵 Dehydrated",
                "😟 Low hydration", 
                "😐 Moderate hydration",
                "😊 Good hydration",
                "😄 Great hydration",
                "🤩 Perfect hydration"
            ]
            
            # Get appropriate response message and a celebratory poem
            confirmation_message = self.content_manager.get_confirmation_message(hydration_level)
            celebration_poem = self.content_manager.get_random_poem()
            
            # Build enhanced confirmation message with updated stats
            response_text = f"✅ **Great!** {confirmation_message}\n\n"
            response_text += f"📊 **Updated Status:**\n"
            response_text += f"• Current level: {level_descriptions[hydration_level]}\n"
            response_text += f"• Today: {daily_stats['confirmed']}✅ {daily_stats['missed']}❌"
            if total_today > 0:
                response_text += f" ({success_rate:.0f}%)"
            response_text += "\n\n"
            
            # Add level-specific encouragement
            if hydration_level >= 4:
                response_text += "🌟 You're doing amazing! Keep up this fantastic hydration routine!\n\n"
            elif hydration_level >= 2:
                response_text += "💪 Great progress! You're building excellent habits!\n\n"
            else:
                response_text += "🌱 Every sip counts! You're on the right track!\n\n"
            
            # Add a celebratory poem
            response_text += f"🎉 **Here's a little celebration poem for you:**\n\n{celebration_poem}"
            
            # Try to edit the message (could be photo with caption or text message)
            try:
                # First try editing as photo caption
                await query.edit_message_caption(
                    caption=response_text,
                    parse_mode='Markdown'
                )
            except Exception:
                # If that fails, try editing as text message
                await query.edit_message_text(
                    response_text,
                    parse_mode='Markdown'
                )
            
            logger.info(f"User {user_id} confirmed water drinking for reminder {reminder_id} - new level: {hydration_level}")
            
        except Exception as e:
            logger.error(f"Error handling water confirmation: {e}")
            try:
                await query.edit_message_caption(caption="❌ Sorry, there was an error processing your confirmation.")
            except Exception:
                try:
                    await query.edit_message_text("❌ Sorry, there was an error processing your confirmation.")
                except Exception:
                    # If all else fails, send a new message
                    await query.message.reply_text("❌ Sorry, there was an error processing your confirmation.")
    
    async def _handle_setup_callback(self, query):
        """Handle setup-related callback queries."""
        action = query.data.replace("setup_", "")
        
        if action == "timezone":
            await self._setup_timezone(query)
        elif action == "waking_hours":
            await self._setup_waking_hours(query)
        elif action == "interval":
            await self._setup_interval(query)
        elif action == "theme":
            await self._setup_theme(query)
        elif action == "complete":
            await self._complete_setup(query)
        elif action == "back":
            # Return to main setup menu
            keyboard = [
                [InlineKeyboardButton("🌍 Set Timezone", callback_data="setup_timezone")],
                [InlineKeyboardButton("🌅 Set Waking Hours", callback_data="setup_waking_hours")],
                [InlineKeyboardButton("⏰ Set Reminder Interval", callback_data="setup_interval")],
                [InlineKeyboardButton("🎨 Choose Theme", callback_data="setup_theme")],
                [InlineKeyboardButton("✅ Finish Setup and View Settings", callback_data="setup_complete")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            setup_text = "🛠️ *Setup Your Hippo Bot*\n\n"
            setup_text += "Let's configure your water reminder preferences:\n\n"
            setup_text += "• **Timezone**: Your local timezone for accurate reminders\n"
            setup_text += "• **Waking Hours**: When you want to receive reminders\n"
            setup_text += "• **Reminder Interval**: How often to remind you\n"
            setup_text += "• **Theme**: Visual style for your reminders\n\n"
            setup_text += "Choose an option below to get started:"
            
            await query.edit_message_text(
                setup_text, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text("Unknown setup option")
    
    async def _setup_timezone(self, query):
        """Handle timezone setup."""
        keyboard = [
            [InlineKeyboardButton("🇸🇬 Singapore (UTC+8)", callback_data="timezone_Asia/Singapore")],
            [InlineKeyboardButton("🇺🇸 US Eastern (UTC-5)", callback_data="timezone_America/New_York")],
            [InlineKeyboardButton("🇺🇸 US Pacific (UTC-8)", callback_data="timezone_America/Los_Angeles")],
            [InlineKeyboardButton("🇬🇧 UK/London (UTC+0)", callback_data="timezone_Europe/London")],
            [InlineKeyboardButton("🇯🇵 Japan/Tokyo (UTC+9)", callback_data="timezone_Asia/Tokyo")],
            [InlineKeyboardButton("🇦🇺 Australia/Sydney (UTC+11)", callback_data="timezone_Australia/Sydney")],
            [InlineKeyboardButton("⬅️ Back to Setup", callback_data="setup_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🌍 *Choose Your Timezone*\n\n"
        text += "Select your timezone for accurate reminder scheduling:\n\n"
        text += "Current default is Singapore (UTC+8)"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _setup_theme(self, query):
        """Handle theme setup."""
        keyboard = [
            [InlineKeyboardButton("💙 Bluey (Default)", callback_data="theme_bluey")],
            [InlineKeyboardButton("🏜️ Desert", callback_data="theme_desert")],
            [InlineKeyboardButton("🌸 Spring", callback_data="theme_spring")],
            [InlineKeyboardButton("🌈 Vivid", callback_data="theme_vivid")],
            [InlineKeyboardButton("⬅️ Back to Setup", callback_data="setup_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🎨 *Choose Your Theme*\n\n"
        text += "Select a visual theme for your water reminders:\n\n"
        text += "• **Bluey**: Cool blue tones (default)\n"
        text += "• **Desert**: Warm sandy colors\n"
        text += "• **Spring**: Fresh green nature\n"
        text += "• **Vivid**: Bright and colorful\n\n"
        text += "Each theme shows different cartoon styles!"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _setup_waking_hours(self, query):
        """Handle waking hours setup."""
        keyboard = [
            [InlineKeyboardButton("🌅 Early Bird (6 AM - 9 PM)", callback_data="waking_6_21")],
            [InlineKeyboardButton("☀️ Regular (7 AM - 10 PM)", callback_data="waking_7_22")], 
            [InlineKeyboardButton("🌙 Night Owl (9 AM - 12 AM)", callback_data="waking_9_24")],
            [InlineKeyboardButton("🔄 24/7 Testing Mode", callback_data="waking_0_24")],
            [InlineKeyboardButton("🔧 Custom Hours", callback_data="waking_custom")],
            [InlineKeyboardButton("⬅️ Back to Setup", callback_data="setup_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🌅 *Choose Your Waking Hours*\n\n"
        text += "When would you like to receive water reminders?\n\n"
        text += "Select a preset or choose custom hours:"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _setup_interval(self, query):
        """Handle reminder interval setup."""
        keyboard = [
            [InlineKeyboardButton("⏰ Every 1 minute (testing)", callback_data="interval_1")],
            [InlineKeyboardButton("⏰ Every 15 minutes", callback_data="interval_15")],
            [InlineKeyboardButton("⏰ Every 30 minutes", callback_data="interval_30")],
            [InlineKeyboardButton("⏰ Every hour", callback_data="interval_60")],
            [InlineKeyboardButton("⏰ Every 2 hours", callback_data="interval_120")],
            [InlineKeyboardButton("⬅️ Back to Setup", callback_data="setup_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "⏰ *Choose Reminder Frequency*\n\n"
        text += "How often would you like to be reminded to drink water?\n\n"
        text += "More frequent reminders help build better habits:"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _calculate_next_reminder_time(self, user_data):
        """Calculate when the next reminder will be sent."""
        try:
            
            # Get user's timezone
            user_tz_str = user_data.get('timezone', 'Asia/Singapore')
            user_tz = pytz.timezone(user_tz_str)
            
            # Get current time in user's timezone
            now_utc = datetime.now(pytz.UTC)
            now_local = now_utc.astimezone(user_tz)
            
            # Add the reminder interval to current time
            interval_minutes = user_data['reminder_interval_minutes']
            next_time = now_local + timedelta(minutes=interval_minutes)
            
            # Check if next time is within waking hours
            start_hour = user_data['waking_start_hour']
            end_hour = user_data['waking_end_hour']
            start_minute = user_data['waking_start_minute']
            end_minute = user_data['waking_end_minute']
            
            # If 24/7 mode, next reminder is simply current time + interval
            if start_hour == 0 and end_hour == 23:
                minutes_until = interval_minutes
                if minutes_until < 60:
                    return f"in {minutes_until} minute{'s' if minutes_until != 1 else ''} ({next_time.strftime('%I:%M %p')})"
                else:
                    hours = minutes_until // 60
                    mins = minutes_until % 60
                    if mins == 0:
                        return f"in {hours} hour{'s' if hours != 1 else ''} ({next_time.strftime('%I:%M %p')})"
                    else:
                        return f"in {hours}h {mins}m ({next_time.strftime('%I:%M %p')})"
            
            # Check if next time falls within waking hours
            start_time = time(start_hour, start_minute)
            end_time = time(end_hour, end_minute)
            next_time_only = next_time.time()
            
            # Handle normal waking hours (e.g., 7:00 - 22:00)
            if start_time <= end_time:
                if start_time <= next_time_only <= end_time:
                    # Next reminder is within today's waking hours
                    minutes_until = interval_minutes
                    if minutes_until < 60:
                        return f"in {minutes_until} minute{'s' if minutes_until != 1 else ''} ({next_time.strftime('%I:%M %p')})"
                    else:
                        hours = minutes_until // 60
                        mins = minutes_until % 60
                        if mins == 0:
                            return f"in {hours} hour{'s' if hours != 1 else ''} ({next_time.strftime('%I:%M %p')})"
                        else:
                            return f"in {hours}h {mins}m ({next_time.strftime('%I:%M %p')})"
                elif next_time_only > end_time:
                    # Next reminder would be past bedtime, schedule for tomorrow morning
                    tomorrow = next_time.date() + timedelta(days=1)
                    next_reminder = user_tz.localize(datetime.combine(tomorrow, start_time))
                    return f"tomorrow at {next_reminder.strftime('%I:%M %p')} (when you wake up)"
                else:
                    # Next reminder is before waking hours today
                    today = next_time.date()
                    next_reminder = user_tz.localize(datetime.combine(today, start_time))
                    return f"at {next_reminder.strftime('%I:%M %p')} (when you wake up)"
            else:
                # Handle overnight waking hours (e.g., 22:00 - 06:00)
                if next_time_only >= start_time or next_time_only <= end_time:
                    # Within overnight waking hours
                    minutes_until = interval_minutes
                    if minutes_until < 60:
                        return f"in {minutes_until} minute{'s' if minutes_until != 1 else ''} ({next_time.strftime('%I:%M %p')})"
                    else:
                        hours = minutes_until // 60
                        mins = minutes_until % 60
                        if mins == 0:
                            return f"in {hours} hour{'s' if hours != 1 else ''} ({next_time.strftime('%I:%M %p')})"
                        else:
                            return f"in {hours}h {mins}m ({next_time.strftime('%I:%M %p')})"
                else:
                    # Outside waking hours, schedule for next waking period
                    if next_time_only > end_time and next_time_only < start_time:
                        # Between end and start time, wait until start time today
                        today = next_time.date()
                        next_reminder = user_tz.localize(datetime.combine(today, start_time))
                        return f"at {next_reminder.strftime('%I:%M %p')} (when you wake up)"
                    
            return f"in {interval_minutes} minute{'s' if interval_minutes != 1 else ''} ({next_time.strftime('%I:%M %p')})"
            
        except Exception as e:
            logger.error(f"Error calculating next reminder time: {e}")
            return None

    async def _complete_setup(self, query):
        """Complete the setup process."""
        user_id = query.from_user.id
        user_data = await self.database.get_user(user_id)
        
        if not user_data:
            await query.edit_message_text("❌ Setup error. Please try /start again.")
            return
        
        completion_text = "🎉 *Setup Complete!*\n\n"
        completion_text += f"**Your Settings:**\n"
        
        # Format waking hours display
        if user_data['waking_start_hour'] == 0 and user_data['waking_end_hour'] == 23:
            waking_display = "24/7 (Testing Mode)"
        else:
            waking_display = f"{user_data['waking_start_hour']:02d}:{user_data['waking_start_minute']:02d} - {user_data['waking_end_hour']:02d}:{user_data['waking_end_minute']:02d}"
        
        completion_text += f"• Timezone: {user_data.get('timezone', 'Asia/Singapore')}\n"
        completion_text += f"• Waking Hours: {waking_display}\n"
        completion_text += f"• Reminder Interval: {user_data['reminder_interval_minutes']} minutes\n"
        # Get display name for theme
        theme_names = {
            "bluey": "Bluey (Cool Blue)",
            "desert": "Desert (Warm Sandy)",
            "spring": "Spring (Fresh Green)",
            "vivid": "Vivid (Bright & Colorful)"
        }
        theme_display = theme_names.get(user_data['theme'], user_data['theme'].title())
        completion_text += f"• Theme: {theme_display}\n\n"
        
        # Calculate next reminder time
        next_reminder_time = await self._calculate_next_reminder_time(user_data)
        if next_reminder_time:
            completion_text += f"⏰ **Next reminder:** {next_reminder_time}\n\n"
        
        completion_text += "I'll start sending you water reminders during your waking hours! 🦛💧\n\n"
        completion_text += "Use /help to see all available commands."
        
        await query.edit_message_text(completion_text, parse_mode='Markdown')
        
        # Start reminders for this user
        await self.reminder_system.start_reminders_for_user(self.job_queue, user_id)
    
    async def _handle_waking_hours_selection(self, query):
        """Handle waking hours selection."""
        user_id = query.from_user.id
        selection = query.data.replace("waking_", "")
        
        if selection == "custom":
            await query.edit_message_text(
                "🔧 Custom hours setup coming soon!\n\n"
                "For now, please choose one of the preset options.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="setup_waking_hours")
                ]])
            )
            return
        elif selection == "back":
            # Return to main setup menu
            keyboard = [
                [InlineKeyboardButton("🌅 Set Waking Hours", callback_data="setup_waking_hours")],
                [InlineKeyboardButton("⏰ Set Reminder Interval", callback_data="setup_interval")],
                [InlineKeyboardButton("🎨 Choose Theme", callback_data="setup_theme")],
                [InlineKeyboardButton("✅ Finish Setup and View Settings", callback_data="setup_complete")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            setup_text = "🛠️ *Setup Your Hippo Bot*\n\n"
            setup_text += "Let's configure your water reminder preferences:\n\n"
            setup_text += "• **Waking Hours**: When you want to receive reminders\n"
            setup_text += "• **Reminder Interval**: How often to remind you\n"
            setup_text += "• **Theme**: Visual style for your reminders\n\n"
            setup_text += "Choose an option below to get started:"
            
            await query.edit_message_text(
                setup_text, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        # Parse preset hours (format: start_end)
        try:
            start_hour, end_hour = map(int, selection.split("_"))
            # Handle 24-hour format for 24/7 mode
            if start_hour == 0 and end_hour == 24:
                # 24/7 mode: set to 0-23 (all day)
                start_hour, end_hour = 0, 23
            elif end_hour == 24:
                end_hour = 0
                
            success = await self.database.update_user_waking_hours(
                user_id, start_hour, 0, end_hour, 0
            )
            
            if success:
                if start_hour == 0 and end_hour == 23:
                    time_display = "24/7 (Testing Mode)"
                else:
                    time_display = f"{start_hour:02d}:00 - {end_hour:02d}:00"
                
                await query.edit_message_text(
                    f"✅ Waking hours set to {time_display}\n\n"
                    "Now let's set your reminder frequency!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⏰ Set Reminder Interval", callback_data="setup_interval")
                    ]])
                )
            else:
                await query.edit_message_text("❌ Error saving waking hours. Please try again.")
                
        except Exception as e:
            logger.error(f"Error setting waking hours: {e}")
            await query.edit_message_text("❌ Error setting waking hours. Please try again.")
    
    async def _handle_interval_selection(self, query):
        """Handle reminder interval selection."""
        user_id = query.from_user.id
        interval_str = query.data.replace("interval_", "")
        
        try:
            interval_minutes = int(interval_str)
            
            success = await self.database.update_user_reminder_interval(user_id, interval_minutes)
            
            if success:
                if interval_minutes == 1:
                    interval_text = "1 minute (testing mode)"
                elif interval_minutes < 60:
                    interval_text = f"{interval_minutes} minutes"
                else:
                    hours = interval_minutes // 60
                    interval_text = f"{hours} hour{'s' if hours > 1 else ''}"
                
                await query.edit_message_text(
                    f"✅ Reminder interval set to every {interval_text}!\n\n"
                    "Your setup is almost complete!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Finish Setup", callback_data="setup_complete")
                    ]])
                )
            else:
                await query.edit_message_text("❌ Error saving reminder interval. Please try again.")
                
        except Exception as e:
            logger.error(f"Error setting reminder interval: {e}")
            await query.edit_message_text("❌ Error setting reminder interval. Please try again.")
    
    async def _handle_timezone_selection(self, query):
        """Handle timezone selection."""
        user_id = query.from_user.id
        timezone_str = query.data.replace("timezone_", "")
        
        try:
            success = await self.database.update_user_timezone(user_id, timezone_str)
            
            if success:
                # Get display name for timezone
                timezone_names = {
                    "Asia/Singapore": "Singapore (UTC+8)",
                    "America/New_York": "US Eastern",
                    "America/Los_Angeles": "US Pacific", 
                    "Europe/London": "UK/London",
                    "Asia/Tokyo": "Japan/Tokyo",
                    "Australia/Sydney": "Australia/Sydney"
                }
                display_name = timezone_names.get(timezone_str, timezone_str)
                
                await query.edit_message_text(
                    f"✅ Timezone set to {display_name}!\n\n"
                    "Now let's set your waking hours!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🌅 Set Waking Hours", callback_data="setup_waking_hours")
                    ]])
                )
            else:
                await query.edit_message_text("❌ Error saving timezone. Please try again.")
                
        except Exception as e:
            logger.error(f"Error setting timezone: {e}")
            await query.edit_message_text("❌ Error setting timezone. Please try again.")
    
    async def _handle_theme_selection(self, query):
        """Handle theme selection."""
        user_id = query.from_user.id
        theme_str = query.data.replace("theme_", "")
        
        try:
            # Validate theme exists
            available_themes = self.content_manager.get_available_themes()
            if theme_str not in available_themes:
                await query.edit_message_text("❌ Invalid theme selected. Please try again.")
                return
            
            success = await self.database.update_user_theme(user_id, theme_str)
            
            if success:
                # Get display name for theme
                theme_names = {
                    "bluey": "Bluey (Cool Blue)",
                    "desert": "Desert (Warm Sandy)",
                    "spring": "Spring (Fresh Green)",
                    "vivid": "Vivid (Bright & Colorful)"
                }
                display_name = theme_names.get(theme_str, theme_str.title())
                
                await query.edit_message_text(
                    f"✅ Theme set to {display_name}!\n\n"
                    "Your reminders will now use this visual style!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Finish Setup", callback_data="setup_complete")
                    ]])
                )
            else:
                await query.edit_message_text("❌ Error saving theme. Please try again.")
                
        except Exception as e:
            logger.error(f"Error setting theme: {e}")
            await query.edit_message_text("❌ Error setting theme. Please try again.")
    
    async def _handle_reset_confirm(self, query):
        """Handle reset confirmation."""
        user_id = query.from_user.id
        
        try:
            # Cancel any active reminders for this user first
            self.reminder_system.cancel_user_reminders(self.job_queue, user_id)
            
            # Delete user and all their data
            success = await self.database.delete_user_completely(user_id)
            
            if success:
                await query.edit_message_text(
                    "✅ *Reset Complete!*\n\n"
                    "Your Hippo Bot session has been completely deleted.\n\n"
                    "• All settings and preferences removed\n"
                    "• Hydration history cleared\n"
                    "• Reminders stopped\n\n"
                    "Run `/start` to begin fresh! 🦛",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "❌ *Reset Failed*\n\n"
                    "There was an error deleting your data. Please try again or contact support.",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error resetting user {user_id}: {e}")
            await query.edit_message_text(
                "❌ *Reset Failed*\n\n"
                "An unexpected error occurred. Please try again.",
                parse_mode='Markdown'
            )
    
    async def _handle_reset_cancel(self, query):
        """Handle reset cancellation."""
        await query.edit_message_text(
            "❌ *Reset Cancelled*\n\n"
            "Your data is safe! Nothing has been deleted.\n\n"
            "Use `/help` to see what else I can do for you! 🦛"
        )
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        await update.message.reply_text(
            "I'm here to help you stay hydrated! 🦛💧\n\n"
            "Use /help to see what I can do for you."
        )