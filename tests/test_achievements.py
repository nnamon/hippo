"""
Tests for the achievement system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.achievements import Achievement, AchievementChecker, ACHIEVEMENTS
from src.database.models import DatabaseManager


class TestAchievementDefinitions:
    """Test achievement definitions and structure."""
    
    def test_all_achievements_have_required_fields(self):
        """Test that all achievements have required fields."""
        for code, achievement in ACHIEVEMENTS.items():
            assert isinstance(achievement, Achievement)
            assert achievement.code == code
            assert achievement.name
            assert achievement.description
            assert achievement.icon
            assert achievement.category in ['easy', 'consistency', 'performance', 'special', 'milestone']
    
    def test_easy_achievements_exist(self):
        """Test that easy achievements are defined."""
        easy_achievements = [a for a in ACHIEVEMENTS.values() if a.category == 'easy']
        assert len(easy_achievements) >= 5
        
        # Check specific easy achievements
        assert 'first_sip' in ACHIEVEMENTS
        assert 'getting_started' in ACHIEVEMENTS
        assert 'hydration_habit' in ACHIEVEMENTS
        assert 'daily_dose' in ACHIEVEMENTS
        assert 'quick_response' in ACHIEVEMENTS
    
    def test_achievement_categories_populated(self):
        """Test that all categories have achievements."""
        categories = {}
        for achievement in ACHIEVEMENTS.values():
            if achievement.category not in categories:
                categories[achievement.category] = 0
            categories[achievement.category] += 1
        
        assert 'easy' in categories and categories['easy'] >= 5
        assert 'consistency' in categories and categories['consistency'] >= 4
        assert 'performance' in categories and categories['performance'] >= 4
        assert 'special' in categories and categories['special'] >= 4
        assert 'milestone' in categories and categories['milestone'] >= 3


class TestAchievementChecker:
    """Test achievement checking logic."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database manager."""
        db = AsyncMock(spec=DatabaseManager)
        return db
    
    @pytest.fixture
    def checker(self, mock_db):
        """Create an achievement checker instance."""
        return AchievementChecker(mock_db)
    
    @pytest.mark.asyncio
    async def test_check_first_confirmation_achievements(self, checker, mock_db):
        """Test achievements for first water confirmation."""
        # Setup mocks
        mock_db.get_total_confirmations.return_value = 1
        mock_db.grant_achievement.return_value = True
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 1, 'missed': 0}
        
        # Check achievements
        new_achievements = await checker.check_confirmation_achievements(123)
        
        # Should get first_sip achievement
        assert 'first_sip' in new_achievements
        mock_db.grant_achievement.assert_any_call(123, 'first_sip')
    
    @pytest.mark.asyncio
    async def test_check_multiple_confirmation_achievements(self, checker, mock_db):
        """Test achievements for multiple confirmations."""
        # Test 5 confirmations - should get "getting_started"
        mock_db.get_total_confirmations.return_value = 5
        mock_db.grant_achievement.return_value = True
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 5, 'missed': 0}
        
        new_achievements = await checker.check_confirmation_achievements(123)
        
        assert 'getting_started' in new_achievements
        mock_db.grant_achievement.assert_any_call(123, 'getting_started')
        
        # Test 10 confirmations - should get "hydration_habit"
        mock_db.get_total_confirmations.return_value = 10
        mock_db.grant_achievement.return_value = True
        
        new_achievements = await checker.check_confirmation_achievements(123)
        
        assert 'hydration_habit' in new_achievements
        mock_db.grant_achievement.assert_any_call(123, 'hydration_habit')
    
    @pytest.mark.asyncio
    async def test_check_milestone_achievements(self, checker, mock_db):
        """Test milestone achievements."""
        # Test 100 confirmations - centurion
        mock_db.get_total_confirmations.return_value = 100
        mock_db.grant_achievement.return_value = True
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 100, 'missed': 0}
        
        new_achievements = await checker.check_confirmation_achievements(123)
        
        assert 'centurion' in new_achievements
        
        # Test 1000 confirmations - hydration veteran
        mock_db.get_total_confirmations.return_value = 1000
        mock_db.grant_achievement.return_value = True
        
        new_achievements = await checker.check_confirmation_achievements(123)
        
        assert 'hydration_veteran' in new_achievements
    
    @pytest.mark.asyncio
    async def test_quick_response_achievement(self, checker, mock_db):
        """Test quick response achievement."""
        mock_db.get_total_confirmations.return_value = 1
        mock_db.grant_achievement.return_value = True
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 1, 'missed': 0}
        
        # Confirm within 1 minute
        reminder_time = datetime.now() - timedelta(seconds=30)
        new_achievements = await checker.check_confirmation_achievements(123, reminder_time)
        
        assert 'quick_response' in new_achievements
        mock_db.grant_achievement.assert_any_call(123, 'quick_response')
    
    @pytest.mark.asyncio
    async def test_time_based_achievements(self, checker, mock_db):
        """Test early bird and night owl achievements."""
        mock_db.get_total_confirmations.return_value = 1
        mock_db.grant_achievement.return_value = True
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 1, 'missed': 0}
        
        # Test early bird (before 6 AM)
        with patch('src.bot.achievements.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 5, 30)  # 5:30 AM
            
            new_achievements = await checker.check_confirmation_achievements(123)
            
            assert 'early_bird' in new_achievements
        
        # Test night owl (between midnight and 4 AM)
        with patch('src.bot.achievements.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 2, 30)  # 2:30 AM
            
            new_achievements = await checker.check_confirmation_achievements(123)
            
            assert 'night_owl' in new_achievements
    
    @pytest.mark.asyncio
    async def test_streak_achievements(self, checker, mock_db):
        """Test streak-based achievements."""
        mock_db.grant_achievement.return_value = True
        
        # Test 3-day streak
        new_achievements = await checker.check_streak_achievements(123, 3)
        assert 'three_day_streak' in new_achievements
        
        # Test 7-day streak
        new_achievements = await checker.check_streak_achievements(123, 7)
        assert 'week_warrior' in new_achievements
        
        # Test 14-day streak
        new_achievements = await checker.check_streak_achievements(123, 14)
        assert 'fortnight_champion' in new_achievements
        
        # Test 30-day streak
        new_achievements = await checker.check_streak_achievements(123, 30)
        assert 'monthly_master' in new_achievements
    
    @pytest.mark.asyncio
    async def test_hydration_level_achievements(self, checker, mock_db):
        """Test hydration level achievements."""
        mock_db.grant_achievement.return_value = True
        
        # Test level 5 achievement
        new_achievements = await checker.check_level_achievements(123, 5)
        assert 'level_five' in new_achievements
        
        # Lower levels shouldn't trigger
        new_achievements = await checker.check_level_achievements(123, 4)
        assert 'level_five' not in new_achievements
    
    @pytest.mark.asyncio
    async def test_performance_achievements(self, checker, mock_db):
        """Test performance-based achievements."""
        mock_db.get_total_confirmations.return_value = 25
        mock_db.grant_achievement.return_value = True
        
        # Test hydration hero (90%+ success rate)
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 45, 'missed': 5}
        
        new_achievements = await checker.check_confirmation_achievements(123)
        
        assert 'hydration_hero' in new_achievements
        
        # Test perfect week
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 28, 'missed': 0}
        
        new_achievements = await checker.check_confirmation_achievements(123)
        
        assert 'perfect_week' in new_achievements
    
    @pytest.mark.asyncio
    async def test_daily_achievements(self, checker, mock_db):
        """Test daily achievements."""
        mock_db.get_total_confirmations.return_value = 5
        mock_db.grant_achievement.return_value = True
        
        # Mock 3+ confirmations today
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 3, 'missed': 0}
        
        new_achievements = await checker.check_confirmation_achievements(123)
        
        assert 'daily_dose' in new_achievements
    
    @pytest.mark.asyncio
    async def test_no_duplicate_achievements(self, checker, mock_db):
        """Test that already earned achievements aren't granted again."""
        mock_db.get_total_confirmations.return_value = 1
        mock_db.grant_achievement.return_value = False  # Already has achievement
        mock_db.get_user_hydration_stats.return_value = {'confirmed': 1, 'missed': 0}
        
        new_achievements = await checker.check_confirmation_achievements(123)
        
        # Should not include first_sip since user already has it
        assert 'first_sip' not in new_achievements
    
    def test_get_achievement_display(self, checker):
        """Test achievement display formatting."""
        display = checker.get_achievement_display('first_sip')
        assert display == "💧 First Sip"
        
        # Test unknown achievement
        display = checker.get_achievement_display('unknown_achievement')
        assert display == "🏆 unknown_achievement"
    
    def test_get_achievement_details(self, checker):
        """Test getting full achievement details."""
        details = checker.get_achievement_details('first_sip')
        assert isinstance(details, Achievement)
        assert details.code == 'first_sip'
        
        # Test unknown achievement
        details = checker.get_achievement_details('unknown')
        assert details is None
    
    def test_get_all_achievements_grouped(self, checker):
        """Test getting achievements grouped by category."""
        grouped = checker.get_all_achievements()
        
        assert 'easy' in grouped
        assert 'consistency' in grouped
        assert 'performance' in grouped
        assert 'special' in grouped
        assert 'milestone' in grouped
        
        # Check that hidden achievements are not included
        all_achievements = []
        for category_achievements in grouped.values():
            all_achievements.extend(category_achievements)
        
        hidden_count = sum(1 for a in all_achievements if a.hidden)
        assert hidden_count == 0
    
    @pytest.mark.asyncio
    async def test_time_based_account_age_achievement(self, checker, mock_db):
        """Test dedication achievement based on account age."""
        mock_db.get_user.return_value = {
            'user_id': 123,
            'created_at': (datetime.now() - timedelta(days=31)).isoformat()
        }
        mock_db.grant_achievement.return_value = True
        
        new_achievements = await checker.check_time_based_achievements(123)
        
        assert 'dedication' in new_achievements
        mock_db.grant_achievement.assert_called_with(123, 'dedication')
    
    @pytest.mark.asyncio
    async def test_grant_if_new_helper(self, checker, mock_db):
        """Test the _grant_if_new helper method."""
        # Test when achievement is new
        mock_db.grant_achievement.return_value = True
        result = await checker._grant_if_new(123, 'test_achievement')
        assert result is True
        
        # Test when user already has achievement
        mock_db.grant_achievement.return_value = False
        result = await checker._grant_if_new(123, 'test_achievement')
        assert result is False