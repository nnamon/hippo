"""
Test configuration and fixtures for Hippo bot tests.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock
from telegram import User, Chat, Message, Update, CallbackQuery
from telegram.ext import ContextTypes

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database.models import DatabaseManager
from src.content.manager import ContentManager
from src.bot.hippo_bot import HippoBot
from src.bot.reminder_system import ReminderSystem


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    
    # Cancel all remaining tasks before closing
    try:
        pending = asyncio.all_tasks(loop)
        if pending:
            for task in pending:
                task.cancel()
            # Wait for tasks to be cancelled
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass
    finally:
        loop.close()


@pytest_asyncio.fixture
async def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    db = DatabaseManager(db_path)
    await db.initialize()
    
    try:
        yield db
    finally:
        await db.close()
        os.unlink(db_path)


@pytest.fixture
def content_manager():
    """Create a content manager instance."""
    # Always create a fresh instance - no shared state
    from src.content.manager import ContentManager
    return ContentManager()


@pytest_asyncio.fixture
async def reminder_system(temp_db, content_manager):
    """Create a reminder system instance."""
    return ReminderSystem(temp_db, content_manager)


@pytest_asyncio.fixture
async def hippo_bot(temp_db, content_manager):
    """Create a Hippo bot instance for testing."""
    from unittest.mock import patch
    with patch('src.bot.hippo_bot.DatabaseManager', return_value=temp_db):
        with patch('src.bot.hippo_bot.ContentManager', return_value=content_manager):
            bot = HippoBot("fake_token")
            bot.database = temp_db
            bot.content_manager = content_manager
            return bot


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.edit_message_caption = AsyncMock()
    bot.edit_message_reply_markup = AsyncMock()
    bot.set_my_commands = AsyncMock()
    return bot


@pytest.fixture
def mock_context(mock_bot):
    """Create a mock context instance."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = mock_bot
    context.job = MagicMock()
    context.job.data = {}
    return context


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = 12345
    user.is_bot = False
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    return user


@pytest.fixture
def mock_chat():
    """Create a mock chat."""
    chat = MagicMock(spec=Chat)
    chat.id = 12345
    chat.type = "private"
    return chat


@pytest.fixture
def mock_message(mock_user, mock_chat):
    """Create a mock message."""
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.date = None
    message.chat = mock_chat
    message.from_user = mock_user
    message.reply_text = AsyncMock()
    return message


@pytest.fixture
def mock_update(mock_message, mock_user):
    """Create a mock update."""
    update = MagicMock(spec=Update)
    update.update_id = 1
    update.message = mock_message
    update.effective_user = mock_user
    update.effective_chat = mock_message.chat
    return update


@pytest.fixture
def mock_callback_query(mock_user, mock_message):
    """Create a mock callback query."""
    query = MagicMock(spec=CallbackQuery)
    query.id = "test_callback"
    query.from_user = mock_user
    query.chat_instance = "test_chat"
    query.message = mock_message
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.edit_message_caption = AsyncMock()
    query.data = "test_data"
    return query


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'user_id': 12345,
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'waking_start_hour': 7,
        'waking_start_minute': 0,
        'waking_end_hour': 22,
        'waking_end_minute': 0,
        'reminder_interval_minutes': 60,
        'theme': 'bluey',
        'timezone': 'Asia/Singapore',
        'is_active': True
    }