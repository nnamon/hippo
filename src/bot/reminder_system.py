"""
Reminder system for Hippo bot - handles scheduling and sending water reminders.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional
from pathlib import Path
import pytz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database.models import DatabaseManager
from src.content.manager import ContentManager

logger = logging.getLogger(__name__)


class ReminderSystem:
    """Manages water reminder scheduling and delivery."""
    
    def __init__(self, database: DatabaseManager, content_manager: ContentManager):
        """Initialize the reminder system."""
        self.database = database
        self.content_manager = content_manager
        self.active_jobs: Dict[int, str] = {}  # user_id -> job_name mapping
    
    def schedule_user_reminders(self, job_queue, user_id: int):
        """Schedule or reschedule reminders for a user."""
        # Cancel existing job if any
        self.cancel_user_reminders(job_queue, user_id)
        
        # Schedule new job
        job_name = f"reminders_user_{user_id}"
        job_queue.run_repeating(
            self._check_and_send_reminder,
            interval=60,  # Check every minute
            first=10,     # Start after 10 seconds
            name=job_name,
            data={"user_id": user_id}
        )
        
        self.active_jobs[user_id] = job_name
        logger.info(f"Scheduled reminders for user {user_id}")
    
    def cancel_user_reminders(self, job_queue, user_id: int):
        """Cancel reminders for a user."""
        if user_id in self.active_jobs:
            job_name = self.active_jobs[user_id]
            
            # Find and remove the job
            current_jobs = job_queue.get_jobs_by_name(job_name)
            for job in current_jobs:
                job.schedule_removal()
            
            del self.active_jobs[user_id]
            logger.info(f"Cancelled reminders for user {user_id}")
    
    async def _check_and_send_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        """Check if it's time to send a reminder and send it if needed."""
        try:
            user_id = context.job.data["user_id"]
            user_data = await self.database.get_user(user_id)
            
            if not user_data or not user_data['is_active']:
                logger.debug(f"User {user_id} not active or not found")
                return
            
            # Check if it's within waking hours
            if not self._is_within_waking_hours(user_data):
                logger.debug(f"User {user_id} outside waking hours")
                return
            
            # Check if enough time has passed since last reminder
            should_send = await self._should_send_reminder(user_id, user_data['reminder_interval_minutes'])
            if not should_send:
                logger.debug(f"User {user_id} not ready for reminder yet")
                return
            
            # Send the reminder
            logger.info(f"Sending water reminder to user {user_id}")
            await self._send_water_reminder(context, user_id, user_data)
            
        except Exception as e:
            logger.error(f"Error in reminder check: {e}")
    
    def _is_within_waking_hours(self, user_data: Dict) -> bool:
        """Check if current time is within user's waking hours."""
        start_hour = user_data['waking_start_hour']
        end_hour = user_data['waking_end_hour']
        
        # 24/7 mode (0-23 hours)
        if start_hour == 0 and end_hour == 23:
            logger.debug(f"User {user_data.get('user_id', 'unknown')} in 24/7 mode - always active")
            return True
        
        # Get user's timezone, default to Singapore if not set
        user_tz_str = user_data.get('timezone', 'Asia/Singapore')
        try:
            user_tz = pytz.timezone(user_tz_str)
        except Exception as e:
            logger.error(f"Invalid timezone {user_tz_str} for user {user_data.get('user_id', 'unknown')}, using Singapore")
            user_tz = pytz.timezone('Asia/Singapore')
        
        # Get current time in user's timezone
        now_utc = datetime.now(pytz.UTC)
        now_local = now_utc.astimezone(user_tz).time()
        
        start_time = time(start_hour, user_data['waking_start_minute'])
        end_time = time(end_hour, user_data['waking_end_minute'])
        
        # Handle case where end time is next day (e.g., 22:00 to 06:00)
        if start_time <= end_time:
            # Normal case: 07:00 to 22:00
            is_within = start_time <= now_local <= end_time
            logger.debug(f"User {user_data.get('user_id', 'unknown')} waking hours check in {user_tz_str}: {start_time} <= {now_local} <= {end_time} = {is_within}")
            return is_within
        else:
            # Overnight case: 22:00 to 06:00
            is_within = now_local >= start_time or now_local <= end_time
            logger.debug(f"User {user_data.get('user_id', 'unknown')} overnight waking hours in {user_tz_str}: {now_local} >= {start_time} or {now_local} <= {end_time} = {is_within}")
            return is_within
    
    async def _should_send_reminder(self, user_id: int, interval_minutes: int) -> bool:
        """Check if enough time has passed since the last reminder."""
        try:
            # Get the last reminder time from either active reminders or hydration events
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
                # No previous reminders, send one now
                logger.debug(f"User {user_id}: No previous reminders found, sending first reminder")
                return True
            
            last_reminder_time = datetime.fromisoformat(result[0])
            current_time = datetime.now()
            time_since_last = current_time - last_reminder_time
            required_interval = timedelta(minutes=interval_minutes)
            
            should_send = time_since_last >= required_interval
            logger.debug(f"User {user_id}: Last reminder: {last_reminder_time}, Current: {current_time}, "
                        f"Time since: {time_since_last}, Required: {required_interval}, Should send: {should_send}")
            
            return should_send
            
        except Exception as e:
            logger.error(f"Error checking reminder timing for user {user_id}: {e}")
            return False
    
    async def _send_water_reminder(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, user_data: Dict):
        """Send a water reminder to the user."""
        try:
            # First expire any active reminders for this user
            expired_count, expired_messages = await self.database.expire_user_active_reminders(user_id)
            if expired_count > 0:
                logger.info(f"Expired {expired_count} unacknowledged reminders for user {user_id}")
                logger.debug(f"Expired messages to edit: {expired_messages}")
                # Edit expired messages to show they're expired
                for message_id, chat_id in expired_messages:
                    logger.debug(f"Editing message {message_id} in chat {chat_id}")
                    await self._mark_reminder_as_expired(context, chat_id, message_id)
            
            # Generate reminder ID
            reminder_id = str(uuid.uuid4())
            
            # Get current hydration level
            hydration_level = await self.database.calculate_hydration_level(user_id)
            
            # Get recent stats for display
            stats = await self.database.get_user_hydration_stats(user_id, days=1)
            total_today = stats['confirmed'] + stats['missed']
            success_rate = (stats['confirmed'] / total_today * 100) if total_today > 0 else 0
            
            # Get content for the reminder
            content = self.content_manager.get_reminder_content(hydration_level, user_data['theme'])
            
            # Hydration level descriptions
            level_descriptions = [
                "😵 Dehydrated",
                "😟 Low hydration", 
                "😐 Moderate hydration",
                "😊 Good hydration",
                "😄 Great hydration",
                "🤩 Perfect hydration"
            ]
            
            # Create confirmation button
            keyboard = [[
                InlineKeyboardButton("💧 I drank water!", callback_data=f"confirm_water_{reminder_id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Prepare message text with inspirational quote and stats
            message_text = f"🦛 **Time for a Hydration Break!**\n\n"
            message_text += f"{content['quote']}\n\n"
            message_text += f"📊 **Your Status:**\n"
            message_text += f"• Current level: {level_descriptions[hydration_level]}\n"
            message_text += f"• Today: {stats['confirmed']}✅ {stats['missed']}❌"
            if total_today > 0:
                message_text += f" ({success_rate:.0f}%)"
            message_text += f"\n\n💧 Tap the button below when you've had some water! 🦛"
            
            # Send the message with image
            image_path = Path("assets") / content['image']
            
            if image_path.exists():
                # Send with image
                with open(image_path, 'rb') as photo:
                    message = await context.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=message_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
            else:
                # Send text only if image not found
                message = await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🦛 {message_text}",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            
            # Record the active reminder with expiration
            expires_at = datetime.now() + timedelta(minutes=30)
            await self.database.create_active_reminder(
                user_id, reminder_id, message.message_id, user_id, expires_at
            )
            
            logger.info(f"Sent water reminder {reminder_id} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending water reminder to user {user_id}: {e}")
    
    async def start_reminders_for_user(self, job_queue, user_id: int):
        """Start reminders for a specific user."""
        user_data = await self.database.get_user(user_id)
        
        if user_data and user_data['is_active']:
            self.schedule_user_reminders(job_queue, user_id)
            return True
        return False
    
    async def start_all_user_reminders(self, job_queue):
        """Start reminders for all active users."""
        try:
            async with self.database.connection.execute("""
                SELECT user_id FROM users WHERE is_active = 1
            """) as cursor:
                users = await cursor.fetchall()
            
            for (user_id,) in users:
                self.schedule_user_reminders(job_queue, user_id)
            
            logger.info(f"Started reminders for {len(users)} active users")
            
        except Exception as e:
            logger.error(f"Error starting user reminders: {e}")
    
    def stop_all_reminders(self, job_queue):
        """Stop all active reminder jobs."""
        for user_id in list(self.active_jobs.keys()):
            self.cancel_user_reminders(job_queue, user_id)
        
        logger.info("Stopped all reminder jobs")
    
    async def _mark_reminder_as_expired(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
        """Mark a reminder message as expired by editing it."""
        try:
            # Create expired button
            keyboard = [[
                InlineKeyboardButton("⏰ Expired - Missed this reminder", callback_data="expired_reminder")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Edit message reply markup (works for both photo and text messages)
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=reply_markup
                )
                logger.debug(f"Successfully marked reminder {message_id} as expired in chat {chat_id}")
            except Exception as e:
                logger.warning(f"Could not edit expired message {message_id} in chat {chat_id}: {e}")
        except Exception as e:
            logger.error(f"Error marking reminder as expired: {e}")