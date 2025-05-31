#!/usr/bin/env python3
"""
Database Debug Script for Hippo Bot

This script dumps useful debug information from the Hippo Bot database
for troubleshooting and monitoring purposes.
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def format_timestamp(ts_str):
    """Format timestamp string for better readability."""
    if not ts_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts_str

def get_database_path():
    """Get the database path from environment or default."""
    return os.getenv('DATABASE_PATH', 'hippo.db')

def connect_to_database():
    """Connect to the database."""
    db_path = get_database_path()
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

def dump_users(conn):
    """Dump user information."""
    print("👥 USERS")
    print("=" * 80)
    
    cursor = conn.execute("""
        SELECT user_id, username, first_name, last_name, created_at,
               waking_start_hour, waking_start_minute, waking_end_hour, waking_end_minute,
               reminder_interval_minutes, theme, timezone, is_active
        FROM users
        ORDER BY created_at DESC
    """)
    
    users = cursor.fetchall()
    if not users:
        print("No users found.")
        return
    
    for user in users:
        waking_schedule = f"{user['waking_start_hour']:02d}:{user['waking_start_minute']:02d} - {user['waking_end_hour']:02d}:{user['waking_end_minute']:02d}"
        if user['waking_start_hour'] == 0 and user['waking_end_hour'] == 23:
            waking_schedule += " (24/7 mode)"
        
        print(f"User ID: {user['user_id']}")
        print(f"  Name: {user['first_name']} {user['last_name'] or ''} (@{user['username'] or 'no_username'})")
        print(f"  Created: {format_timestamp(user['created_at'])}")
        print(f"  Status: {'🟢 Active' if user['is_active'] else '🔴 Inactive'}")
        print(f"  Waking Hours: {waking_schedule}")
        print(f"  Reminder Interval: {user['reminder_interval_minutes']} minutes")
        print(f"  Theme: {user['theme']}")
        print(f"  Timezone: {user['timezone']}")
        print()

def dump_recent_events(conn, days=7):
    """Dump recent hydration events."""
    print(f"💧 RECENT HYDRATION EVENTS (Last {days} days)")
    print("=" * 80)
    
    cursor = conn.execute("""
        SELECT he.*, u.first_name, u.username
        FROM hydration_events he
        JOIN users u ON he.user_id = u.user_id
        WHERE he.created_at >= datetime('now', '-{} days')
        ORDER BY he.created_at DESC
        LIMIT 50
    """.format(days))
    
    events = cursor.fetchall()
    if not events:
        print("No recent events found.")
        return
    
    for event in events:
        status_emoji = "✅" if event['event_type'] == 'confirmed' else "❌"
        user_name = f"{event['first_name']} (@{event['username'] or 'no_username'})"
        
        print(f"{status_emoji} {event['event_type'].upper()} - {user_name}")
        print(f"    Time: {format_timestamp(event['created_at'])}")
        print(f"    Reminder ID: {event['reminder_id']}")
        print()

def dump_active_reminders(conn):
    """Dump currently active reminders."""
    print("⏰ ACTIVE REMINDERS")
    print("=" * 80)
    
    cursor = conn.execute("""
        SELECT ar.*, u.first_name, u.username
        FROM active_reminders ar
        JOIN users u ON ar.user_id = u.user_id
        ORDER BY ar.created_at DESC
    """)
    
    reminders = cursor.fetchall()
    if not reminders:
        print("No active reminders found.")
        return
    
    for reminder in reminders:
        user_name = f"{reminder['first_name']} (@{reminder['username'] or 'no_username'})"
        expires_at = format_timestamp(reminder['expires_at'])
        
        # Check if expired
        try:
            exp_dt = datetime.fromisoformat(reminder['expires_at'])
            now = datetime.now()
            is_expired = exp_dt < now
            status = "🔴 EXPIRED" if is_expired else "🟢 ACTIVE"
        except:
            status = "❓ UNKNOWN"
        
        print(f"{status} - {user_name}")
        print(f"    Created: {format_timestamp(reminder['created_at'])}")
        print(f"    Expires: {expires_at}")
        print(f"    Message ID: {reminder['message_id']} (Chat: {reminder['chat_id']})")
        print(f"    Reminder ID: {reminder['reminder_id']}")
        print()

def dump_user_stats(conn):
    """Dump user statistics."""
    print("📊 USER STATISTICS")
    print("=" * 80)
    
    cursor = conn.execute("""
        SELECT u.user_id, u.first_name, u.username,
               COUNT(CASE WHEN he.event_type = 'confirmed' THEN 1 END) as confirmed_count,
               COUNT(CASE WHEN he.event_type = 'missed' THEN 1 END) as missed_count,
               COUNT(he.id) as total_events,
               MAX(he.created_at) as last_event
        FROM users u
        LEFT JOIN hydration_events he ON u.user_id = he.user_id
        WHERE he.created_at >= datetime('now', '-7 days') OR he.created_at IS NULL
        GROUP BY u.user_id, u.first_name, u.username
        ORDER BY total_events DESC
    """)
    
    stats = cursor.fetchall()
    
    for stat in stats:
        user_name = f"{stat['first_name']} (@{stat['username'] or 'no_username'})"
        total = stat['total_events'] or 0
        confirmed = stat['confirmed_count'] or 0
        missed = stat['missed_count'] or 0
        success_rate = (confirmed / total * 100) if total > 0 else 0
        
        print(f"User: {user_name} (ID: {stat['user_id']})")
        print(f"  Last 7 days: {confirmed}✅ confirmed, {missed}❌ missed ({success_rate:.1f}% success rate)")
        print(f"  Last event: {format_timestamp(stat['last_event'])}")
        print()

def dump_database_info(conn):
    """Dump general database information."""
    print("🗄️ DATABASE INFORMATION")
    print("=" * 80)
    
    db_path = get_database_path()
    print(f"Database Path: {db_path}")
    
    try:
        stat = os.stat(db_path)
        size_kb = stat.st_size / 1024
        modified = datetime.fromtimestamp(stat.st_mtime)
        print(f"File Size: {size_kb:.1f} KB")
        print(f"Last Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
    except:
        print("Could not get file stats")
    
    # Table counts
    tables = ['users', 'hydration_events', 'active_reminders']
    for table in tables:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table.title()}: {count} records")
        except Exception as e:
            print(f"{table.title()}: Error - {e}")
    
    print()

def calculate_hydration_levels(conn):
    """Calculate and display current hydration levels for all users."""
    print("🌊 CURRENT HYDRATION LEVELS")
    print("=" * 80)
    
    level_descriptions = [
        "😵 Dehydrated",
        "😟 Low hydration", 
        "😐 Moderate hydration",
        "😊 Good hydration",
        "😄 Great hydration",
        "🤩 Perfect hydration"
    ]
    
    cursor = conn.execute("SELECT user_id, first_name, username FROM users WHERE is_active = 1")
    users = cursor.fetchall()
    
    for user in users:
        user_id = user['user_id']
        user_name = f"{user['first_name']} (@{user['username'] or 'no_username'})"
        
        # Get recent events (last 24 hours)
        cursor = conn.execute("""
            SELECT event_type FROM hydration_events 
            WHERE user_id = ? AND created_at >= datetime('now', '-1 day')
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        
        recent_events = cursor.fetchall()
        
        # Calculate hydration level (simplified version of the bot's logic)
        if not recent_events:
            level = 0
        else:
            confirmed_count = sum(1 for event in recent_events if event['event_type'] == 'confirmed')
            total_count = len(recent_events)
            
            if total_count == 0:
                level = 0
            else:
                ratio = confirmed_count / total_count
                if ratio >= 0.9:
                    level = 5
                elif ratio >= 0.8:
                    level = 4
                elif ratio >= 0.6:
                    level = 3
                elif ratio >= 0.4:
                    level = 2
                elif ratio >= 0.2:
                    level = 1
                else:
                    level = 0
        
        print(f"{user_name}: {level_descriptions[level]} (Level {level})")
        if recent_events:
            print(f"  Recent events: {len(recent_events)} in last 24h ({sum(1 for e in recent_events if e['event_type'] == 'confirmed')} confirmed)")
        else:
            print("  No recent events")
        print()

def main():
    """Main function."""
    print("🦛 Hippo Bot Database Debug Tool")
    print("=" * 80)
    print()
    
    conn = connect_to_database()
    
    try:
        dump_database_info(conn)
        dump_users(conn)
        dump_user_stats(conn)
        calculate_hydration_levels(conn)
        dump_active_reminders(conn)
        dump_recent_events(conn)
        
        print("✅ Debug dump completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during debug dump: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()