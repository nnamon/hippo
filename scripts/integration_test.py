#!/usr/bin/env python3
"""
Integration test script for Hippo bot.

This script tests the full bot initialization and component integration
to ensure all parts work together correctly.
"""

import asyncio
import sys
import tempfile
import os
from pathlib import Path

# Add both project root and src to Python path for robust imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))


async def test_database_integration():
    """Test database initialization and basic operations."""
    print("🔄 Testing database integration...")
    
    from database.models import DatabaseManager
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path)
        await db.initialize()
        
        # Test basic user operations
        user_id = 12345
        await db.create_user(user_id, "testuser", "Test", "User")
        user = await db.get_user(user_id)
        assert user is not None
        assert user['username'] == "testuser"
        
        await db.close()
        print("✅ Database integration test passed")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


async def test_content_manager_integration():
    """Test content manager initialization and functionality."""
    print("🔄 Testing content manager integration...")
    
    from content.manager import ContentManager
    
    content_manager = ContentManager()
    
    # Test fallback poems
    assert len(content_manager.fallback_poems) > 0, "Fallback poems should be loaded"
    assert len(content_manager.themes) > 0, "Themes should be loaded"
    
    # Test poem retrieval
    poem = content_manager.get_random_poem()
    assert isinstance(poem, str), "Should return a string poem"
    assert len(poem) > 0, "Poem should not be empty"
    
    # Test async poem retrieval
    poem_async = await content_manager.get_random_poem_async()
    assert isinstance(poem_async, str), "Should return a string poem"
    
    # Test image retrieval
    image_path = content_manager.get_image_for_hydration_level(2, 'bluey')
    assert isinstance(image_path, str), "Should return image path string"
    assert 'bluey' in image_path, "Should contain theme name"
    
    print("✅ Content manager integration test passed")


async def test_reminder_system_integration():
    """Test reminder system integration with database and content manager."""
    print("🔄 Testing reminder system integration...")
    
    try:
        from database.models import DatabaseManager
        from content.manager import ContentManager
        from bot.reminder_system import ReminderSystem
    except ImportError:
        from src.database.models import DatabaseManager
        from src.content.manager import ContentManager
        from src.bot.reminder_system import ReminderSystem
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path)
        await db.initialize()
        
        content_manager = ContentManager()
        reminder_system = ReminderSystem(db, content_manager)
        
        # Test that reminder system initializes correctly
        assert reminder_system.database is db, "Reminder system should have database reference"
        assert reminder_system.content_manager is content_manager, "Reminder system should have content manager reference"
        
        await db.close()
        print("✅ Reminder system integration test passed")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


async def test_bot_imports():
    """Test that bot components can be imported without errors."""
    print("🔄 Testing bot imports...")
    
    try:
        # Try relative imports first
        from bot.hippo_bot import HippoBot
        from bot.reminder_system import ReminderSystem
        from database.models import DatabaseManager
        from content.manager import ContentManager
        
        print("✅ All bot imports successful")
        
    except ImportError:
        try:
            # Try absolute imports as fallback
            from src.bot.hippo_bot import HippoBot
            from src.bot.reminder_system import ReminderSystem
            from src.database.models import DatabaseManager
            from src.content.manager import ContentManager
            
            print("✅ All bot imports successful")
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            raise


async def test_dynamic_poem_generation():
    """Test dynamic poem generation features."""
    print("🔄 Testing dynamic poem generation...")
    
    from content.manager import ContentManager
    
    content_manager = ContentManager()
    
    # Test emoji classification
    emoji = content_manager._classify_poem_emoji("Water Song", "Test Author", ["Water flows", "Ocean waves"])
    assert emoji in ['💧', '🌊', '💦', '🏊'], f"Should return water-themed emoji, got: {emoji}"
    
    # Test cache initialization
    assert hasattr(content_manager, 'poem_cache'), "Should have poem cache"
    assert hasattr(content_manager, 'cache_size'), "Should have cache size"
    assert content_manager.cache_size == 20, "Cache size should be 20"
    
    print("✅ Dynamic poem generation test passed")


async def main():
    """Run all integration tests."""
    print("🦛 Hippo Bot Integration Tests")
    print("=" * 50)
    
    tests = [
        test_bot_imports,
        test_database_integration,
        test_content_manager_integration,
        test_reminder_system_integration,
        test_dynamic_poem_generation,
    ]
    
    failed_tests = []
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed_tests.append(test.__name__)
    
    print("\n" + "=" * 50)
    if failed_tests:
        print(f"❌ {len(failed_tests)} test(s) failed:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        sys.exit(1)
    else:
        print("✅ All integration tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())