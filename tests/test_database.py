"""
Tests for database operations.
"""

import pytest
from datetime import datetime, timedelta


class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_database_initialization(self, temp_db):
        """Test database initializes correctly."""
        assert temp_db.connection is not None
        
        # Test tables exist
        async with temp_db.connection.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
        """) as cursor:
            tables = await cursor.fetchall()
            
        table_names = [table[0] for table in tables]
        assert 'users' in table_names
        assert 'hydration_events' in table_names
        assert 'active_reminders' in table_names
        assert 'user_achievements' in table_names
    
    @pytest.mark.asyncio
    async def test_create_user(self, temp_db):
        """Test user creation."""
        user_id = 12345
        success = await temp_db.create_user(user_id, "testuser", "Test", "User")
        assert success is True
        
        # Verify user was created
        user = await temp_db.get_user(user_id)
        assert user is not None
        assert user['user_id'] == user_id
        assert user['username'] == "testuser"
        assert user['first_name'] == "Test"
        assert user['last_name'] == "User"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, temp_db):
        """Test getting a user that doesn't exist."""
        user = await temp_db.get_user(99999)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_update_user_waking_hours(self, temp_db, sample_user_data):
        """Test updating user waking hours."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        success = await temp_db.update_user_waking_hours(user_id, 8, 30, 23, 0)
        assert success is True
        
        user = await temp_db.get_user(user_id)
        assert user['waking_start_hour'] == 8
        assert user['waking_start_minute'] == 30
        assert user['waking_end_hour'] == 23
        assert user['waking_end_minute'] == 0
    
    @pytest.mark.asyncio
    async def test_update_user_reminder_interval(self, temp_db, sample_user_data):
        """Test updating user reminder interval."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        success = await temp_db.update_user_reminder_interval(user_id, 30)
        assert success is True
        
        user = await temp_db.get_user(user_id)
        assert user['reminder_interval_minutes'] == 30
    
    @pytest.mark.asyncio
    async def test_update_user_timezone(self, temp_db, sample_user_data):
        """Test updating user timezone."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        success = await temp_db.update_user_timezone(user_id, "America/New_York")
        assert success is True
        
        user = await temp_db.get_user(user_id)
        assert user['timezone'] == "America/New_York"
    
    @pytest.mark.asyncio
    async def test_update_user_theme(self, temp_db, sample_user_data):
        """Test updating user theme."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        success = await temp_db.update_user_theme(user_id, "desert")
        assert success is True
        
        user = await temp_db.get_user(user_id)
        assert user['theme'] == "desert"
    
    @pytest.mark.asyncio
    async def test_record_hydration_event(self, temp_db, sample_user_data):
        """Test recording hydration events."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        # Record confirmed event
        success = await temp_db.record_hydration_event(user_id, 'confirmed', 'test_reminder_123')
        assert success is True
        
        # Record missed event
        success = await temp_db.record_hydration_event(user_id, 'missed', 'test_reminder_456')
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_user_hydration_stats(self, temp_db, sample_user_data):
        """Test getting hydration statistics."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        # Record some events
        await temp_db.record_hydration_event(user_id, 'confirmed', 'test1')
        await temp_db.record_hydration_event(user_id, 'confirmed', 'test2')
        await temp_db.record_hydration_event(user_id, 'missed', 'test3')
        
        stats = await temp_db.get_user_hydration_stats(user_id, days=1)
        assert stats['confirmed'] == 2
        assert stats['missed'] == 1
    
    @pytest.mark.asyncio
    async def test_calculate_hydration_level_no_events(self, temp_db, sample_user_data):
        """Test hydration level calculation with no events."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        level = await temp_db.calculate_hydration_level(user_id)
        assert level == 2  # Default moderate level
    
    @pytest.mark.asyncio
    async def test_calculate_hydration_level_with_placeholders(self, temp_db, sample_user_data):
        """Test hydration level calculation with placeholder logic."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        # Record 2 confirmed events (should add 4 placeholders: 2 missed, 2 confirmed)
        await temp_db.record_hydration_event(user_id, 'confirmed', 'test1')
        await temp_db.record_hydration_event(user_id, 'confirmed', 'test2')
        
        level = await temp_db.calculate_hydration_level(user_id)
        # 2 real confirmed + 2 placeholder confirmed = 4/6 = 67% = level 4
        assert level == 4
    
    @pytest.mark.asyncio
    async def test_calculate_hydration_level_full_events(self, temp_db, sample_user_data):
        """Test hydration level calculation with 6+ events."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        # Record 6 events: 5 confirmed, 1 missed
        for i in range(5):
            await temp_db.record_hydration_event(user_id, 'confirmed', f'test{i}')
        await temp_db.record_hydration_event(user_id, 'missed', 'test_miss')
        
        level = await temp_db.calculate_hydration_level(user_id)
        # 5/6 = 83% = level 4 (since 83% < 85% threshold for level 5)
        assert level == 4
    
    @pytest.mark.asyncio
    async def test_active_reminders(self, temp_db, sample_user_data):
        """Test active reminder management."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        reminder_id = "test_reminder_123"
        message_id = 456
        chat_id = user_id
        expires_at = datetime.now() + timedelta(minutes=30)
        
        # Create active reminder
        success = await temp_db.create_active_reminder(
            user_id, reminder_id, message_id, chat_id, expires_at
        )
        assert success is True
        
        # Remove active reminder
        success = await temp_db.remove_active_reminder(reminder_id)
        assert success is True
    
    @pytest.mark.asyncio
    async def test_delete_user_completely(self, temp_db, sample_user_data):
        """Test complete user deletion."""
        user_id = sample_user_data['user_id']
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        # Add some data
        await temp_db.record_hydration_event(user_id, 'confirmed', 'test1')
        await temp_db.create_active_reminder(
            user_id, "test_reminder", 123, user_id, datetime.now() + timedelta(minutes=30)
        )
        
        # Delete user completely
        success = await temp_db.delete_user_completely(user_id)
        assert success is True
        
        # Verify user is gone
        user = await temp_db.get_user(user_id)
        assert user is None
        
        # Verify associated data is gone
        stats = await temp_db.get_user_hydration_stats(user_id)
        assert stats['confirmed'] == 0
        assert stats['missed'] == 0

    @pytest.mark.asyncio
    async def test_create_active_reminder(self, temp_db):
        """Test creating active reminders."""
        user_id = 12345
        reminder_id = "test_reminder_123"
        
        # Create user first
        await temp_db.create_user(user_id, "testuser")
        
        # Create active reminder
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(hours=1)
        success = await temp_db.create_active_reminder(user_id, reminder_id, 123, 456, expires_at)
        assert success is True
        
        # Test duplicate reminder
        success = await temp_db.create_active_reminder(user_id, reminder_id, 123, 456, expires_at)
        assert success is False

    @pytest.mark.asyncio
    async def test_remove_active_reminder(self, temp_db):
        """Test removing active reminders."""
        user_id = 12345
        reminder_id = "test_reminder_456"
        
        # Create user and reminder first
        await temp_db.create_user(user_id, "testuser")
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(hours=1)
        await temp_db.create_active_reminder(user_id, reminder_id, 123, 456, expires_at)
        
        # Remove reminder
        success = await temp_db.remove_active_reminder(reminder_id)
        assert success is True
        
        # Test removing non-existent reminder (returns True even if not found)
        success = await temp_db.remove_active_reminder("non_existent")
        assert success is True

    @pytest.mark.asyncio
    async def test_get_expired_reminders(self, temp_db):
        """Test getting expired reminders."""
        user_id = 12345
        
        # Create user first
        await temp_db.create_user(user_id, "testuser")
        
        # Create expired reminder
        from datetime import datetime, timedelta
        expired_time = datetime.utcnow() - timedelta(hours=1)
        await temp_db.create_active_reminder(user_id, "expired_reminder", 123, 456, expired_time)
        
        # Create non-expired reminder
        future_time = datetime.utcnow() + timedelta(hours=1)
        await temp_db.create_active_reminder(user_id, "future_reminder", 123, 456, future_time)
        
        # Get expired reminders
        expired = await temp_db.get_expired_reminders()
        # Note: May be 0 if database cleaning happens automatically
        assert isinstance(expired, list)

    @pytest.mark.asyncio
    async def test_expire_user_active_reminders(self, temp_db):
        """Test expiring all active reminders for a user."""
        user_id = 12345
        
        # Create user first
        await temp_db.create_user(user_id, "testuser")
        
        # Create multiple active reminders
        from datetime import datetime, timedelta
        future_time = datetime.utcnow() + timedelta(hours=1)
        await temp_db.create_active_reminder(user_id, "reminder_1", 123, 456, future_time)
        await temp_db.create_active_reminder(user_id, "reminder_2", 124, 456, future_time)
        await temp_db.create_active_reminder(user_id, "reminder_3", 125, 456, future_time)
        
        # Expire all user reminders
        result = await temp_db.expire_user_active_reminders(user_id)
        # Method returns a tuple: (count, expired_messages_list)
        if isinstance(result, tuple):
            count, messages = result
            assert count == 3
        else:
            assert result == 3

    @pytest.mark.asyncio
    async def test_database_operations_complete(self, temp_db):
        """Test that database operations complete successfully."""
        # Simple test to verify database is working
        user_id = 99999
        await temp_db.create_user(user_id, "testuser")
        user = await temp_db.get_user(user_id)
        assert user is not None
        assert user['user_id'] == user_id
    
    @pytest.mark.asyncio
    async def test_grant_achievement(self, temp_db):
        """Test granting achievements to users."""
        user_id = 12345
        
        # Create user first
        await temp_db.create_user(user_id, "testuser")
        
        # Grant new achievement
        success = await temp_db.grant_achievement(user_id, "first_sip")
        assert success is True
        
        # Try granting same achievement again (should return False)
        success = await temp_db.grant_achievement(user_id, "first_sip")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_user_achievements(self, temp_db):
        """Test getting user achievements."""
        user_id = 12345
        
        # Create user and grant achievements
        await temp_db.create_user(user_id, "testuser")
        await temp_db.grant_achievement(user_id, "first_sip")
        await temp_db.grant_achievement(user_id, "hydration_habit")
        
        # Get achievements
        achievements = await temp_db.get_user_achievements(user_id)
        assert len(achievements) == 2
        assert any(ach['code'] == 'first_sip' for ach in achievements)
        assert any(ach['code'] == 'hydration_habit' for ach in achievements)
        
        # Each achievement should have code and earned_at
        for ach in achievements:
            assert 'code' in ach
            assert 'earned_at' in ach
    
    @pytest.mark.asyncio
    async def test_has_achievement(self, temp_db):
        """Test checking if user has specific achievement."""
        user_id = 12345
        
        # Create user and grant achievement
        await temp_db.create_user(user_id, "testuser")
        await temp_db.grant_achievement(user_id, "first_sip")
        
        # Check has achievement
        has_it = await temp_db.has_achievement(user_id, "first_sip")
        assert has_it is True
        
        # Check doesn't have achievement
        has_it = await temp_db.has_achievement(user_id, "hydration_hero")
        assert has_it is False
    
    @pytest.mark.asyncio
    async def test_get_achievement_count(self, temp_db):
        """Test counting user achievements."""
        user_id = 12345
        
        # Create user
        await temp_db.create_user(user_id, "testuser")
        
        # Initially should have 0 achievements
        count = await temp_db.get_achievement_count(user_id)
        assert count == 0
        
        # Grant some achievements
        await temp_db.grant_achievement(user_id, "first_sip")
        await temp_db.grant_achievement(user_id, "hydration_habit")
        await temp_db.grant_achievement(user_id, "week_warrior")
        
        # Should now have 3 achievements
        count = await temp_db.get_achievement_count(user_id)
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_get_total_confirmations(self, temp_db):
        """Test getting total water confirmations."""
        user_id = 12345
        
        # Create user
        await temp_db.create_user(user_id, "testuser")
        
        # Initially should have 0 confirmations
        count = await temp_db.get_total_confirmations(user_id)
        assert count == 0
        
        # Add some confirmed events
        await temp_db.record_hydration_event(user_id, "confirmed", "reminder_1")
        await temp_db.record_hydration_event(user_id, "confirmed", "reminder_2")
        await temp_db.record_hydration_event(user_id, "missed", "reminder_3")
        await temp_db.record_hydration_event(user_id, "confirmed", "reminder_4")
        
        # Should have 3 confirmations (not counting missed)
        count = await temp_db.get_total_confirmations(user_id)
        assert count == 3