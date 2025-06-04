"""
Database models and operations for Hippo bot.
"""

import aiosqlite
import logging
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for Hippo bot."""
    
    def __init__(self, db_path: str = "hippo.db"):
        """Initialize database manager with path."""
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def initialize(self):
        """Initialize database connection and create tables."""
        self.connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        logger.info(f"Database initialized at {self.db_path}")
    
    async def close(self):
        """Close database connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")
    
    async def _create_tables(self):
        """Create all necessary tables."""
        # Users table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                waking_start_hour INTEGER DEFAULT 7,
                waking_start_minute INTEGER DEFAULT 0,
                waking_end_hour INTEGER DEFAULT 22,
                waking_end_minute INTEGER DEFAULT 0,
                reminder_interval_minutes INTEGER DEFAULT 60,
                theme TEXT DEFAULT 'bluey',
                timezone TEXT DEFAULT 'Asia/Singapore',
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Hydration events table (tracks water drinking confirmations)
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS hydration_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT CHECK(event_type IN ('confirmed', 'missed')),
                reminder_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Active reminders table (tracks pending reminders)
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS active_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reminder_id TEXT UNIQUE,
                message_id INTEGER,
                chat_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Achievements table (tracks earned achievements)
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_code TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, achievement_code)
            )
        """)
        
        await self.connection.commit()
        
        # Add timezone column if it doesn't exist (migration for existing databases)
        try:
            await self.connection.execute("""
                ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'Asia/Singapore'
            """)
            await self.connection.commit()
            logger.info("Added timezone column to users table")
        except Exception:
            # Column already exists, ignore the error
            pass
        
        logger.info("Database tables created/verified")
    
    # User operations
    async def create_user(self, user_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None) -> bool:
        """Create a new user record."""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
            await self.connection.commit()
            logger.info(f"Created/updated user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user record by ID."""
        async with self.connection.execute("""
            SELECT * FROM users WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    
    async def update_user_waking_hours(self, user_id: int, start_hour: int, 
                                     start_minute: int, end_hour: int, end_minute: int) -> bool:
        """Update user's waking hours."""
        try:
            await self.connection.execute("""
                UPDATE users SET waking_start_hour = ?, waking_start_minute = ?,
                               waking_end_hour = ?, waking_end_minute = ?
                WHERE user_id = ?
            """, (start_hour, start_minute, end_hour, end_minute, user_id))
            await self.connection.commit()
            logger.info(f"Updated waking hours for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating waking hours for user {user_id}: {e}")
            return False
    
    async def update_user_reminder_interval(self, user_id: int, interval_minutes: int) -> bool:
        """Update user's reminder interval."""
        try:
            await self.connection.execute("""
                UPDATE users SET reminder_interval_minutes = ? WHERE user_id = ?
            """, (interval_minutes, user_id))
            await self.connection.commit()
            logger.info(f"Updated reminder interval for user {user_id} to {interval_minutes} minutes")
            return True
        except Exception as e:
            logger.error(f"Error updating reminder interval for user {user_id}: {e}")
            return False
    
    async def update_user_timezone(self, user_id: int, timezone: str) -> bool:
        """Update user's timezone."""
        try:
            # Validate timezone
            import pytz
            pytz.timezone(timezone)  # This will raise exception if invalid
            
            await self.connection.execute("""
                UPDATE users SET timezone = ? WHERE user_id = ?
            """, (timezone, user_id))
            await self.connection.commit()
            logger.info(f"Updated timezone for user {user_id} to {timezone}")
            return True
        except Exception as e:
            logger.error(f"Error updating timezone for user {user_id}: {e}")
            return False
    
    async def update_user_theme(self, user_id: int, theme: str) -> bool:
        """Update user's theme."""
        try:
            await self.connection.execute("""
                UPDATE users SET theme = ? WHERE user_id = ?
            """, (theme, user_id))
            await self.connection.commit()
            logger.info(f"Updated theme for user {user_id} to {theme}")
            return True
        except Exception as e:
            logger.error(f"Error updating theme for user {user_id}: {e}")
            return False
    
    async def delete_user_completely(self, user_id: int) -> bool:
        """Delete a user and all their associated data completely."""
        try:
            # Delete in order to respect foreign key constraints
            # 1. Delete active reminders
            await self.connection.execute("""
                DELETE FROM active_reminders WHERE user_id = ?
            """, (user_id,))
            
            # 2. Delete hydration events
            await self.connection.execute("""
                DELETE FROM hydration_events WHERE user_id = ?
            """, (user_id,))
            
            # 3. Delete user record
            await self.connection.execute("""
                DELETE FROM users WHERE user_id = ?
            """, (user_id,))
            
            await self.connection.commit()
            logger.info(f"Completely deleted user {user_id} and all associated data")
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            await self.connection.rollback()
            return False
    
    # Hydration event operations
    async def record_hydration_event(self, user_id: int, event_type: str, reminder_id: str) -> bool:
        """Record a hydration event (confirmed or missed)."""
        try:
            await self.connection.execute("""
                INSERT INTO hydration_events (user_id, event_type, reminder_id)
                VALUES (?, ?, ?)
            """, (user_id, event_type, reminder_id))
            await self.connection.commit()
            logger.info(f"Recorded {event_type} hydration event for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error recording hydration event for user {user_id}: {e}")
            return False
    
    async def get_user_hydration_stats(self, user_id: int, days: int = 7) -> Dict[str, int]:
        """Get user's hydration statistics for the last N days."""
        try:
            async with self.connection.execute("""
                SELECT event_type, COUNT(*) as count
                FROM hydration_events
                WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
                GROUP BY event_type
            """.format(days), (user_id,)) as cursor:
                results = await cursor.fetchall()
                
            stats = {'confirmed': 0, 'missed': 0}
            for event_type, count in results:
                stats[event_type] = count
                
            return stats
        except Exception as e:
            logger.error(f"Error getting hydration stats for user {user_id}: {e}")
            return {'confirmed': 0, 'missed': 0}
    
    async def calculate_hydration_level(self, user_id: int) -> int:
        """Calculate current hydration level (0-5) based on rolling average of past 6 reminders."""
        try:
            # Get the last 6 hydration events (confirmed or missed) ordered by most recent
            async with self.connection.execute("""
                SELECT event_type FROM hydration_events
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 6
            """, (user_id,)) as cursor:
                recent_events = await cursor.fetchall()
            
            if not recent_events:
                return 2  # Default moderate level if no history
            
            # Extract event types from tuples
            event_types = [event_type for (event_type,) in recent_events]
            
            # If we have less than 6 total reminders, add placeholders
            # Half misses, half confirmations to start closer to 50%
            if len(event_types) < 6:
                missing_count = 6 - len(event_types)
                placeholders = []
                
                # Add alternating confirmed and missed events
                for i in range(missing_count):
                    if i % 2 == 0:
                        placeholders.append('missed')
                    else:
                        placeholders.append('confirmed')
                
                # Add placeholders to the end (older events)
                event_types.extend(placeholders)
            
            # Count confirmed events in the 6 events (real + placeholders)
            confirmed_count = sum(1 for event_type in event_types if event_type == 'confirmed')
            total_events = len(event_types)  # Should always be 6 now
            
            # Calculate ratio based on recent performance
            confirmed_ratio = confirmed_count / total_events
            
            # Map ratio to hydration level (0-5) with more granular steps
            if confirmed_ratio >= 0.85:  # 5-6 out of 6
                level = 5  # Perfect hydration
            elif confirmed_ratio >= 0.65:  # 4+ out of 6
                level = 4  # Great hydration
            elif confirmed_ratio >= 0.5:   # 3+ out of 6
                level = 3  # Good hydration
            elif confirmed_ratio >= 0.35:  # 2+ out of 6
                level = 2  # Moderate hydration
            elif confirmed_ratio >= 0.15:  # 1+ out of 6
                level = 1  # Low hydration
            else:  # 0 out of 6
                level = 0  # Dehydrated
            
            logger.debug(f"User {user_id} hydration level: {confirmed_count}/{total_events} confirmed = {confirmed_ratio:.2f} ratio = level {level}")
            return level
                
        except Exception as e:
            logger.error(f"Error calculating hydration level for user {user_id}: {e}")
            return 2  # Default moderate level on error
    
    # Active reminder operations
    async def create_active_reminder(self, user_id: int, reminder_id: str, 
                                   message_id: int, chat_id: int, expires_at: datetime) -> bool:
        """Create an active reminder record."""
        try:
            await self.connection.execute("""
                INSERT INTO active_reminders (user_id, reminder_id, message_id, chat_id, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, reminder_id, message_id, chat_id, expires_at.isoformat()))
            await self.connection.commit()
            logger.info(f"Created active reminder {reminder_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating active reminder for user {user_id}: {e}")
            return False
    
    async def remove_active_reminder(self, reminder_id: str) -> bool:
        """Remove an active reminder record."""
        try:
            await self.connection.execute("""
                DELETE FROM active_reminders WHERE reminder_id = ?
            """, (reminder_id,))
            await self.connection.commit()
            logger.info(f"Removed active reminder {reminder_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing active reminder {reminder_id}: {e}")
            return False
    
    async def get_expired_reminders(self) -> List[Dict[str, Any]]:
        """Get all expired reminders that need to be processed."""
        try:
            async with self.connection.execute("""
                SELECT * FROM active_reminders 
                WHERE expires_at <= datetime('now')
            """) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting expired reminders: {e}")
            return []
    
    async def expire_user_active_reminders(self, user_id: int) -> int:
        """Expire all active reminders for a user and record as missed events."""
        try:
            # First get all active reminders for this user with message details
            async with self.connection.execute("""
                SELECT reminder_id, message_id, chat_id FROM active_reminders 
                WHERE user_id = ?
            """, (user_id,)) as cursor:
                reminders = await cursor.fetchall()
            
            logger.debug(f"Found {len(reminders)} active reminders for user {user_id}")
            
            expired_count = 0
            expired_messages = []
            for (reminder_id, message_id, chat_id) in reminders:
                logger.debug(f"Expiring reminder {reminder_id}: message_id={message_id}, chat_id={chat_id}")
                # Record as missed event
                await self.record_hydration_event(user_id, 'missed', reminder_id)
                # Remove from active reminders
                await self.remove_active_reminder(reminder_id)
                # Store message details for editing
                expired_messages.append((message_id, chat_id))
                expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Expired {expired_count} active reminders for user {user_id}")
            
            return expired_count, expired_messages
            
        except Exception as e:
            logger.error(f"Error expiring reminders for user {user_id}: {e}")
            return 0, []
    
    # Achievement operations
    async def grant_achievement(self, user_id: int, achievement_code: str) -> bool:
        """Grant an achievement to a user."""
        try:
            await self.connection.execute("""
                INSERT OR IGNORE INTO user_achievements (user_id, achievement_code)
                VALUES (?, ?)
            """, (user_id, achievement_code))
            await self.connection.commit()
            
            # Check if this was actually a new achievement
            cursor = await self.connection.execute("""
                SELECT changes()
            """)
            changes = await cursor.fetchone()
            
            if changes[0] > 0:
                logger.info(f"Granted achievement {achievement_code} to user {user_id}")
                return True
            else:
                logger.debug(f"User {user_id} already has achievement {achievement_code}")
                return False
        except Exception as e:
            logger.error(f"Error granting achievement {achievement_code} to user {user_id}: {e}")
            return False
    
    async def get_user_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all achievements earned by a user."""
        try:
            async with self.connection.execute("""
                SELECT achievement_code, earned_at
                FROM user_achievements
                WHERE user_id = ?
                ORDER BY earned_at DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [{'code': code, 'earned_at': earned_at} for code, earned_at in rows]
        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {e}")
            return []
    
    async def has_achievement(self, user_id: int, achievement_code: str) -> bool:
        """Check if a user has a specific achievement."""
        try:
            async with self.connection.execute("""
                SELECT 1 FROM user_achievements
                WHERE user_id = ? AND achievement_code = ?
            """, (user_id, achievement_code)) as cursor:
                result = await cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking achievement {achievement_code} for user {user_id}: {e}")
            return False
    
    async def get_achievement_count(self, user_id: int) -> int:
        """Get the total number of achievements earned by a user."""
        try:
            async with self.connection.execute("""
                SELECT COUNT(*) FROM user_achievements
                WHERE user_id = ?
            """, (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting achievements for user {user_id}: {e}")
            return 0
    
    async def get_total_confirmations(self, user_id: int) -> int:
        """Get total number of water confirmations for a user."""
        try:
            async with self.connection.execute("""
                SELECT COUNT(*) FROM hydration_events
                WHERE user_id = ? AND event_type = 'confirmed'
            """, (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting confirmations for user {user_id}: {e}")
            return 0