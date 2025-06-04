"""
Hippo Bot - Main bot class for handling Telegram interactions.
"""

import logging
import uuid
import pytz
from datetime import datetime, timedelta, time
from typing import Optional
from pathlib import Path

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
from src.content.charts import ChartGenerator
from src.bot.reminder_system import ReminderSystem
from src.bot.achievements import AchievementChecker, ACHIEVEMENTS

logger = logging.getLogger(__name__)

# Fun hippo name suggestions
HIPPO_NAME_SUGGESTIONS = [
    "Splashy", "Bubbles", "River", "Aqua", "Hydro", "Tsunami",
    "Splash", "Ripple", "Puddle", "Drops", "Ocean", "Brook",
    "Crystal", "Misty", "Rain", "Storm", "Blue", "Wave",
    "Fluid", "Gush", "Spring", "Flow", "Dew", "Cascade"
]


class HippoBot:
    """Main Hippo bot class."""
    
    def __init__(self, token: str):
        """Initialize the bot with the given token."""
        self.token = token
        self.application: Optional[Application] = None
        self.database: Optional[DatabaseManager] = None
        self.content_manager: Optional[ContentManager] = None
        self.chart_generator: Optional[ChartGenerator] = None
        self.job_queue: Optional[JobQueue] = None
        self.reminder_system: Optional[ReminderSystem] = None
        self.achievement_checker: Optional[AchievementChecker] = None
        
    def start(self):  # pragma: no cover
        """Start the bot."""
        # Build application
        self.application = Application.builder().token(self.token).build()  # pragma: no cover
        self.job_queue = self.application.job_queue  # pragma: no cover
        
        # Add handlers
        self._add_handlers()
        
        # Start background jobs
        self._schedule_background_jobs()  # pragma: no cover
        
        # Initialize database and other components when the bot starts
        self.application.post_init = self._post_init  # pragma: no cover
        
        # Start the bot with polling (this handles the event loop)
        self.application.run_polling()  # pragma: no cover
    
    async def _post_init(self, application):  # pragma: no cover
        """Initialize components after the application starts."""
        # Initialize database with path from environment or default
        import os  # pragma: no cover
        db_path = os.getenv('DATABASE_PATH', 'hippo.db')  # pragma: no cover
        self.database = DatabaseManager(db_path)  # pragma: no cover
        await self.database.initialize()  # pragma: no cover
        
        # Initialize content manager
        self.content_manager = ContentManager()  # pragma: no cover
        
        # Initialize chart generator
        self.chart_generator = ChartGenerator()  # pragma: no cover
        
        # Initialize reminder system
        self.reminder_system = ReminderSystem(self.database, self.content_manager)  # pragma: no cover
        
        # Initialize achievement checker
        self.achievement_checker = AchievementChecker(self.database)  # pragma: no cover
        
        # Start reminders for existing users (schedule for after startup)
        self.job_queue.run_once(  # pragma: no cover
            self._start_user_reminders_delayed,
            when=10,  # Start after 10 seconds
            name="start_user_reminders"
        )
        
        # Set bot commands (schedule for after startup)
        self.job_queue.run_once(  # pragma: no cover
            self._set_bot_commands_delayed,
            when=2,  # Set commands after 2 seconds
            name="set_bot_commands"
        )
        
    async def _start_user_reminders_delayed(self, context: ContextTypes.DEFAULT_TYPE):  # pragma: no cover
        """Start reminders for all existing users (called after startup)."""
        await self.reminder_system.start_all_user_reminders(self.job_queue)  # pragma: no cover
    
    async def _set_bot_commands_delayed(self, context: ContextTypes.DEFAULT_TYPE):  # pragma: no cover
        """Set bot commands for slash command completions."""
        try:  # pragma: no cover
            commands = [  # pragma: no cover
                BotCommand("start", "Start the bot and check setup"),
                BotCommand("setup", "Configure reminder preferences"),
                BotCommand("stats", "View your hydration statistics"),
                BotCommand("achievements", "View your achievements"),
                BotCommand("charts", "View hydration charts and progress visualizations"),
                BotCommand("poem", "Get a random water reminder poem"),
                BotCommand("quote", "Get a random inspirational quote"),
                BotCommand("hipponame", "Change your hippo's name"),
                BotCommand("reset", "Delete all your data and start fresh"),
                BotCommand("help", "Show help and available commands")
            ]
            
            await self.application.bot.set_my_commands(commands)  # pragma: no cover
            logger.info("Bot commands set successfully")  # pragma: no cover
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to set bot commands: {e}")  # pragma: no cover
    
    async def stop(self):  # pragma: no cover
        """Stop the bot (called automatically by run_polling)."""
        if self.reminder_system and self.job_queue:  # pragma: no cover
            self.reminder_system.stop_all_reminders(self.job_queue)  # pragma: no cover
            
        if self.database:  # pragma: no cover
            await self.database.close()  # pragma: no cover
    
    def _add_handlers(self):
        """Add command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("setup", self.setup_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("achievements", self.achievements_command))
        self.application.add_handler(CommandHandler("charts", self.charts_command))
        self.application.add_handler(CommandHandler("poem", self.poem_command))
        self.application.add_handler(CommandHandler("quote", self.quote_command))
        self.application.add_handler(CommandHandler("hipponame", self.hipponame_command))
        self.application.add_handler(CommandHandler("reset", self.reset_command))
        
        # Callback query handler for buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler for general messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def _schedule_background_jobs(self):  # pragma: no cover
        """Schedule background jobs for reminder management."""
        # Check for expired reminders every 5 minutes
        self.job_queue.run_repeating(  # pragma: no cover
            self._process_expired_reminders,
            interval=300,  # 5 minutes
            first=10,      # Start after 10 seconds
            name="expired_reminders_check"
        )
    
    async def _process_expired_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Process expired reminders and mark them as missed."""
        try:  # pragma: no cover
            expired_reminders = await self.database.get_expired_reminders()  # pragma: no cover
            
            for reminder in expired_reminders:  # pragma: no cover
                # Edit the message to show it's expired
                await self.reminder_system._mark_reminder_as_expired(  # pragma: no cover
                    context, reminder['chat_id'], reminder['message_id']
                )
                
                # Mark as missed
                await self.database.record_hydration_event(  # pragma: no cover
                    reminder['user_id'], 'missed', reminder['reminder_id']
                )
                
                # Remove from active reminders
                await self.database.remove_active_reminder(reminder['reminder_id'])  # pragma: no cover
                
                logger.info(f"Processed expired reminder {reminder['reminder_id']} for user {reminder['user_id']}")  # pragma: no cover
                
        except Exception as e:  # pragma: no cover
            logger.error(f"Error processing expired reminders: {e}")  # pragma: no cover
    
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
/achievements - View your achievements and progress
/poem - Get a random water reminder poem
/quote - Get a random inspirational quote
/hipponame - Change your hippo's name
/reset - Delete all your data and start fresh
/help - Show this help message

I'll send you friendly reminders to drink water with cute cartoons, poems, and inspirational quotes during your waking hours!
        """
        await update.message.reply_text(help_text)
    
    async def setup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setup command."""
        user_id = update.effective_user.id
        
        # Create setup keyboard
        keyboard = [
            [InlineKeyboardButton("🦛 Name Your Hippo", callback_data="setup_hippo_name")],
            [InlineKeyboardButton("🌍 Set Timezone", callback_data="setup_timezone")],
            [InlineKeyboardButton("🌅 Set Waking Hours", callback_data="setup_waking_hours")],
            [InlineKeyboardButton("⏰ Set Reminder Interval", callback_data="setup_interval")],
            [InlineKeyboardButton("🎨 Choose Theme", callback_data="setup_theme")],
            [InlineKeyboardButton("✅ Finish Setup and View Settings", callback_data="setup_complete")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        setup_text = "🛠️ *Setup Your Hippo Bot*\n\n"
        setup_text += "Let's configure your water reminder preferences:\n\n"
        setup_text += "• **Hippo Name**: Give your companion a personal name\n"
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
        
        # Get user data for hippo name
        user_data = await self.database.get_user(user_id)
        hippo_name = user_data.get('hippo_name', 'Hippo') if user_data else 'Hippo'
        
        # Calculate next reminder time
        next_reminder_text = await self._calculate_next_reminder_text(user_id)
        
        stats_text = f"📊 *{hippo_name}'s Hydration Report (Last 7 Days)*\n\n"
        stats_text += f"💧 Water confirmations: {stats['confirmed']}\n"
        stats_text += f"❌ Missed reminders: {stats['missed']}\n"
        stats_text += f"📈 Success rate: {success_rate:.1f}%\n\n"
        stats_text += f"{hippo_name}'s current assessment:\n{level_descriptions[hydration_level]}\n\n"
        stats_text += f"⏰ {next_reminder_text}"
        
        # Add achievement count to stats
        achievement_count = await self.database.get_achievement_count(user_id)
        total_achievements = len([a for a in ACHIEVEMENTS.values() if not a.hidden])
        
        stats_text += f"\n\n🏆 Achievements: {achievement_count}/{total_achievements}"
        
        # Add inline button for charts
        keyboard = [
            [InlineKeyboardButton("📊 View Charts", callback_data="stats_charts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def achievements_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /achievements command."""
        user_id = update.effective_user.id
        
        # Get user's earned achievements
        earned_achievements = await self.database.get_user_achievements(user_id)
        earned_codes = {ach['code'] for ach in earned_achievements}
        
        # Get all achievements grouped by category
        all_achievements = self.achievement_checker.get_all_achievements()
        
        # Build achievements display
        achievements_text = "🏆 **Your Achievements**\n\n"
        
        category_names = {
            'easy': '💧 Easy',
            'consistency': '🔥 Consistency',
            'performance': '⭐ Performance',
            'special': '✨ Special',
            'milestone': '🎯 Milestones'
        }
        
        total_earned = 0
        total_available = 0
        
        for category, achievements in all_achievements.items():
            if not achievements:
                continue
                
            achievements_text += f"**{category_names[category]}**\n"
            
            for achievement in achievements:
                total_available += 1
                if achievement.code in earned_codes:
                    total_earned += 1
                    achievements_text += f"✅ {achievement.icon} **{achievement.name}**\n"
                    achievements_text += f"   _{achievement.description}_\n"
                else:
                    achievements_text += f"🔒 {achievement.icon} {achievement.name}\n"
                    achievements_text += f"   _{achievement.description}_\n"
            
            achievements_text += "\n"
        
        # Add summary
        percentage = (total_earned / total_available * 100) if total_available > 0 else 0
        achievements_text += f"**Progress: {total_earned}/{total_available} ({percentage:.0f}%)**\n\n"
        
        # Add encouragement based on progress
        if percentage == 100:
            achievements_text += "🎉 Incredible! You've unlocked all achievements!"
        elif percentage >= 75:
            achievements_text += "🌟 Amazing progress! You're almost there!"
        elif percentage >= 50:
            achievements_text += "💪 Great job! You're halfway to completing all achievements!"
        elif percentage >= 25:
            achievements_text += "🌱 Good start! Keep drinking water to unlock more!"
        else:
            achievements_text += "💧 Start your journey! Each sip brings new achievements!"
        
        await update.message.reply_text(achievements_text, parse_mode='Markdown')
    
    async def charts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /charts command with chart selection options."""
        user_id = update.effective_user.id
        
        # Check if user exists
        user = await self.database.get_user(user_id)
        if not user:
            await update.message.reply_text(
                "Please start the bot first with /start to set up your account!"
            )
            return
        
        # Check if chart generator is initialized
        if not self.chart_generator:
            logger.error("Chart generator not initialized")
            await update.message.reply_text(
                "❌ Chart system is still starting up. Please try again in a moment!"
            )
            return
        
        # Create inline keyboard for chart selection
        keyboard = [
            [
                InlineKeyboardButton("📊 Daily Timeline", callback_data="chart_daily"),
                InlineKeyboardButton("📈 Weekly Trend", callback_data="chart_weekly")
            ],
            [
                InlineKeyboardButton("📅 Monthly Calendar", callback_data="chart_monthly"),
                InlineKeyboardButton("🥧 Success Rate", callback_data="chart_pie")
            ],
            [
                InlineKeyboardButton("📶 Progress Bar", callback_data="chart_progress"),
                InlineKeyboardButton("📋 Dashboard", callback_data="chart_dashboard")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📊 **Hydration Charts & Visualizations**\n\n"
            "Choose the type of chart you'd like to view:\n\n"
            "📊 **Daily Timeline** - 24-hour view of today's hydration\n"
            "📈 **Weekly Trend** - 7-day hydration level progress\n"
            "📅 **Monthly Calendar** - Color-coded monthly overview\n"
            "🥧 **Success Rate** - Pie chart of confirmations vs misses\n"
            "📶 **Progress Bar** - Current hydration level indicator\n"
            "📋 **Dashboard** - Combined stats overview\n\n"
            "Select a chart to generate:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
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
    
    async def quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quote command."""
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
            
            # Get a random inspirational quote from the content manager (async version)
            quote = await self.content_manager.get_random_quote_async()
            
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
            quote_text = f"💭 *Here's an inspirational quote for you:*\n\n{quote}\n\n"
            quote_text += f"💧 *Current Hydration:* {level_descriptions[hydration_level]}\n\n"
            quote_text += "Stay inspired and stay hydrated! 🦛✨"
            
            # Send the image with the quote
            with open(f"assets/{image_path}", 'rb') as image_file:
                await update.message.reply_photo(
                    photo=image_file,
                    caption=quote_text,
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            logger.error(f"Error handling quote command: {e}")
            await update.message.reply_text(
                "❌ Sorry, I couldn't fetch a quote right now. Please try again later!"
            )
    
    async def hipponame_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /hipponame command."""
        user_id = update.effective_user.id
        
        # Get current hippo name
        user_data = await self.database.get_user(user_id)
        if not user_data:
            await update.message.reply_text(
                "Please use /start to set up your account first!"
            )
            return
        
        current_name = user_data.get('hippo_name', 'Hippo')
        
        # Check if user provided a new name
        args = update.message.text.split(' ', 1)
        if len(args) > 1:
            new_name = args[1].strip()
            
            # Validate and save the new name
            if await self._validate_and_save_hippo_name(user_id, new_name):
                await update.message.reply_text(
                    f"🦛 *Name updated!*\n\n"
                    f"Your hippo is now named **{new_name}**!\n"
                    f"{new_name} is excited to continue helping you stay hydrated! 💧",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ *Invalid name!*\n\n"
                    "Please make sure the name is:\n"
                    "• 1-20 characters long\n"
                    "• Contains only letters, numbers, spaces, hyphens, apostrophes, or periods\n\n"
                    "Example: `/hipponame Bubbles`",
                    parse_mode='Markdown'
                )
        else:
            # Show current name and instructions
            await update.message.reply_text(
                f"🦛 *Your Hippo's Name*\n\n"
                f"Current name: **{current_name}**\n\n"
                f"To change the name, use:\n"
                f"`/hipponame [new name]`\n\n"
                f"Example: `/hipponame Splashy`\n\n"
                f"Or use /setup to access the name selection menu.",
                parse_mode='Markdown'
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
        elif query.data.startswith("name_"):
            await self._handle_name_selection(query)
        elif query.data.startswith("custom_hours_"):
            await self._handle_custom_hours_callback(query)
        elif query.data.startswith("start_hour_"):
            await self._handle_start_hour_selection(query)
        elif query.data.startswith("start_time_"):
            await self._handle_start_time_selection(query)
        elif query.data.startswith("end_hour_"):
            await self._handle_end_hour_selection(query)
        elif query.data.startswith("end_time_"):
            await self._handle_end_time_selection(query)
        elif query.data == "stats":
            await self._handle_stats_callback(query)
        elif query.data == "stats_charts":
            await self._handle_stats_charts_callback(query)
        elif query.data.startswith("chart_"):
            await self._handle_chart_callback(query)
        else:
            await query.edit_message_text("Unknown button action")
    
    async def _handle_water_confirmation(self, query):
        """Handle water drinking confirmation with two-phase update for better UX."""
        try:
            # Extract reminder ID from callback data
            reminder_id = query.data.replace("confirm_water_", "")
            user_id = query.from_user.id
            
            # Get user data early for immediate feedback
            user_data = await self.database.get_user(user_id)
            hippo_name = user_data.get('hippo_name', 'Hippo') if user_data else 'Hippo'
            
            # PHASE 1: Immediate text-only update for instant feedback
            try:
                immediate_text = f"✅ **{hippo_name} is so proud!** Recording your water intake...\n\n🔄 Updating your hydration status..."
                if query.message.photo:
                    await query.edit_message_caption(
                        caption=immediate_text,
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        immediate_text,
                        parse_mode='Markdown'
                    )
            except Exception as immediate_error:
                logger.warning(f"Could not provide immediate feedback: {immediate_error}")
            
            # Get reminder creation time if available (for quick response achievement)
            reminder_time = None
            
            # Record the confirmation
            await self.database.record_hydration_event(user_id, 'confirmed', reminder_id)
            
            # Remove from active reminders
            await self.database.remove_active_reminder(reminder_id)
            
            # Check for new achievements
            new_achievements = await self.achievement_checker.check_confirmation_achievements(user_id, reminder_time)
            
            # Check hydration level achievements
            hydration_level = await self.database.calculate_hydration_level(user_id)
            level_achievements = await self.achievement_checker.check_level_achievements(user_id, hydration_level)
            new_achievements.extend(level_achievements)
            
            # Get updated hydration level and stats
            hydration_level = await self.database.calculate_hydration_level(user_id)
            daily_stats = await self.database.get_user_hydration_stats(user_id, days=1)
            
            # Get theme (user_data already retrieved above)
            theme = user_data.get('theme', 'bluey') if user_data else 'bluey'
            
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
            
            # Get appropriate response message, fresh inspirational quote, and celebratory poem
            confirmation_message = self.content_manager.get_confirmation_message(hydration_level)
            fresh_quote = self.content_manager.get_random_quote()
            celebration_poem = self.content_manager.get_random_poem()
            
            # Build enhanced confirmation message with fresh quote and poem
            response_text = f"✅ **{hippo_name} is beaming with pride!** {confirmation_message}\n\n"
            response_text += f"💭 **{hippo_name}'s Inspiration for you:**\n{fresh_quote}\n\n"
            
            response_text += f"📊 **{hippo_name}'s Updated Status Report:**\n"
            response_text += f"• Current level: {level_descriptions[hydration_level]}\n"
            response_text += f"• Today: {daily_stats['confirmed']}✅ {daily_stats['missed']}❌"
            if total_today > 0:
                response_text += f" ({success_rate:.0f}%)"
            response_text += "\n\n"
            
            # Add level-specific encouragement with hippo name
            if hydration_level >= 4:
                response_text += f"🌟 {hippo_name} says you're doing amazing! Keep up this fantastic hydration routine!\n\n"
            elif hydration_level >= 2:
                response_text += f"💪 {hippo_name} sees your great progress! You're building excellent habits!\n\n"
            else:
                response_text += f"🌱 {hippo_name} knows every sip counts! You're on the right track!\n\n"
            
            # Add achievement notifications if any
            if new_achievements:
                response_text += "🏆 **New Achievements Unlocked!**\n"
                for achievement_code in new_achievements:
                    achievement = ACHIEVEMENTS.get(achievement_code)
                    if achievement:
                        response_text += f"{achievement.icon} **{achievement.name}** - {achievement.description}\n"
                response_text += "\n"
            
            # Add a celebratory poem as a reward
            response_text += f"🎉 **{hippo_name} has a celebration poem just for you:**\n\n{celebration_poem}"
            
            # Get the updated image for the new hydration level
            updated_image_path = self.content_manager.get_image_for_hydration_level(hydration_level, theme)
            full_image_path = f"assets/{updated_image_path}"
            
            # PHASE 2: Update with final content and image
            try:
                # Check if original message has a photo
                if query.message.photo:
                    # Edit the message media (image) and caption
                    from telegram import InputMediaPhoto
                    
                    with open(full_image_path, 'rb') as photo:
                        new_media = InputMediaPhoto(
                            media=photo,
                            caption=response_text,
                            parse_mode='Markdown'
                        )
                        await query.edit_message_media(media=new_media)
                else:
                    # Original message was text-only, try to edit it
                    await query.edit_message_text(
                        response_text,
                        parse_mode='Markdown'
                    )
            except Exception as edit_error:
                logger.warning(f"Could not update message with new image: {edit_error}")
                # Fallback: try to edit caption/text only without changing image
                try:
                    # First try editing as photo caption
                    await query.edit_message_caption(
                        caption=response_text,
                        parse_mode='Markdown'
                    )
                except Exception as fallback_error:
                    logger.warning(f"Caption edit fallback also failed: {fallback_error}")
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
        
        if action == "hippo_name":
            await self._setup_hippo_name(query)
        elif action == "timezone":
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
                [InlineKeyboardButton("🦛 Name Your Hippo", callback_data="setup_hippo_name")],
                [InlineKeyboardButton("🌍 Set Timezone", callback_data="setup_timezone")],
                [InlineKeyboardButton("🌅 Set Waking Hours", callback_data="setup_waking_hours")],
                [InlineKeyboardButton("⏰ Set Reminder Interval", callback_data="setup_interval")],
                [InlineKeyboardButton("🎨 Choose Theme", callback_data="setup_theme")],
                [InlineKeyboardButton("✅ Finish Setup and View Settings", callback_data="setup_complete")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            setup_text = "🛠️ *Setup Your Hippo Bot*\n\n"
            setup_text += "Let's configure your water reminder preferences:\n\n"
            setup_text += "• **Hippo Name**: Give your companion a personal name\n"
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
    
    async def _setup_hippo_name(self, query):
        """Handle hippo name setup."""
        import random
        
        # Get current hippo name
        user_id = query.from_user.id
        user_data = await self.database.get_user(user_id)
        current_name = user_data.get('hippo_name', 'Hippo') if user_data else 'Hippo'
        
        # Select 6 random suggestions
        suggestions = random.sample(HIPPO_NAME_SUGGESTIONS, 6)
        
        keyboard = []
        # Add suggestion buttons in rows of 2
        for i in range(0, len(suggestions), 2):
            row = []
            row.append(InlineKeyboardButton(f"🦛 {suggestions[i]}", callback_data=f"name_{suggestions[i]}"))
            if i + 1 < len(suggestions):
                row.append(InlineKeyboardButton(f"🦛 {suggestions[i+1]}", callback_data=f"name_{suggestions[i+1]}"))
            keyboard.append(row)
        
        # Add custom name and back button
        keyboard.append([InlineKeyboardButton("✏️ Enter Custom Name", callback_data="name_custom")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Setup", callback_data="setup_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🦛 *Name Your Hippo Companion*\n\n"
        text += f"Your hippo's current name is: **{current_name}**\n\n"
        text += "Choose a new name from the suggestions below, or enter a custom name:\n\n"
        text += "💧 Your hippo will appear in all reminders and messages!"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
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
        
        # Show hippo name
        hippo_name = user_data.get('hippo_name', 'Hippo')
        completion_text += f"• Hippo Name: {hippo_name}\n"
        
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
        next_reminder_text = await self._calculate_next_reminder_text(user_id)
        completion_text += f"⏰ **{next_reminder_text}**\n\n"
        
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
            await self._start_custom_hours_setup(query)
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
    
    async def _handle_name_selection(self, query):
        """Handle hippo name selection."""
        try:
            user_id = query.from_user.id
            selection = query.data.replace("name_", "")
            
            if selection == "custom":
                # Handle custom name input
                await query.edit_message_text(
                    "✏️ *Enter Custom Hippo Name*\n\n"
                    "Please type your hippo's new name in the chat.\n"
                    "The name should be 1-20 characters long.\n\n"
                    "💡 *Tip*: Use /setup to return to the setup menu if needed.",
                    parse_mode='Markdown'
                )
                # Store state for text message handler
                if not hasattr(self, '_awaiting_custom_name'):
                    self._awaiting_custom_name = set()
                self._awaiting_custom_name.add(user_id)
            else:
                # Handle predefined name selection
                name = selection
                if await self._validate_and_save_hippo_name(user_id, name):
                    await query.edit_message_text(
                        f"🦛 *Great choice!*\n\n"
                        f"Your hippo is now named **{name}**!\n"
                        f"{name} is excited to help you stay hydrated! 💧",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("✅ Finish Setup", callback_data="setup_complete")
                        ]])
                    )
                else:
                    await query.edit_message_text("❌ Error saving hippo name. Please try again.")
                    
        except Exception as e:
            logger.error(f"Error setting hippo name: {e}")
            await query.edit_message_text("❌ Error setting hippo name. Please try again.")
    
    async def _validate_and_save_hippo_name(self, user_id: int, name: str) -> bool:
        """Validate and save hippo name."""
        # Validate name
        if not name or len(name.strip()) == 0:
            return False
        
        name = name.strip()
        
        # Length validation
        if len(name) > 20:
            return False
        
        # Basic content validation (no special characters except spaces, hyphens, apostrophes, periods)
        import re
        if not re.match(r"^[a-zA-Z0-9\s\-'.]+$", name):
            return False
        
        # Save to database
        return await self.database.update_user_hippo_name(user_id, name)
    
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
                    "Run /start to begin fresh! 🦛",
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
        

    async def _start_custom_hours_setup(self, query):
        """Start the custom hours setup process."""
        await self._setup_start_time(query)

    async def _setup_start_time(self, query):
        """Setup start time selection."""
        keyboard = []
        
        # Create hour selection buttons (0-23)
        for row in range(6):  # 6 rows of 4 buttons each
            hour_row = []
            for col in range(4):
                hour = row * 4 + col
                if hour < 24:
                    hour_row.append(InlineKeyboardButton(
                        f"{hour:02d}:xx", 
                        callback_data=f"start_hour_{hour}"
                    ))
            if hour_row:
                keyboard.append(hour_row)
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="setup_waking_hours")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🌅 *Step 1: Choose Start Hour*\n\n"
        text += "When do you want to START receiving reminders?\n"
        text += "Select the hour (you'll choose minutes next):"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

    async def _setup_start_minute(self, query, hour):
        """Setup start minute selection."""
        keyboard = [
            [
                InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"start_time_{hour}_0"),
                InlineKeyboardButton(f"{hour:02d}:15", callback_data=f"start_time_{hour}_15")
            ],
            [
                InlineKeyboardButton(f"{hour:02d}:30", callback_data=f"start_time_{hour}_30"),
                InlineKeyboardButton(f"{hour:02d}:45", callback_data=f"start_time_{hour}_45")
            ],
            [InlineKeyboardButton("⬅️ Back to Hours", callback_data="custom_hours_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"🕐 *Step 1: Choose Start Minute*\n\n"
        text += f"Start hour: **{hour:02d}:xx**\n\n"
        text += "Select the exact start time:"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

    async def _setup_end_time(self, query, start_hour, start_minute):
        """Setup end time selection."""
        keyboard = []
        
        # Create hour selection buttons (0-23)
        for row in range(6):  # 6 rows of 4 buttons each
            hour_row = []
            for col in range(4):
                hour = row * 4 + col
                if hour < 24:
                    hour_row.append(InlineKeyboardButton(
                        f"{hour:02d}:xx", 
                        callback_data=f"end_hour_{start_hour}_{start_minute}_{hour}"
                    ))
            if hour_row:
                keyboard.append(hour_row)
        
        keyboard.append([InlineKeyboardButton("⬅️ Back to Start Time", callback_data="custom_hours_start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"🌙 *Step 2: Choose End Hour*\n\n"
        text += f"Start time: **{start_hour:02d}:{start_minute:02d}**\n\n"
        text += "When do you want to STOP receiving reminders?\n"
        text += "Select the hour (you'll choose minutes next):"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

    async def _setup_end_minute(self, query, start_hour, start_minute, end_hour):
        """Setup end minute selection."""
        keyboard = [
            [
                InlineKeyboardButton(f"{end_hour:02d}:00", callback_data=f"end_time_{start_hour}_{start_minute}_{end_hour}_0"),
                InlineKeyboardButton(f"{end_hour:02d}:15", callback_data=f"end_time_{start_hour}_{start_minute}_{end_hour}_15")
            ],
            [
                InlineKeyboardButton(f"{end_hour:02d}:30", callback_data=f"end_time_{start_hour}_{start_minute}_{end_hour}_30"),
                InlineKeyboardButton(f"{end_hour:02d}:45", callback_data=f"end_time_{start_hour}_{start_minute}_{end_hour}_45")
            ],
            [InlineKeyboardButton("⬅️ Back to Hours", callback_data=f"end_hour_{start_hour}_{start_minute}_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"🕐 *Step 2: Choose End Minute*\n\n"
        text += f"Start time: **{start_hour:02d}:{start_minute:02d}**\n"
        text += f"End hour: **{end_hour:02d}:xx**\n\n"
        text += "Select the exact end time:"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

    async def _complete_custom_hours_setup(self, query, start_hour, start_minute, end_hour, end_minute):
        """Complete the custom hours setup."""
        user_id = query.from_user.id
        
        # Validate times
        if start_hour == end_hour and start_minute == end_minute:
            await query.edit_message_text(
                "❌ *Invalid Time Range*\n\n"
                "Start and end times cannot be the same.\n"
                "Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Try Again", callback_data="custom_hours_start")
                ]])
            )
            return
        
        # Save to database
        success = await self.database.update_user_waking_hours(
            user_id, start_hour, start_minute, end_hour, end_minute
        )
        
        if success:
            # Create time display
            start_time = f"{start_hour:02d}:{start_minute:02d}"
            end_time = f"{end_hour:02d}:{end_minute:02d}"
            
            # Check if it's overnight schedule
            is_overnight = (start_hour > end_hour) or (start_hour == end_hour and start_minute > end_minute)
            schedule_type = "overnight" if is_overnight else "regular"
            
            text = f"✅ *Custom Hours Set Successfully!*\n\n"
            text += f"**Your new schedule:**\n"
            text += f"🌅 Start: {start_time}\n"
            text += f"🌙 End: {end_time}\n"
            text += f"📅 Type: {schedule_type} schedule\n\n"
            
            if is_overnight:
                text += "💡 *Overnight schedule detected!*\n"
                text += f"Reminders from {start_time} until {end_time} next day.\n\n"
            
            text += "Your water reminders will now follow this custom schedule! 🦛💧"
            
            keyboard = [
                [InlineKeyboardButton("⚙️ Back to Setup", callback_data="setup_back")],
                [InlineKeyboardButton("📊 View Stats", callback_data="stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await query.edit_message_text(
                "❌ *Error saving custom hours*\n\n"
                "Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Try Again", callback_data="custom_hours_start")
                ]])
            )

    async def _handle_custom_hours_callback(self, query):
        """Handle custom hours related callbacks."""
        action = query.data.replace("custom_hours_", "")
        
        if action == "start":
            await self._setup_start_time(query)
        elif action == "cancel":
            # Return to setup menu
            await self._setup_waking_hours(query)

    async def _handle_start_hour_selection(self, query):
        """Handle start hour selection."""
        hour = int(query.data.replace("start_hour_", ""))
        await self._setup_start_minute(query, hour)

    async def _handle_start_time_selection(self, query):
        """Handle start time (hour and minute) selection."""
        parts = query.data.replace("start_time_", "").split("_")
        start_hour = int(parts[0])
        start_minute = int(parts[1])
        await self._setup_end_time(query, start_hour, start_minute)

    async def _handle_end_hour_selection(self, query):
        """Handle end hour selection."""
        parts = query.data.replace("end_hour_", "").split("_")
        
        if parts[-1] == "back":
            # Back button - return to end hour selection
            start_hour = int(parts[0])
            start_minute = int(parts[1])
            await self._setup_end_time(query, start_hour, start_minute)
        else:
            # Regular end hour selection
            start_hour = int(parts[0])
            start_minute = int(parts[1])
            end_hour = int(parts[2])
            await self._setup_end_minute(query, start_hour, start_minute, end_hour)

    async def _handle_end_time_selection(self, query):
        """Handle end time (hour and minute) selection."""
        parts = query.data.replace("end_time_", "").split("_")
        start_hour = int(parts[0])
        start_minute = int(parts[1])
        end_hour = int(parts[2])
        end_minute = int(parts[3])
        await self._complete_custom_hours_setup(query, start_hour, start_minute, end_hour, end_minute)

    async def _handle_stats_callback(self, query):
        """Handle stats callback from inline button."""
        user_id = query.from_user.id
        
        # Get user stats
        stats = await self.database.get_user_hydration_stats(user_id, days=7)
        
        if not stats:
            await query.edit_message_text("❌ No stats available yet. Start drinking water to see your progress!")
            return
        
        # Calculate success rate
        total_events = stats['confirmed'] + stats['missed']
        if total_events > 0:
            success_rate = (stats['confirmed'] / total_events) * 100
        else:
            success_rate = 0
        
        # Get current hydration level
        hydration_level = await self.database.calculate_hydration_level(user_id)
        
        # Get user data for hippo name
        user_data = await self.database.get_user(user_id)
        hippo_name = user_data.get('hippo_name', 'Hippo') if user_data else 'Hippo'
        
        level_descriptions = {
            0: "🏜️ Completely Dehydrated - Needs immediate water!",
            1: "😵 Very Dehydrated - Multiple glasses needed",
            2: "😰 Dehydrated - Time for some water",
            3: "😊 Moderately Hydrated - Keep it up",
            4: "😄 Well Hydrated - Great job!",
            5: "🤩 Perfectly Hydrated - You're crushing it!"
        }
        
        stats_text = f"📊 *{hippo_name}'s Hydration Report (Last 7 Days)*\n\n"
        stats_text += f"💧 Water confirmations: {stats['confirmed']}\n"
        stats_text += f"❌ Missed reminders: {stats['missed']}\n"
        stats_text += f"📈 Success rate: {success_rate:.1f}%\n\n"
        stats_text += f"Current hydration level:\n{level_descriptions[hydration_level]}"
        
        await query.edit_message_text(stats_text, parse_mode='Markdown')
    
    async def _handle_chart_callback(self, query):
        """Handle chart generation callbacks."""
        user_id = query.from_user.id
        chart_type = query.data.replace("chart_", "")
        
        try:
            # Show loading message
            await query.edit_message_text("🔄 Generating chart... Please wait a moment!")
            
            # Get current hydration level and user data
            current_level = await self.database.calculate_hydration_level(user_id)
            user = await self.database.get_user(user_id)
            
            chart_buf = None
            
            if chart_type == "daily":
                # Daily timeline chart
                today = datetime.now()
                events = await self.database.get_hydration_events_for_date(user_id, today)
                chart_buf = await self.chart_generator.generate_daily_timeline(
                    user_id, events, current_level, today
                )
                caption = f"📊 **Daily Hydration Timeline**\n\n"
                caption += f"Today's hydration events at a glance.\n"
                caption += f"Current Level: {current_level}/5 💧"
                
            elif chart_type == "weekly":
                # Weekly trend chart
                weekly_data = await self.database.get_daily_hydration_summary(user_id, 7)
                # Add average level calculation for each day
                for day in weekly_data:
                    # Simple approximation - could be improved
                    day['avg_level'] = min(5, max(0, day['success_rate'] * 5))
                chart_buf = await self.chart_generator.generate_weekly_trend(user_id, weekly_data)
                caption = f"📈 **Weekly Hydration Trend**\n\n"
                caption += f"Your hydration progress over the last 7 days.\n"
                caption += f"Current Level: {current_level}/5 💧"
                
            elif chart_type == "monthly":
                # Monthly calendar chart
                now = datetime.now()
                monthly_data = await self.database.get_monthly_hydration_summary(user_id, now.year, now.month)
                # Add average level calculation for each day
                for day in monthly_data:
                    day['avg_level'] = min(5, max(0, day['success_rate'] * 5))
                chart_buf = await self.chart_generator.generate_monthly_calendar(
                    user_id, monthly_data, now.year, now.month
                )
                caption = f"📅 **Monthly Hydration Calendar**\n\n"
                caption += f"Color-coded overview of {now.strftime('%B %Y')}.\n"
                caption += f"Current Level: {current_level}/5 💧"
                
            elif chart_type == "pie":
                # Success rate pie chart
                stats = await self.database.get_user_hydration_stats(user_id, 30)  # Last 30 days
                chart_buf = await self.chart_generator.generate_success_rate_pie(user_id, stats)
                total = stats['confirmed'] + stats['missed']
                success_rate = (stats['confirmed'] / total * 100) if total > 0 else 0
                caption = f"🥧 **Success Rate Chart**\n\n"
                caption += f"Your hydration success rate (last 30 days).\n"
                caption += f"Success Rate: {success_rate:.1f}% ({stats['confirmed']}/{total})"
                
            elif chart_type == "progress":
                # Progress bar chart
                chart_buf = await self.chart_generator.generate_progress_bar(user_id, current_level)
                caption = f"📶 **Hydration Progress Bar**\n\n"
                caption += f"Your current hydration level visualization.\n"
                caption += f"Level {current_level} of 5 ({current_level/5*100:.0f}%)"
                
            elif chart_type == "dashboard":
                # Stats dashboard
                stats = await self.database.get_user_hydration_stats(user_id, 7)
                achievement_count = await self.database.get_achievement_count(user_id)
                recent_levels = await self.database.get_recent_hydration_levels(user_id, 7)
                
                stats_data = {
                    'confirmed': stats['confirmed'],
                    'missed': stats['missed'],
                    'current_level': current_level,
                    'achievement_count': achievement_count,
                    'recent_levels': recent_levels
                }
                chart_buf = await self.chart_generator.generate_stats_dashboard(user_id, stats_data)
                caption = f"📋 **Hydration Dashboard**\n\n"
                caption += f"Complete overview of your hydration metrics.\n"
                caption += f"Current Level: {current_level}/5 💧"
                
            else:
                await query.edit_message_text("❌ Unknown chart type requested.")
                return
            
            if chart_buf:
                # Send the chart image
                await query.delete_message()  # Delete the loading message
                await query.message.reply_photo(
                    photo=chart_buf,
                    caption=caption,
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text("❌ Failed to generate chart. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error generating chart {chart_type} for user {user_id}: {e}")
            await query.edit_message_text(
                f"❌ Error generating chart: {str(e)}\n\n"
                "This might be due to insufficient data. Try using the bot for a few days first!"
            )
    
    async def _handle_stats_charts_callback(self, query):
        """Handle stats charts callback to show chart selection options."""
        # Create inline keyboard for chart selection
        keyboard = [
            [
                InlineKeyboardButton("📊 Daily Timeline", callback_data="chart_daily"),
                InlineKeyboardButton("📈 Weekly Trend", callback_data="chart_weekly")
            ],
            [
                InlineKeyboardButton("📅 Monthly Calendar", callback_data="chart_monthly"),
                InlineKeyboardButton("🥧 Success Rate", callback_data="chart_pie")
            ],
            [
                InlineKeyboardButton("📶 Progress Bar", callback_data="chart_progress"),
                InlineKeyboardButton("📋 Dashboard", callback_data="chart_dashboard")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📊 **Hydration Charts & Visualizations**\n\n"
            "Choose the type of chart you'd like to view:\n\n"
            "📊 **Daily Timeline** - 24-hour view of today's hydration\n"
            "📈 **Weekly Trend** - 7-day hydration level progress\n"
            "📅 **Monthly Calendar** - Color-coded monthly overview\n"
            "🥧 **Success Rate** - Pie chart of confirmations vs misses\n"
            "📶 **Progress Bar** - Current hydration level indicator\n"
            "📋 **Dashboard** - Combined stats overview\n\n"
            "Select a chart to generate:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _calculate_next_reminder_text(self, user_id: int) -> str:
        """Calculate when the next reminder will be sent."""
        try:
            # Get user data
            user_data = await self.database.get_user(user_id)
            if not user_data or not user_data['is_active']:
                return "Next reminder: User not active"
            
            # Get user's timezone
            user_tz_str = user_data.get('timezone', 'Asia/Singapore')
            try:
                user_tz = pytz.timezone(user_tz_str)
            except Exception:
                user_tz = pytz.timezone('Asia/Singapore')
            
            # Get current time in user's timezone
            now_utc = datetime.now(pytz.UTC)
            now_local = now_utc.astimezone(user_tz)
            
            # Check if currently within waking hours
            from src.bot.reminder_system import ReminderSystem
            reminder_system = ReminderSystem(self.database, self.content_manager)
            is_within_waking_hours = reminder_system._is_within_waking_hours(user_data)
            
            if not is_within_waking_hours:
                # Calculate next waking time
                next_wake_time = self._calculate_next_wake_time(user_data, now_local)
                if next_wake_time:
                    return f"Next reminder: {next_wake_time.strftime('%H:%M')} (when waking hours start)"
                else:
                    return "Next reminder: When waking hours start"
            
            # User is within waking hours, calculate next reminder based on interval
            interval_minutes = user_data['reminder_interval_minutes']
            
            # Get last reminder time
            async with self.database.connection.execute("""
                SELECT MAX(last_reminder) as last_reminder FROM (
                    SELECT MAX(created_at) as last_reminder
                    FROM active_reminders 
                    WHERE user_id = ?
                    UNION ALL
                    SELECT MAX(created_at) as last_reminder
                    FROM hydration_events 
                    WHERE user_id = ?
                )
            """, (user_id, user_id)) as cursor:
                result = await cursor.fetchone()
            
            if not result or not result[0]:
                # No previous reminders, next one should be soon
                return "Next reminder: Within the next few minutes"
            
            last_reminder_time = datetime.fromisoformat(result[0])
            next_reminder_time = last_reminder_time + timedelta(minutes=interval_minutes)
            
            # Convert to user's timezone for display
            if next_reminder_time.tzinfo is None:
                next_reminder_time = pytz.UTC.localize(next_reminder_time)
            next_reminder_local = next_reminder_time.astimezone(user_tz)
            
            # Check if next reminder is still within waking hours today
            if self._is_time_within_waking_hours(next_reminder_local.time(), user_data):
                # Format relative time
                time_diff = next_reminder_local - now_local
                if time_diff.total_seconds() <= 0:
                    return "Next reminder: Any moment now"
                elif time_diff.total_seconds() < 3600:  # Less than 1 hour
                    minutes = int(time_diff.total_seconds() / 60)
                    return f"Next reminder: In {minutes} minute{'s' if minutes != 1 else ''}"
                else:
                    return f"Next reminder: {next_reminder_local.strftime('%H:%M')}"
            else:
                # Next reminder would be outside waking hours, so it's tomorrow
                next_wake_time = self._calculate_next_wake_time(user_data, now_local)
                if next_wake_time:
                    return f"Next reminder: {next_wake_time.strftime('%H:%M')} (tomorrow)"
                else:
                    return "Next reminder: Tomorrow when waking hours start"
                    
        except Exception as e:
            logger.error(f"Error calculating next reminder for user {user_id}: {e}")
            return "Next reminder: Unable to calculate"
    
    def _calculate_next_wake_time(self, user_data: dict, current_time: datetime) -> Optional[datetime]:
        """Calculate the next time waking hours start."""
        try:
            start_hour = user_data['waking_start_hour']
            start_minute = user_data['waking_start_minute']
            
            # If 24/7 mode, return None
            if start_hour == 0 and user_data['waking_end_hour'] == 23:
                return None
            
            # Calculate next wake time (could be today or tomorrow)
            today_wake = current_time.replace(
                hour=start_hour, 
                minute=start_minute, 
                second=0, 
                microsecond=0
            )
            
            if today_wake > current_time:
                return today_wake
            else:
                # Tomorrow
                return today_wake + timedelta(days=1)
                
        except Exception as e:
            logger.error(f"Error calculating next wake time: {e}")
            return None
    
    def _is_time_within_waking_hours(self, check_time: time, user_data: dict) -> bool:
        """Check if a specific time is within waking hours."""
        start_hour = user_data['waking_start_hour']
        end_hour = user_data['waking_end_hour']
        start_minute = user_data['waking_start_minute']
        end_minute = user_data['waking_end_minute']
        
        # 24/7 mode
        if start_hour == 0 and end_hour == 23:
            return True
        
        start_time = time(start_hour, start_minute)
        end_time = time(end_hour, end_minute)
        
        # Handle overnight schedule
        if start_time <= end_time:
            return start_time <= check_time <= end_time
        else:
            return check_time >= start_time or check_time <= end_time

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        user_id = update.effective_user.id
        
        # Check if user is entering a custom hippo name
        if hasattr(self, '_awaiting_custom_name') and user_id in self._awaiting_custom_name:
            name = update.message.text.strip()
            
            # Validate the name
            if await self._validate_and_save_hippo_name(user_id, name):
                self._awaiting_custom_name.remove(user_id)
                await update.message.reply_text(
                    f"🦛 *Perfect!*\n\n"
                    f"Your hippo is now named **{name}**!\n"
                    f"{name} is excited to help you stay hydrated! 💧\n\n"
                    "Use /setup to continue configuring your bot.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ *Invalid name!*\n\n"
                    "Please make sure the name is:\n"
                    "• 1-20 characters long\n"
                    "• Contains only letters, numbers, spaces, hyphens, apostrophes, or periods\n\n"
                    "Try again or use /setup to return to the setup menu.",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "I'm here to help you stay hydrated! 🦛💧\n\n"
                "Use /help to see what I can do for you."
            )