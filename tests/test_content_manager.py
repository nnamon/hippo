"""
Tests for content manager functionality.
"""

import pytest


class TestContentManager:
    """Test content manager functionality."""
    
    def test_content_manager_initialization(self, content_manager):
        """Test content manager initializes correctly."""
        assert len(content_manager.poems) == 30
        assert len(content_manager.themes) == 4
        assert isinstance(content_manager.confirmation_messages, dict)
        assert len(content_manager.recent_poems) == 0
    
    def test_get_random_poem(self, content_manager):
        """Test random poem selection."""
        poem1 = content_manager.get_random_poem()
        poem2 = content_manager.get_random_poem()
        
        assert poem1 in content_manager.poems
        assert poem2 in content_manager.poems
        assert len(content_manager.recent_poems) == 2
        assert poem1 in content_manager.recent_poems
        assert poem2 in content_manager.recent_poems
    
    def test_poem_repetition_avoidance(self, content_manager):
        """Test that recent poems are avoided."""
        # Get half the poems to trigger reset
        poems_gotten = []
        for _ in range(15):  # Half of 30 poems
            poem = content_manager.get_random_poem()
            poems_gotten.append(poem)
        
        # All should be different
        assert len(set(poems_gotten)) == 15
        
        # Get another poem to trigger reset
        next_poem = content_manager.get_random_poem()
        
        # Recent poems list should be reduced to last 3
        assert len(content_manager.recent_poems) == 4  # 3 + the new one
    
    def test_get_available_themes(self, content_manager):
        """Test getting available themes."""
        themes = content_manager.get_available_themes()
        expected_themes = ['bluey', 'desert', 'spring', 'vivid']
        
        assert len(themes) == 4
        for theme in expected_themes:
            assert theme in themes
    
    def test_get_image_for_hydration_level(self, content_manager):
        """Test image selection for hydration levels."""
        # Test valid levels
        for level in range(6):
            image = content_manager.get_image_for_hydration_level(level, 'bluey')
            assert image.startswith('bluey/')
            assert image.endswith('.png')
        
        # Test level bounds
        image_low = content_manager.get_image_for_hydration_level(-1, 'bluey')
        image_high = content_manager.get_image_for_hydration_level(10, 'bluey')
        
        assert image_low == content_manager.themes['bluey'][0]  # Level 0
        assert image_high == content_manager.themes['bluey'][5]  # Level 5
    
    def test_get_image_invalid_theme(self, content_manager):
        """Test image selection with invalid theme."""
        # Should fallback to default theme
        image = content_manager.get_image_for_hydration_level(2, 'nonexistent')
        # Should use first available theme (bluey)
        assert 'bluey/' in image or 'desert/' in image or 'spring/' in image or 'vivid/' in image
    
    def test_get_confirmation_message_low_level(self, content_manager):
        """Test confirmation messages for low hydration levels."""
        message = content_manager.get_confirmation_message(0)
        assert message in content_manager.confirmation_messages['low']
        
        message = content_manager.get_confirmation_message(1)
        assert message in content_manager.confirmation_messages['low']
    
    def test_get_confirmation_message_moderate_level(self, content_manager):
        """Test confirmation messages for moderate hydration levels."""
        message = content_manager.get_confirmation_message(2)
        assert message in content_manager.confirmation_messages['moderate']
        
        message = content_manager.get_confirmation_message(3)
        assert message in content_manager.confirmation_messages['moderate']
    
    def test_get_confirmation_message_high_level(self, content_manager):
        """Test confirmation messages for high hydration levels."""
        message = content_manager.get_confirmation_message(4)
        assert message in content_manager.confirmation_messages['high']
        
        message = content_manager.get_confirmation_message(5)
        assert message in content_manager.confirmation_messages['high']
    
    def test_get_reminder_content(self, content_manager):
        """Test complete reminder content generation."""
        content = content_manager.get_reminder_content(3, 'spring')
        
        assert 'poem' in content
        assert 'image' in content
        assert 'hydration_level' in content
        
        assert content['poem'] in content_manager.poems
        assert content['image'].startswith('spring/')
        assert content['hydration_level'] == 3
    
    def test_add_theme(self, content_manager):
        """Test adding a new theme."""
        new_theme_images = [
            'newtheme/level0.png',
            'newtheme/level1.png',
            'newtheme/level2.png',
            'newtheme/level3.png',
            'newtheme/level4.png',
            'newtheme/level5.png'
        ]
        
        success = content_manager.add_theme('newtheme', new_theme_images)
        assert success is True
        
        themes = content_manager.get_available_themes()
        assert 'newtheme' in themes
        
        # Test with wrong number of images
        success = content_manager.add_theme('badtheme', ['only1.png'])
        assert success is False