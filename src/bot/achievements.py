"""
Achievement system for Hippo bot.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class Achievement:
    """Represents an achievement that users can earn."""
    code: str
    name: str
    description: str
    icon: str
    category: str  # 'easy', 'consistency', 'performance', 'special', 'milestone'
    hidden: bool = False  # Hidden achievements aren't shown until earned


# Achievement definitions
ACHIEVEMENTS = {
    # Easy achievements - designed to be earned quickly
    'first_sip': Achievement(
        code='first_sip',
        name='First Sip',
        description='Confirm your first water reminder',
        icon='💧',
        category='easy'
    ),
    'getting_started': Achievement(
        code='getting_started',
        name='Getting Started',
        description='Complete 5 water confirmations',
        icon='🚰',
        category='easy'
    ),
    'hydration_habit': Achievement(
        code='hydration_habit',
        name='Hydration Habit',
        description='Confirm 10 water reminders',
        icon='💦',
        category='easy'
    ),
    'daily_dose': Achievement(
        code='daily_dose',
        name='Daily Dose',
        description='Confirm 3 reminders in a single day',
        icon='📅',
        category='easy'
    ),
    'quick_response': Achievement(
        code='quick_response',
        name='Quick Response',
        description='Confirm a reminder within 1 minute',
        icon='⚡',
        category='easy'
    ),
    
    # Consistency achievements
    'three_day_streak': Achievement(
        code='three_day_streak',
        name='Three Day Streak',
        description='Maintain a 3-day hydration streak',
        icon='🔥',
        category='consistency'
    ),
    'week_warrior': Achievement(
        code='week_warrior',
        name='Week Warrior',
        description='Achieve a 7-day hydration streak',
        icon='🗓️',
        category='consistency'
    ),
    'fortnight_champion': Achievement(
        code='fortnight_champion',
        name='Fortnight Champion',
        description='Maintain a 14-day streak',
        icon='🏆',
        category='consistency'
    ),
    'monthly_master': Achievement(
        code='monthly_master',
        name='Monthly Master',
        description='Incredible 30-day streak!',
        icon='👑',
        category='consistency'
    ),
    
    # Performance achievements
    'perfect_day': Achievement(
        code='perfect_day',
        name='Perfect Day',
        description='Confirm all reminders in a day',
        icon='💯',
        category='performance'
    ),
    'hydration_hero': Achievement(
        code='hydration_hero',
        name='Hydration Hero',
        description='Maintain 90%+ success rate (min 20 reminders)',
        icon='🦸',
        category='performance'
    ),
    'perfect_week': Achievement(
        code='perfect_week',
        name='Perfect Week',
        description='100% confirmation rate for 7 days',
        icon='🌟',
        category='performance'
    ),
    'level_five': Achievement(
        code='level_five',
        name='Maximum Hydration',
        description='Reach hydration level 5',
        icon='🌊',
        category='performance'
    ),
    
    # Special achievements
    'early_bird': Achievement(
        code='early_bird',
        name='Early Bird',
        description='Confirm a reminder before 6 AM',
        icon='🌅',
        category='special'
    ),
    'night_owl': Achievement(
        code='night_owl',
        name='Night Owl',
        description='Confirm a reminder after midnight',
        icon='🦉',
        category='special'
    ),
    'weekend_warrior': Achievement(
        code='weekend_warrior',
        name='Weekend Warrior',
        description='Perfect hydration on a weekend',
        icon='🎉',
        category='special'
    ),
    'theme_explorer': Achievement(
        code='theme_explorer',
        name='Theme Explorer',
        description='Try all available themes',
        icon='🎨',
        category='special'
    ),
    
    # Milestone achievements
    'centurion': Achievement(
        code='centurion',
        name='Centurion',
        description='Reach 100 total confirmations',
        icon='💪',
        category='milestone'
    ),
    'hydration_veteran': Achievement(
        code='hydration_veteran',
        name='Hydration Veteran',
        description='1000 confirmations! You\'re a legend!',
        icon='🎖️',
        category='milestone'
    ),
    'dedication': Achievement(
        code='dedication',
        name='Dedication',
        description='Use Hippo for 30 days',
        icon='📆',
        category='milestone'
    ),
    
    # Hidden achievements
    'poetry_lover': Achievement(
        code='poetry_lover',
        name='Poetry Lover',
        description='Request 20 poems',
        icon='📝',
        category='special',
        hidden=True
    ),
    'quote_collector': Achievement(
        code='quote_collector',
        name='Quote Collector',
        description='Request 20 quotes',
        icon='💭',
        category='special',
        hidden=True
    ),
}


class AchievementChecker:
    """Checks and awards achievements based on user actions."""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    async def check_confirmation_achievements(self, user_id: int, reminder_time: datetime = None):
        """Check achievements related to water confirmations."""
        new_achievements = []
        
        # Get total confirmations
        total_confirmations = await self.db.get_total_confirmations(user_id)
        
        # First Sip
        if total_confirmations >= 1:
            if await self._grant_if_new(user_id, 'first_sip'):
                new_achievements.append('first_sip')
        
        # Getting Started
        if total_confirmations >= 5:
            if await self._grant_if_new(user_id, 'getting_started'):
                new_achievements.append('getting_started')
        
        # Hydration Habit
        if total_confirmations >= 10:
            if await self._grant_if_new(user_id, 'hydration_habit'):
                new_achievements.append('hydration_habit')
        
        # Centurion
        if total_confirmations >= 100:
            if await self._grant_if_new(user_id, 'centurion'):
                new_achievements.append('centurion')
        
        # Hydration Veteran
        if total_confirmations >= 1000:
            if await self._grant_if_new(user_id, 'hydration_veteran'):
                new_achievements.append('hydration_veteran')
        
        # Quick Response (if reminder was confirmed within 1 minute)
        if reminder_time and (datetime.now() - reminder_time).total_seconds() <= 60:
            if await self._grant_if_new(user_id, 'quick_response'):
                new_achievements.append('quick_response')
        
        # Check time-based achievements
        current_hour = datetime.now().hour
        
        # Early Bird
        if current_hour < 6:
            if await self._grant_if_new(user_id, 'early_bird'):
                new_achievements.append('early_bird')
        
        # Night Owl
        if current_hour >= 0 and current_hour < 4:
            if await self._grant_if_new(user_id, 'night_owl'):
                new_achievements.append('night_owl')
        
        # Check daily achievements
        await self._check_daily_achievements(user_id, new_achievements)
        
        # Check performance achievements
        await self._check_performance_achievements(user_id, new_achievements)
        
        return new_achievements
    
    async def check_streak_achievements(self, user_id: int, current_streak: int):
        """Check streak-related achievements."""
        new_achievements = []
        
        if current_streak >= 3:
            if await self._grant_if_new(user_id, 'three_day_streak'):
                new_achievements.append('three_day_streak')
        
        if current_streak >= 7:
            if await self._grant_if_new(user_id, 'week_warrior'):
                new_achievements.append('week_warrior')
        
        if current_streak >= 14:
            if await self._grant_if_new(user_id, 'fortnight_champion'):
                new_achievements.append('fortnight_champion')
        
        if current_streak >= 30:
            if await self._grant_if_new(user_id, 'monthly_master'):
                new_achievements.append('monthly_master')
        
        return new_achievements
    
    async def check_level_achievements(self, user_id: int, hydration_level: int):
        """Check hydration level achievements."""
        new_achievements = []
        
        if hydration_level >= 5:
            if await self._grant_if_new(user_id, 'level_five'):
                new_achievements.append('level_five')
        
        return new_achievements
    
    async def check_theme_achievement(self, user_id: int, themes_used: set):
        """Check if user has tried all themes."""
        # This would need to track which themes the user has used
        # For now, we'll check if they've used all 4 available themes
        if len(themes_used) >= 4:
            if await self._grant_if_new(user_id, 'theme_explorer'):
                return ['theme_explorer']
        return []
    
    async def check_command_achievements(self, user_id: int, command: str):
        """Check achievements related to command usage."""
        new_achievements = []
        
        # These would need counters in the database
        # For now, we'll implement the structure
        if command == 'poem':
            # Would check poem request count
            pass
        elif command == 'quote':
            # Would check quote request count
            pass
        
        return new_achievements
    
    async def check_time_based_achievements(self, user_id: int):
        """Check achievements based on account age."""
        new_achievements = []
        
        # Get user creation date
        user = await self.db.get_user(user_id)
        if user and user.get('created_at'):
            created_at = datetime.fromisoformat(user['created_at'])
            days_active = (datetime.now() - created_at).days
            
            if days_active >= 30:
                if await self._grant_if_new(user_id, 'dedication'):
                    new_achievements.append('dedication')
        
        return new_achievements
    
    async def _check_daily_achievements(self, user_id: int, new_achievements: list):
        """Check achievements related to daily performance."""
        # Count today's confirmations
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # This would need a more specific database query
        # For now, we'll use the stats method as a proxy
        stats = await self.db.get_user_hydration_stats(user_id, days=1)
        today_confirmations = stats.get('confirmed', 0)
        
        # Daily Dose
        if today_confirmations >= 3:
            if await self._grant_if_new(user_id, 'daily_dose'):
                new_achievements.append('daily_dose')
        
        # Weekend Warrior (check if today is weekend and perfect)
        if datetime.now().weekday() >= 5:  # Saturday or Sunday
            # Would need to check if all reminders were confirmed today
            pass
    
    async def _check_performance_achievements(self, user_id: int, new_achievements: list):
        """Check performance-based achievements."""
        stats = await self.db.get_user_hydration_stats(user_id, days=7)
        total = stats['confirmed'] + stats['missed']
        
        if total >= 20:  # Minimum reminders for percentage achievements
            success_rate = stats['confirmed'] / total if total > 0 else 0
            
            # Hydration Hero
            if success_rate >= 0.9:
                if await self._grant_if_new(user_id, 'hydration_hero'):
                    new_achievements.append('hydration_hero')
            
            # Perfect Week
            if stats['missed'] == 0 and stats['confirmed'] >= 20:
                if await self._grant_if_new(user_id, 'perfect_week'):
                    new_achievements.append('perfect_week')
    
    async def _grant_if_new(self, user_id: int, achievement_code: str) -> bool:
        """Grant achievement if user doesn't already have it."""
        return await self.db.grant_achievement(user_id, achievement_code)
    
    def get_achievement_display(self, achievement_code: str) -> str:
        """Get formatted display string for an achievement."""
        achievement = ACHIEVEMENTS.get(achievement_code)
        if achievement:
            return f"{achievement.icon} {achievement.name}"
        return f"🏆 {achievement_code}"
    
    def get_achievement_details(self, achievement_code: str) -> Optional[Achievement]:
        """Get full achievement details."""
        return ACHIEVEMENTS.get(achievement_code)
    
    def get_all_achievements(self) -> Dict[str, List[Achievement]]:
        """Get all achievements grouped by category."""
        grouped = {
            'easy': [],
            'consistency': [],
            'performance': [],
            'special': [],
            'milestone': []
        }
        
        for achievement in ACHIEVEMENTS.values():
            if not achievement.hidden:  # Don't show hidden achievements
                grouped[achievement.category].append(achievement)
        
        return grouped