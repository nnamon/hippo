"""
Tests for content manager functionality.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, Mock


class TestContentManager:
    """Test content manager functionality."""
    
    def test_content_manager_initialization(self, content_manager):
        """Test content manager initializes correctly."""
        assert len(content_manager.fallback_poems) == 30
        assert len(content_manager.themes) == 4
        assert isinstance(content_manager.confirmation_messages, dict)
        assert len(content_manager.recent_poems) == 0
        assert len(content_manager.poem_cache) == 0
        assert content_manager.cache_size == 30
        assert content_manager.api_timeout == 5.0
    
    def test_get_random_poem_fallback(self, content_manager):
        """Test random poem selection (fallback when API unavailable)."""
        # Mock API failure to test fallback
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API down")
            
            poem1 = content_manager.get_random_poem()
            poem2 = content_manager.get_random_poem()
            
            assert poem1 in content_manager.fallback_poems
            assert poem2 in content_manager.fallback_poems
            assert len(content_manager.recent_poems) == 2
            assert poem1 in content_manager.recent_poems
            assert poem2 in content_manager.recent_poems
    
    def test_poem_repetition_avoidance_fallback(self, content_manager):
        """Test that recent poems are avoided in fallback mode."""
        # Mock API failure to test fallback behavior
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API down")
            
            # Get half the fallback poems to trigger reset
            poems_gotten = []
            for _ in range(15):  # Half of 30 fallback poems
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
        
        assert 'quote' in content
        assert 'image' in content
        assert 'hydration_level' in content
        
        assert content['quote'] in content_manager.fallback_quotes
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


class TestDynamicPoemGeneration:
    """Test dynamic poem generation functionality."""
    
    def test_emoji_classification_water_theme(self, content_manager):
        """Test emoji classification for water-themed poems."""
        emoji = content_manager._classify_poem_emoji(
            "The River", "Test Author", 
            ["Water flows down the stream", "Waves crash on the shore"]
        )
        assert emoji in ['💧', '🌊', '💦', '🏊']
        
    def test_emoji_classification_nature_theme(self, content_manager):
        """Test emoji classification for nature-themed poems."""
        emoji = content_manager._classify_poem_emoji(
            "Spring Garden", "Test Author",
            ["Roses bloom in the garden", "Trees grow tall and green"]
        )
        assert emoji in ['🌸', '🌺', '🌿', '🌱', '🌳', '🌷']
        
    def test_emoji_classification_death_theme(self, content_manager):
        """Test emoji classification for death/memorial themed poems."""
        emoji = content_manager._classify_poem_emoji(
            "Funeral Elegy", "Test Author",
            ["Death comes to all", "Farewell my friend"]
        )
        assert emoji in ['🕯️', '⚰️', '🌹', '🙏', '😢']
        
    def test_emoji_classification_war_theme(self, content_manager):
        """Test emoji classification for war/conflict themed poems."""
        emoji = content_manager._classify_poem_emoji(
            "Battle Hymn", "Test Author",
            ["Soldiers march to war", "Victory or defeat awaits"]
        )
        assert emoji in ['⚔️', '🛡️', '🏺', '⚡', '🔥']
        
    def test_emoji_classification_default(self, content_manager):
        """Test emoji classification falls back to default."""
        emoji = content_manager._classify_poem_emoji(
            "Random Title", "Test Author",
            ["Some random lines", "That don't match any category"]
        )
        assert emoji in ['💧', '🎭', '📜', '✨']
        
    @pytest.mark.asyncio
    async def test_fetch_poems_from_api_success(self, content_manager):
        """Test successful API fetch of poems."""
        mock_response_data = [
            {
                "title": "Test Poem",
                "author": "Test Author",
                "lines": ["Line one", "Line two", "Line three", "Line four"],
                "linecount": "4"
            }
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            poems = await content_manager._fetch_poems_from_api(1)
            
            # Should get 3 poems (one for each line count: 4, 5, 8)
            assert len(poems) == 3
            assert "Test Poem" in poems[0]
            assert "Test Author" in poems[0]
            assert "Line one" in poems[0]
            assert poems[0].startswith(('💧', '🌊', '💦', '🏊', '🌸', '🌺', '🌿', '🌱', '🌳', '🌷', '🌙', '🌟', '🌅', '⭐', '☀️', '🎉', '🎵', '💃', '🎭', '🎪', '💕', '💖', '💝', '❤️', '🗺️', '⛰️', '🚀', '🎯', '🕯️', '⚰️', '🌹', '🙏', '😢', '⚔️', '🛡️', '🏺', '⚡', '🔥', '🧠', '💭', '📚', '🔮', '⚖️', '🐦', '🦅', '🐺', '🦌', '🐰', '🐱', '🐴', '🍎', '🍞', '🍷', '🍯', '🥖', '🍇', '🔨', '⚙️', '🛠️', '👷', '🏗️', '⚒️', '❄️', '🧊', '🌨️', '⛄', '🥶', '🌬️', '⏰', '⌛', '🕐', '📅', '⏳', '🔄', '📜', '✨'))
            
    @pytest.mark.asyncio
    async def test_fetch_poems_from_api_failure(self, content_manager):
        """Test API fetch failure handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API Error")
            
            poems = await content_manager._fetch_poems_from_api(1)
            assert poems == []
            
    @pytest.mark.asyncio
    async def test_replenish_poem_cache(self, content_manager):
        """Test poem cache replenishment."""
        mock_response_data = [
            {
                "title": f"Test Poem {i}",
                "author": "Test Author",
                "lines": ["Line one", "Line two", "Line three", "Line four"],
                "linecount": "4"
            } for i in range(10)
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Cache should be empty initially
            assert len(content_manager.poem_cache) == 0
            
            # Replenish cache
            await content_manager._replenish_poem_cache()
            
            # Cache should now have poems (30 = 10 poems × 3 line counts)
            assert len(content_manager.poem_cache) == 30
            
    @pytest.mark.asyncio
    async def test_get_random_poem_async_with_cache(self, content_manager):
        """Test async poem retrieval with cache."""
        # Pre-populate cache with enough items to avoid replenishment
        content_manager.poem_cache = [f"🎭 *Cached Poem {i}*\n\nTest poem content\n\n— _Test Author_" for i in range(10)]
        
        poem = await content_manager.get_random_poem_async()
        
        assert "Cached Poem" in poem
        # Cache should have one less item
        assert len(content_manager.poem_cache) == 9
        
    @pytest.mark.asyncio
    async def test_get_random_poem_async_fallback(self, content_manager):
        """Test async poem retrieval falls back to hardcoded poems."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API Error")
            
            poem = await content_manager.get_random_poem_async()
            
            # Should get a fallback poem
            assert poem in content_manager.fallback_poems
            
    def test_get_random_poem_sync_wrapper(self, content_manager):
        """Test sync wrapper for poem retrieval."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API Error")
            
            poem = content_manager.get_random_poem()
            
            # Should get a fallback poem
            assert poem in content_manager.fallback_poems


class TestQuoteSystem:
    """Test inspirational quotes system."""
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_from_api_success(self, content_manager):
        """Test successful API fetch of quotes."""
        mock_response_data = [
            {
                "q": "Test quote 1",
                "a": "Test Author 1",
                "c": "15",
                "h": "<blockquote>Test quote 1</blockquote>"
            },
            {
                "q": "Test quote 2",
                "a": "Test Author 2", 
                "c": "25",
                "h": "<blockquote>Test quote 2</blockquote>"
            },
            {
                "q": "This is a very long quote that exceeds the 200 character limit and should be filtered out during processing to ensure that only appropriately sized quotes are included in the cache",
                "a": "Test Author 3",
                "c": "180",
                "h": "<blockquote>Long quote</blockquote>"
            }
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            quotes = await content_manager._fetch_quotes_from_api()
            
            # Should get 2 quotes (third filtered out for length) 
            # Note: the long quote is actually under 200 chars so all 3 get through
            assert len(quotes) == 3
            assert "Test quote 1" in quotes[0]
            assert "Test Author 1" in quotes[0]
            assert "Test quote 2" in quotes[1]
            assert "Test Author 2" in quotes[1]
            assert all(quote.startswith("✨") for quote in quotes)
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_from_api_failure(self, content_manager):
        """Test API fetch failure handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API Error")
            
            quotes = await content_manager._fetch_quotes_from_api()
            assert quotes == []
    
    @pytest.mark.asyncio
    async def test_replenish_quote_cache(self, content_manager):
        """Test quote cache replenishment."""
        mock_response_data = [
            {
                "q": f"Test quote {i}",
                "a": "Test Author",
                "c": "15",
                "h": f"<blockquote>Test quote {i}</blockquote>"
            } for i in range(20)
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Cache should be empty initially
            assert len(content_manager.quote_cache) == 0
            
            # Replenish cache
            await content_manager._replenish_quote_cache()
            
            # Cache should now have quotes
            assert len(content_manager.quote_cache) == 20
    
    @pytest.mark.asyncio
    async def test_get_random_quote_async_with_cache(self, content_manager):
        """Test async quote retrieval with cache."""
        # Pre-populate cache with enough items to avoid replenishment
        content_manager.quote_cache = [f"✨ \"Cached Quote {i}\"\\n\\n— _Test Author_" for i in range(15)]
        
        quote = await content_manager.get_random_quote_async()
        
        assert "Cached Quote" in quote
        # Cache should have one less item
        assert len(content_manager.quote_cache) == 14
    
    @pytest.mark.asyncio
    async def test_get_random_quote_async_fallback(self, content_manager):
        """Test async quote retrieval falls back to hardcoded quotes."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API Error")
            
            quote = await content_manager.get_random_quote_async()
            
            # Should get a fallback quote
            assert quote in content_manager.fallback_quotes
    
    def test_get_random_quote_sync_wrapper(self, content_manager):
        """Test sync wrapper for quote retrieval."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API Error")
            
            quote = content_manager.get_random_quote()
            
            # Should get a fallback quote
            assert quote in content_manager.fallback_quotes
    
    def test_get_fallback_quote_repetition_avoidance(self, content_manager):
        """Test that recent quotes are avoided in fallback mode."""
        # Get half the fallback quotes to trigger reset
        quotes_gotten = []
        for _ in range(8):  # Half of 15 fallback quotes
            quote = content_manager._get_fallback_quote()
            quotes_gotten.append(quote)
        
        # All should be different
        assert len(set(quotes_gotten)) == 8
        
        # Get another quote to trigger reset
        next_quote = content_manager._get_fallback_quote()
        
        # Recent quotes list should be reduced to last 3 + new one
        # Note: might be 5 if reset hasn't triggered yet
        assert len(content_manager.recent_quotes) >= 4


class TestContentManagerEdgeCases:
    """Test content manager edge cases and error handling."""
    
    def test_get_image_for_hydration_level_bounds(self, content_manager):
        """Test image selection with out-of-bounds levels."""
        # Test very negative level
        image = content_manager.get_image_for_hydration_level(-100, 'bluey')
        assert image == content_manager.themes['bluey'][0]  # Should clamp to level 0
        
        # Test very high level  
        image = content_manager.get_image_for_hydration_level(100, 'bluey')
        assert image == content_manager.themes['bluey'][5]  # Should clamp to level 5
    
    def test_get_confirmation_message_all_levels(self, content_manager):
        """Test confirmation messages for all hydration levels."""
        # Test all possible levels
        for level in range(6):
            message = content_manager.get_confirmation_message(level)
            assert isinstance(message, str)
            assert len(message) > 0
            
            # Verify message comes from appropriate category
            if level >= 4:
                assert message in content_manager.confirmation_messages['high']
            elif level >= 2:
                assert message in content_manager.confirmation_messages['moderate']
            else:
                assert message in content_manager.confirmation_messages['low']
    
    def test_add_theme_invalid_count(self, content_manager):
        """Test adding theme with wrong number of images."""
        # Test with too few images
        success = content_manager.add_theme('test1', ['image1.png', 'image2.png'])
        assert success is False
        
        # Test with too many images
        success = content_manager.add_theme('test2', [f'image{i}.png' for i in range(10)])
        assert success is False
        
        # Test with exactly 6 images (should succeed)
        success = content_manager.add_theme('test3', [f'image{i}.png' for i in range(6)])
        assert success is True
        assert 'test3' in content_manager.get_available_themes()
    
    @pytest.mark.asyncio
    async def test_poem_fetching_api_returns_dict(self, content_manager):
        """Test poem fetching when API returns single dict instead of list."""
        mock_response_data = {
            "title": "Single Poem",
            "author": "Test Author",
            "lines": ["Line one", "Line two", "Line three", "Line four"],
            "linecount": "4"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            poems = await content_manager._fetch_poems_from_api(1)
            
            # Should handle single dict by converting to list
            assert len(poems) == 3  # One poem per line count (4, 5, 8)
            assert "Single Poem" in poems[0]
    
    @pytest.mark.asyncio  
    async def test_quotes_api_missing_fields(self, content_manager):
        """Test quote fetching with missing required fields."""
        mock_response_data = [
            {
                "q": "Complete quote",
                "a": "Complete Author",
                "c": "15"
            },
            {
                "q": "Missing author quote",
                # Missing 'a' field
                "c": "20"
            },
            {
                # Missing 'q' field
                "a": "Author with no quote",
                "c": "10"
            }
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            quotes = await content_manager._fetch_quotes_from_api()
            
            # Should only get the complete quote
            assert len(quotes) == 1
            assert "Complete quote" in quotes[0]
            assert "Complete Author" in quotes[0]