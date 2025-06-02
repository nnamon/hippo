"""
Tests for bot command handlers.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from src.bot.hippo_bot import HippoBot


class TestBotCommands:
    """Test bot command handlers."""
    
    @pytest.mark.asyncio
    async def test_start_command_new_user(self, hippo_bot, mock_update, mock_context):
        """Test /start command for new user."""
        # Import here to avoid circular imports
        from src.bot.hippo_bot import HippoBot
        
        user_id = mock_update.effective_user.id
        
        # Mock the update to have a reply method
        mock_update.message.reply_text = AsyncMock()
        
        # Test start command
        await hippo_bot.start_command(mock_update, mock_context)
        
        # Verify user was created
        user = await hippo_bot.database.get_user(user_id)
        assert user is not None
        assert user['user_id'] == user_id
        
        # Verify welcome message was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Welcome to Hippo" in args[0]
    
    @pytest.mark.asyncio
    async def test_start_command_existing_user(self, hippo_bot, mock_update, mock_context, sample_user_data):
        """Test /start command for existing user."""
        user_id = mock_update.effective_user.id
        
        # Create user first
        await hippo_bot.database.create_user(
            user_id, 
            sample_user_data['username'],
            sample_user_data['first_name'],
            sample_user_data['last_name']
        )
        
        mock_update.message.reply_text = AsyncMock()
        
        # Test start command
        await hippo_bot.start_command(mock_update, mock_context)
        
        # Verify welcome back message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Welcome to Hippo" in args[0]
    
    @pytest.mark.asyncio
    async def test_help_command(self, hippo_bot, mock_update, mock_context):
        """Test /help command."""
        mock_update.message.reply_text = AsyncMock()
        
        await hippo_bot.help_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "/start" in args[0]
        assert "/setup" in args[0]
        assert "/stats" in args[0]
    
    @pytest.mark.asyncio
    async def test_stats_command_no_user(self, hippo_bot, mock_update, mock_context):
        """Test /stats command for non-existent user."""
        mock_update.message.reply_text = AsyncMock()
        
        await hippo_bot.stats_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Hydration Stats" in args[0]
    
    @pytest.mark.asyncio
    async def test_stats_command_with_user(self, hippo_bot, mock_update, mock_context, sample_user_data):
        """Test /stats command for existing user."""
        user_id = mock_update.effective_user.id
        
        # Create user and add some hydration data
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        await hippo_bot.database.record_hydration_event(user_id, 'confirmed', 'test1')
        await hippo_bot.database.record_hydration_event(user_id, 'missed', 'test2')
        
        mock_update.message.reply_text = AsyncMock()
        
        await hippo_bot.stats_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Hydration Stats" in args[0]
        assert "success rate" in args[0].lower()
    
    @pytest.mark.asyncio
    async def test_setup_command(self, hippo_bot, mock_update, mock_context):
        """Test /setup command."""
        user_id = mock_update.effective_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_update.message.reply_text = AsyncMock()
        
        await hippo_bot.setup_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Setup Your Hippo Bot" in args[0]
        assert kwargs.get('reply_markup') is not None
    
    @pytest.mark.asyncio
    async def test_poem_command(self, hippo_bot, mock_update, mock_context):
        """Test /poem command with hydration level and image."""
        user_id = mock_update.effective_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        # Mock reply_photo method
        mock_update.message.reply_photo = AsyncMock()
        
        # Mock open function for image file
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = MagicMock()
            
            await hippo_bot.poem_command(mock_update, mock_context)
        
        # Verify image was sent with poem
        mock_update.message.reply_photo.assert_called_once()
        args, kwargs = mock_update.message.reply_photo.call_args
        
        # Check that caption contains poem and hydration status
        caption = kwargs.get('caption', '')
        assert "Here's a water reminder poem for you:" in caption
        assert "Current Hydration:" in caption
        assert "Remember to stay hydrated!" in caption

    @pytest.mark.asyncio
    async def test_quote_command(self, hippo_bot, mock_update, mock_context):
        """Test /quote command with hydration level and image."""
        user_id = mock_update.effective_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        # Mock reply_photo method
        mock_update.message.reply_photo = AsyncMock()
        
        # Mock open function for image file
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = MagicMock()
            
            await hippo_bot.quote_command(mock_update, mock_context)
        
        # Verify image was sent with quote
        mock_update.message.reply_photo.assert_called_once()
        args, kwargs = mock_update.message.reply_photo.call_args
        
        # Check that caption contains quote and hydration status
        caption = kwargs.get('caption', '')
        assert "Here's an inspirational quote for you:" in caption
        assert "Current Hydration:" in caption
        assert "Stay inspired and stay hydrated!" in caption


class TestCallbackHandlers:
    """Test callback query handlers."""
    
    @pytest.mark.asyncio
    async def test_water_confirmation_callback(self, hippo_bot, mock_callback_query, mock_context, sample_user_data):
        """Test water confirmation callback."""
        user_id = mock_callback_query.from_user.id
        reminder_id = "test_reminder_123"
        
        # Setup user and active reminder
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        await hippo_bot.database.create_active_reminder(
            user_id, reminder_id, 123, user_id, 
            datetime.now() + timedelta(minutes=30)
        )
        
        # Set callback data
        mock_callback_query.data = f"confirm_water_{reminder_id}"
        
        # Mock message to have photo (which triggers new image update behavior)
        mock_callback_query.message.photo = [MagicMock()]  # Mock photo array
        mock_callback_query.edit_message_media = AsyncMock()
        
        await hippo_bot._handle_water_confirmation(mock_callback_query)
        
        # Verify hydration event was recorded
        stats = await hippo_bot.database.get_user_hydration_stats(user_id)
        assert stats['confirmed'] == 1
        
        # Verify either the new image update behavior (edit_message_media) or fallback behavior was called
        message_was_updated = (
            mock_callback_query.edit_message_media.called
        ) or (
            mock_callback_query.edit_message_caption.called or mock_callback_query.edit_message_text.called
        )
        assert message_was_updated
    
    @pytest.mark.asyncio
    async def test_setup_timezone_callback(self, hippo_bot, mock_callback_query, mock_context):
        """Test timezone setup callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "timezone_America/New_York"
        
        await hippo_bot._handle_timezone_selection(mock_callback_query)
        
        # Verify timezone was updated
        user = await hippo_bot.database.get_user(user_id)
        assert user['timezone'] == "America/New_York"
        
        # Verify response message
        mock_callback_query.edit_message_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_theme_selection_callback(self, hippo_bot, mock_callback_query, mock_context):
        """Test theme selection callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "theme_desert"
        
        await hippo_bot._handle_theme_selection(mock_callback_query)
        
        # Verify theme was updated
        user = await hippo_bot.database.get_user(user_id)
        assert user['theme'] == "desert"
        
        # Verify response message
        mock_callback_query.edit_message_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_waking_hours_selection(self, hippo_bot, mock_callback_query, mock_context):
        """Test waking hours selection callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "waking_7_22"
        
        await hippo_bot._handle_waking_hours_selection(mock_callback_query)
        
        # Verify waking hours were updated
        user = await hippo_bot.database.get_user(user_id)
        assert user['waking_start_hour'] == 7
        assert user['waking_end_hour'] == 22
        
        # Verify response message
        mock_callback_query.edit_message_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reminder_interval_selection(self, hippo_bot, mock_callback_query, mock_context):
        """Test reminder interval selection callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "interval_30"
        
        await hippo_bot._handle_interval_selection(mock_callback_query)
        
        # Verify interval was updated
        user = await hippo_bot.database.get_user(user_id)
        assert user['reminder_interval_minutes'] == 30
        
        # Verify response message
        mock_callback_query.edit_message_text.assert_called_once()


class TestNextReminderCalculation:
    """Test next reminder time calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_next_reminder_time_24_7_mode(self, hippo_bot):
        """Test next reminder calculation for 24/7 mode."""
        user_data = {
            'waking_start_hour': 0,
            'waking_start_minute': 0,
            'waking_end_hour': 23,
            'waking_end_minute': 0,
            'reminder_interval_minutes': 60,
            'timezone': 'Asia/Singapore'
        }
        
        result = await hippo_bot._calculate_next_reminder_time(user_data)
        assert result is not None
        assert "in 1 hour" in result
        assert ":" in result  # Should contain time
    
    @pytest.mark.asyncio
    async def test_calculate_next_reminder_time_normal_hours(self, hippo_bot):
        """Test next reminder calculation for normal waking hours."""
        user_data = {
            'waking_start_hour': 7,
            'waking_start_minute': 0,
            'waking_end_hour': 22,
            'waking_end_minute': 0,
            'reminder_interval_minutes': 30,
            'timezone': 'Asia/Singapore'
        }
        
        result = await hippo_bot._calculate_next_reminder_time(user_data)
        assert result is not None
        assert "30 minutes" in result or "when you wake up" in result
    
    @pytest.mark.asyncio
    async def test_calculate_next_reminder_time_short_interval(self, hippo_bot):
        """Test next reminder calculation for short intervals."""
        user_data = {
            'waking_start_hour': 0,
            'waking_start_minute': 0,
            'waking_end_hour': 23,
            'waking_end_minute': 0,
            'reminder_interval_minutes': 1,
            'timezone': 'Asia/Singapore'
        }
        
        result = await hippo_bot._calculate_next_reminder_time(user_data)
        assert result is not None
        assert "in 1 minute" in result


    @pytest.mark.asyncio  
    async def test_custom_hours_start_callback(self, hippo_bot, mock_callback_query, mock_context):
        """Test custom hours start callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "custom_hours_start"
        
        await hippo_bot._handle_custom_hours_callback(mock_callback_query)
        
        # Should show start time selection
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Step 1: Choose Start Hour" in args[0]

    @pytest.mark.asyncio
    async def test_custom_hours_cancel_callback(self, hippo_bot, mock_callback_query, mock_context):
        """Test custom hours cancel callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "custom_hours_cancel"
        
        await hippo_bot._handle_custom_hours_callback(mock_callback_query)
        
        # Should return to waking hours setup menu
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Choose Your Waking Hours" in args[0]

    @pytest.mark.asyncio
    async def test_start_hour_selection(self, hippo_bot, mock_callback_query, mock_context):
        """Test start hour selection callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "start_hour_8"
        
        await hippo_bot._handle_start_hour_selection(mock_callback_query)
        
        # Should show minute selection for hour 8
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Step 1: Choose Start Minute" in args[0]
        assert "Start hour: **08:xx**" in args[0]

    @pytest.mark.asyncio
    async def test_start_time_selection(self, hippo_bot, mock_callback_query, mock_context):
        """Test start time (hour and minute) selection callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "start_time_8_30"
        
        await hippo_bot._handle_start_time_selection(mock_callback_query)
        
        # Should show end hour selection
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Step 2: Choose End Hour" in args[0]
        assert "Start time: **08:30**" in args[0]

    @pytest.mark.asyncio
    async def test_end_hour_selection(self, hippo_bot, mock_callback_query, mock_context):
        """Test end hour selection callback."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "end_hour_8_30_22"
        
        await hippo_bot._handle_end_hour_selection(mock_callback_query)
        
        # Should show minute selection for end hour 22
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Step 2: Choose End Minute" in args[0]
        assert "Start time: **08:30**" in args[0]
        assert "End hour: **22:xx**" in args[0]

    @pytest.mark.asyncio
    async def test_complete_custom_hours_setup_normal_schedule(self, hippo_bot, mock_callback_query, mock_context):
        """Test completing custom hours setup with normal schedule."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "end_time_8_30_22_15"
        
        await hippo_bot._handle_end_time_selection(mock_callback_query)
        
        # Verify waking hours were updated in database
        user = await hippo_bot.database.get_user(user_id)
        assert user['waking_start_hour'] == 8
        assert user['waking_start_minute'] == 30
        assert user['waking_end_hour'] == 22  
        assert user['waking_end_minute'] == 15
        
        # Should show success message
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Custom Hours Set Successfully!" in args[0]
        assert "Start: 08:30" in args[0]
        assert "End: 22:15" in args[0]
        assert "regular schedule" in args[0]

    @pytest.mark.asyncio
    async def test_complete_custom_hours_setup_overnight_schedule(self, hippo_bot, mock_callback_query, mock_context):
        """Test completing custom hours setup with overnight schedule."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "end_time_22_45_6_15"
        
        await hippo_bot._handle_end_time_selection(mock_callback_query)
        
        # Verify waking hours were updated in database  
        user = await hippo_bot.database.get_user(user_id)
        assert user['waking_start_hour'] == 22
        assert user['waking_start_minute'] == 45
        assert user['waking_end_hour'] == 6
        assert user['waking_end_minute'] == 15
        
        # Should show success message with overnight detection
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Custom Hours Set Successfully!" in args[0]
        assert "Start: 22:45" in args[0]
        assert "End: 06:15" in args[0]
        assert "overnight schedule" in args[0]
        assert "Overnight schedule detected!" in args[0]

    @pytest.mark.asyncio
    async def test_complete_custom_hours_setup_invalid_time(self, hippo_bot, mock_callback_query, mock_context):
        """Test completing custom hours setup with invalid time (same start and end)."""
        user_id = mock_callback_query.from_user.id
        await hippo_bot.database.create_user(user_id, "testuser", "Test", "User")
        
        mock_callback_query.data = "end_time_8_30_8_30"
        
        await hippo_bot._handle_end_time_selection(mock_callback_query)
        
        # Should show error message for invalid time range
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Invalid Time Range" in args[0]

    @pytest.mark.asyncio
    async def test_reset_command(self, hippo_bot, mock_update, mock_context):
        """Test /reset command displays confirmation dialog."""
        user_id = mock_update.effective_user.id
        
        # Create user first
        await hippo_bot.database.create_user(user_id, "testuser")
        
        # Mock the reply method
        mock_update.message.reply_text = AsyncMock()
        
        # Test reset command
        await hippo_bot.reset_command(mock_update, mock_context)
        
        # Verify confirmation message was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Reset Your Hippo Bot Session" in args[0]
        assert "permanently delete" in args[0]
        assert kwargs['parse_mode'] == 'Markdown'
        assert kwargs['reply_markup'] is not None

    @pytest.mark.asyncio
    async def test_reset_confirm_callback(self, hippo_bot, mock_callback_query):
        """Test reset confirmation callback."""
        user_id = mock_callback_query.from_user.id
        
        # Create user first
        await hippo_bot.database.create_user(user_id, "testuser")
        
        # Set callback data for reset confirmation
        mock_callback_query.data = "reset_confirm"
        mock_callback_query.edit_message_text = AsyncMock()
        
        # Mock reminder system
        hippo_bot.reminder_system = AsyncMock()
        hippo_bot.reminder_system.cancel_user_reminders = AsyncMock()
        
        # Test reset confirmation
        await hippo_bot._handle_reset_confirm(mock_callback_query)
        
        # Verify user was deleted
        user = await hippo_bot.database.get_user(user_id)
        assert user is None
        
        # Verify confirmation message was sent
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Reset Complete" in args[0]
        assert "completely deleted" in args[0]

    @pytest.mark.asyncio
    async def test_reset_cancel_callback(self, hippo_bot, mock_callback_query):
        """Test reset cancellation callback."""
        user_id = mock_callback_query.from_user.id
        
        # Create user first
        await hippo_bot.database.create_user(user_id, "testuser")
        
        # Set callback data for reset cancellation
        mock_callback_query.data = "reset_cancel"
        mock_callback_query.edit_message_text = AsyncMock()
        
        # Test reset cancellation
        await hippo_bot._handle_reset_cancel(mock_callback_query)
        
        # Verify user still exists
        user = await hippo_bot.database.get_user(user_id)
        assert user is not None
        assert user['user_id'] == user_id
        
        # Verify cancellation message was sent
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Reset Cancelled" in args[0]

    @pytest.mark.asyncio
    async def test_stats_callback_with_data(self, hippo_bot, mock_callback_query):
        """Test stats callback with hydration data."""
        user_id = mock_callback_query.from_user.id
        
        # Create user first
        await hippo_bot.database.create_user(user_id, "testuser")
        
        # Add some hydration events
        await hippo_bot.database.record_hydration_event(user_id, "confirmed", "test_reminder_1")
        await hippo_bot.database.record_hydration_event(user_id, "confirmed", "test_reminder_2")
        await hippo_bot.database.record_hydration_event(user_id, "missed", "test_reminder_3")
        
        # Set callback data for stats
        mock_callback_query.data = "stats"
        mock_callback_query.edit_message_text = AsyncMock()
        
        # Test stats callback
        await hippo_bot._handle_stats_callback(mock_callback_query)
        
        # Verify stats message was sent
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Your Hydration Stats" in args[0]
        assert "Water confirmations: 2" in args[0]
        assert "Missed reminders: 1" in args[0]
        assert "Success rate: 66.7%" in args[0]

    @pytest.mark.asyncio
    async def test_stats_callback_no_data(self, hippo_bot, mock_callback_query):
        """Test stats callback with no hydration data."""
        user_id = mock_callback_query.from_user.id
        
        # Create user first
        await hippo_bot.database.create_user(user_id, "testuser")
        
        # Set callback data for stats
        mock_callback_query.data = "stats"
        mock_callback_query.edit_message_text = AsyncMock()
        
        # Test stats callback
        await hippo_bot._handle_stats_callback(mock_callback_query)
        
        # Verify stats message was sent (even with zero data)
        mock_callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_callback_query.edit_message_text.call_args
        assert "Your Hydration Stats" in args[0]
        assert "Success rate: 0.0%" in args[0]