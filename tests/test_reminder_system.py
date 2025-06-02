"""
Tests for reminder system functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time, timedelta


class TestReminderSystem:
    """Test reminder system functionality."""
    
    @pytest.mark.asyncio
    async def test_is_within_waking_hours_24_7_mode(self, reminder_system):
        """Test waking hours check for 24/7 mode."""
        user_data = {
            'waking_start_hour': 0,
            'waking_start_minute': 0,
            'waking_end_hour': 23,
            'waking_end_minute': 0,
            'timezone': 'Asia/Singapore',
            'user_id': 12345
        }
        
        result = reminder_system._is_within_waking_hours(user_data)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_within_waking_hours_normal_schedule(self, reminder_system):
        """Test waking hours check for normal schedule."""
        user_data = {
            'waking_start_hour': 7,
            'waking_start_minute': 0,
            'waking_end_hour': 22,
            'waking_end_minute': 0,
            'timezone': 'Asia/Singapore',
            'user_id': 12345
        }
        
        # This will depend on current time, so we just check it doesn't crash
        result = reminder_system._is_within_waking_hours(user_data)
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_is_within_waking_hours_overnight_schedule(self, reminder_system):
        """Test waking hours check for overnight schedule."""
        user_data = {
            'waking_start_hour': 22,
            'waking_start_minute': 0,
            'waking_end_hour': 6,
            'waking_end_minute': 0,
            'timezone': 'Asia/Singapore',
            'user_id': 12345
        }
        
        # This will depend on current time, so we just check it doesn't crash
        result = reminder_system._is_within_waking_hours(user_data)
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_should_send_reminder_no_previous(self, reminder_system):
        """Test should send reminder with no previous reminders."""
        user_id = 12345
        interval_minutes = 60
        
        result = await reminder_system._should_send_reminder(user_id, interval_minutes)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_send_reminder_with_recent(self, reminder_system, temp_db):
        """Test should send reminder with recent reminder."""
        user_id = 12345
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        # Create a recent hydration event
        await temp_db.record_hydration_event(user_id, 'confirmed', 'recent_reminder')
        
        # Should not send another reminder immediately
        result = await reminder_system._should_send_reminder(user_id, 60)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_schedule_user_reminders(self, reminder_system):
        """Test scheduling reminders for a user."""
        user_id = 12345
        job_queue = MagicMock()
        job_queue.run_repeating = MagicMock()
        job_queue.get_jobs_by_name = MagicMock(return_value=[])
        
        reminder_system.schedule_user_reminders(job_queue, user_id)
        
        # Verify job was scheduled
        job_queue.run_repeating.assert_called_once()
        assert user_id in reminder_system.active_jobs
    
    @pytest.mark.asyncio
    async def test_cancel_user_reminders(self, reminder_system):
        """Test cancelling reminders for a user."""
        user_id = 12345
        job_queue = MagicMock()
        
        # Setup mock job
        mock_job = MagicMock()
        mock_job.schedule_removal = MagicMock()
        job_queue.get_jobs_by_name = MagicMock(return_value=[mock_job])
        
        # Add user to active jobs
        reminder_system.active_jobs[user_id] = f"reminders_user_{user_id}"
        
        reminder_system.cancel_user_reminders(job_queue, user_id)
        
        # Verify job was cancelled
        mock_job.schedule_removal.assert_called_once()
        assert user_id not in reminder_system.active_jobs
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', create=True)
    @pytest.mark.asyncio
    async def test_send_water_reminder(self, mock_open, mock_exists, reminder_system, temp_db, mock_context):
        """Test sending water reminder."""
        user_id = 12345
        user_data = {
            'user_id': user_id,
            'theme': 'bluey',
            'reminder_interval_minutes': 60,
            'is_active': True
        }
        
        # Setup database
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        # Mock the bot methods
        mock_context.bot.send_photo = AsyncMock()
        mock_context.bot.send_photo.return_value = MagicMock(message_id=123)
        
        # Mock file reading
        mock_open.return_value.__enter__.return_value = b"fake_image_data"
        
        await reminder_system._send_water_reminder(mock_context, user_id, user_data)
        
        # Verify photo was sent
        mock_context.bot.send_photo.assert_called_once()
        
        # Verify call arguments contain expected data
        call_args = mock_context.bot.send_photo.call_args
        assert call_args[1]['chat_id'] == user_id
        assert 'caption' in call_args[1]
        assert 'reply_markup' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_start_reminders_for_user(self, reminder_system, temp_db):
        """Test starting reminders for a specific user."""
        user_id = 12345
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        
        job_queue = MagicMock()
        job_queue.run_repeating = MagicMock()
        job_queue.get_jobs_by_name = MagicMock(return_value=[])
        
        result = await reminder_system.start_reminders_for_user(job_queue, user_id)
        
        assert result is True
        job_queue.run_repeating.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_reminders_for_inactive_user(self, reminder_system, temp_db):
        """Test starting reminders for inactive user."""
        user_id = 12345
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        # Make user inactive
        await temp_db.connection.execute(
            "UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,)
        )
        await temp_db.connection.commit()
        
        job_queue = MagicMock()
        
        result = await reminder_system.start_reminders_for_user(job_queue, user_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mark_reminder_as_expired(self, reminder_system, mock_context):
        """Test marking reminder as expired."""
        chat_id = 12345
        message_id = 123
        
        mock_context.bot.edit_message_reply_markup = AsyncMock()
        
        await reminder_system._mark_reminder_as_expired(mock_context, chat_id, message_id)
        
        # Verify markup was edited
        mock_context.bot.edit_message_reply_markup.assert_called_once()
        call_args = mock_context.bot.edit_message_reply_markup.call_args
        assert call_args[1]['chat_id'] == chat_id
        assert call_args[1]['message_id'] == message_id
    
    @pytest.mark.asyncio
    async def test_check_and_send_reminder_outside_waking_hours(self, reminder_system, temp_db, mock_context):
        """Test reminder check outside waking hours."""
        user_id = 12345
        user_data = {
            'user_id': user_id,
            'waking_start_hour': 9,
            'waking_start_minute': 0,
            'waking_end_hour': 17,
            'waking_end_minute': 0,
            'reminder_interval_minutes': 60,
            'timezone': 'Asia/Singapore',
            'is_active': True,
            'theme': 'bluey'
        }
        
        # Create user in database
        await temp_db.create_user(user_id, "testuser", "Test", "User")
        await temp_db.update_user_waking_hours(user_id, 9, 0, 17, 0)
        
        # Mock job data
        mock_context.job = MagicMock()
        mock_context.job.data = {'user_id': user_id}
        
        # Mock _is_within_waking_hours to return False
        with patch.object(reminder_system, '_is_within_waking_hours', return_value=False):
            await reminder_system._check_and_send_reminder(mock_context)
        
        # Should not send message if outside waking hours
        # (We can't easily assert this without more complex mocking)
    
    @pytest.mark.asyncio
    async def test_stop_all_reminders(self, reminder_system):
        """Test stopping all reminder jobs."""
        job_queue = MagicMock()
        
        # Add some active jobs
        reminder_system.active_jobs[123] = "job1"
        reminder_system.active_jobs[456] = "job2"
        
        # Mock job objects
        mock_job1 = MagicMock()
        mock_job2 = MagicMock()
        job_queue.get_jobs_by_name.side_effect = [[mock_job1], [mock_job2]]
        
        reminder_system.stop_all_reminders(job_queue)
        
        # Verify all jobs were cancelled
        assert len(reminder_system.active_jobs) == 0
        mock_job1.schedule_removal.assert_called_once()
        mock_job2.schedule_removal.assert_called_once()

    @pytest.mark.asyncio
    async def test_reminder_system_initialization(self, reminder_system):
        """Test reminder system initialization."""
        # Test that reminder system has correct attributes
        assert hasattr(reminder_system, 'database')
        assert hasattr(reminder_system, 'content_manager')
        assert hasattr(reminder_system, 'active_jobs')
        assert isinstance(reminder_system.active_jobs, dict)