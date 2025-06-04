"""
Chart generation for Hippo bot progress visualizations.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import io
import logging
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional, Tuple
import calendar
import numpy as np

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates charts and visualizations for hydration data."""
    
    def __init__(self):
        """Initialize chart generator with style settings."""
        # Set matplotlib to use non-interactive backend
        plt.switch_backend('Agg')
        
        # Set up cache directory
        self.cache_dir = Path("cache/charts")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = 300  # 5 minutes cache TTL
        
        # Chart styling
        self.colors = {
            'primary': '#1E88E5',      # Blue
            'secondary': '#42A5F5',     # Light blue
            'success': '#4CAF50',       # Green
            'warning': '#FF9800',       # Orange
            'danger': '#F44336',        # Red
            'background': '#FFFFFF',    # White
            'text': '#212121',          # Dark gray
            'grid': '#E0E0E0'          # Light gray
        }
        
        # Chart dimensions (mobile-friendly)
        self.chart_size = (8, 6)  # 800x600 pixels at 100 DPI
        self.dpi = 100
        
        # Hydration level colors
        self.hydration_colors = [
            '#F44336',  # Level 0 - Red (dehydrated)
            '#FF9800',  # Level 1 - Orange (low)
            '#FFC107',  # Level 2 - Yellow (moderate)
            '#8BC34A',  # Level 3 - Light green (good)
            '#4CAF50',  # Level 4 - Green (great)
            '#2196F3'   # Level 5 - Blue (perfect)
        ]
        
        logger.info("Chart generator initialized")
    
    def _generate_cache_key(self, chart_type: str, user_id: int, **kwargs) -> str:
        """Generate a cache key for chart data."""
        # Create a string representation of all parameters
        params_str = f"{chart_type}_{user_id}_" + "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        # Hash it to create a consistent cache key
        return hashlib.md5(params_str.encode()).hexdigest()
    
    def _get_cached_chart(self, cache_key: str) -> Optional[io.BytesIO]:
        """Get cached chart if it exists and is still valid."""
        cache_file = self.cache_dir / f"{cache_key}.png"
        
        if cache_file.exists():
            # Check if cache is still valid
            file_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if file_age < self.cache_ttl:
                try:
                    with open(cache_file, 'rb') as f:
                        buf = io.BytesIO(f.read())
                        buf.seek(0)
                        logger.info(f"Serving cached chart: {cache_key}")
                        return buf
                except Exception as e:
                    logger.warning(f"Error reading cached chart {cache_key}: {e}")
        
        return None
    
    def _cache_chart(self, cache_key: str, chart_buf: io.BytesIO):
        """Cache a chart for future use."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.png"
            with open(cache_file, 'wb') as f:
                chart_buf.seek(0)
                f.write(chart_buf.read())
                chart_buf.seek(0)  # Reset for use
            logger.info(f"Cached chart: {cache_key}")
        except Exception as e:
            logger.warning(f"Error caching chart {cache_key}: {e}")
    
    def _setup_plot_style(self, fig, ax):
        """Apply consistent styling to plots."""
        # Background colors
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Grid styling
        ax.grid(True, alpha=0.3, color=self.colors['grid'])
        ax.set_axisbelow(True)
        
        # Spine styling
        for spine in ax.spines.values():
            spine.set_color(self.colors['grid'])
            spine.set_linewidth(0.5)
        
        # Text color
        ax.tick_params(colors=self.colors['text'])
        ax.xaxis.label.set_color(self.colors['text'])
        ax.yaxis.label.set_color(self.colors['text'])
        
        # Title styling
        if ax.get_title():
            ax.title.set_color(self.colors['text'])
            ax.title.set_fontweight('bold')
    
    def _save_chart_to_bytes(self, fig) -> io.BytesIO:
        """Save matplotlib figure to bytes buffer."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight', 
                   facecolor=self.colors['background'], edgecolor='none')
        buf.seek(0)
        plt.close(fig)
        return buf
    
    async def generate_daily_timeline(self, user_id: int, hydration_events: List[Dict], 
                                    current_level: int, date: datetime = None) -> io.BytesIO:
        """Generate 24-hour timeline chart showing hydration events."""
        if date is None:
            date = datetime.now()
        
        # Check cache first
        cache_key = self._generate_cache_key(
            "daily_timeline", user_id, 
            date=date.strftime('%Y-%m-%d'), 
            level=current_level,
            events_count=len(hydration_events)
        )
        
        cached_chart = self._get_cached_chart(cache_key)
        if cached_chart:
            return cached_chart
        
        fig, ax = plt.subplots(figsize=self.chart_size)
        
        # Set up 24-hour timeline
        hours = list(range(24))
        hour_labels = [f"{h:02d}:00" for h in hours]
        
        # Initialize hydration status for each hour (default to no data)
        hour_status = ['none'] * 24
        
        # Process hydration events for the specific date
        for event in hydration_events:
            event_time = datetime.fromisoformat(event['created_at'])
            if event_time.date() == date.date():
                hour = event_time.hour
                hour_status[hour] = event['event_type']
        
        # Create bar chart
        bar_colors = []
        bar_heights = []
        
        for status in hour_status:
            if status == 'confirmed':
                bar_colors.append(self.colors['success'])
                bar_heights.append(1)
            elif status == 'missed':
                bar_colors.append(self.colors['danger'])
                bar_heights.append(1)
            else:
                bar_colors.append(self.colors['grid'])
                bar_heights.append(0.3)
        
        bars = ax.bar(hours, bar_heights, color=bar_colors, alpha=0.8, width=0.8)
        
        # Styling
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Hydration Status')
        ax.set_title(f'Daily Hydration Timeline - {date.strftime("%B %d, %Y")}\n'
                    f'Current Level: {current_level}/5 💧')
        
        # Set x-axis ticks
        ax.set_xticks(range(0, 24, 3))  # Show every 3 hours
        ax.set_xticklabels([f"{h:02d}" for h in range(0, 24, 3)])
        
        # Set y-axis
        ax.set_ylim(0, 1.2)
        ax.set_yticks([0, 0.5, 1])
        ax.set_yticklabels(['No Data', 'Activity', 'Event'])
        
        # Add legend
        legend_elements = [
            plt.Rectangle((0, 0), 1, 1, facecolor=self.colors['success'], label='Confirmed'),
            plt.Rectangle((0, 0), 1, 1, facecolor=self.colors['danger'], label='Missed'),
            plt.Rectangle((0, 0), 1, 1, facecolor=self.colors['grid'], label='No Reminder')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Apply styling
        self._setup_plot_style(fig, ax)
        
        logger.info(f"Generated daily timeline chart for user {user_id} on {date.date()}")
        chart_buf = self._save_chart_to_bytes(fig)
        
        # Cache the chart
        self._cache_chart(cache_key, chart_buf)
        
        return chart_buf
    
    async def generate_weekly_trend(self, user_id: int, weekly_data: List[Dict]) -> io.BytesIO:
        """Generate 7-day trend chart showing average hydration levels."""
        # Check cache first
        data_hash = hashlib.md5(str(weekly_data).encode()).hexdigest()[:8]
        cache_key = self._generate_cache_key(
            "weekly_trend", user_id, 
            data_hash=data_hash,
            data_count=len(weekly_data)
        )
        
        cached_chart = self._get_cached_chart(cache_key)
        if cached_chart:
            return cached_chart
        
        fig, ax = plt.subplots(figsize=self.chart_size)
        
        # Prepare data
        days = []
        levels = []
        success_rates = []
        
        for day_data in weekly_data[-7:]:  # Last 7 days
            date = datetime.fromisoformat(day_data['date'])
            days.append(date.strftime('%a\n%m/%d'))
            levels.append(day_data.get('avg_level', 2))
            success_rates.append(day_data.get('success_rate', 0))
        
        # Create line chart with area fill
        x_pos = range(len(days))
        line = ax.plot(x_pos, levels, color=self.colors['primary'], linewidth=3, 
                      marker='o', markersize=8, markerfacecolor=self.colors['secondary'])
        ax.fill_between(x_pos, levels, alpha=0.3, color=self.colors['primary'])
        
        # Styling
        ax.set_xlabel('Day')
        ax.set_ylabel('Average Hydration Level')
        ax.set_title('Weekly Hydration Trend\n7-Day Progress Overview')
        
        # Set axes
        ax.set_xticks(x_pos)
        ax.set_xticklabels(days)
        ax.set_ylim(0, 5.5)
        ax.set_yticks(range(6))
        ax.set_yticklabels(['Dehydrated', 'Low', 'Moderate', 'Good', 'Great', 'Perfect'])
        
        # Add horizontal reference lines
        for level in range(6):
            ax.axhline(y=level, color=self.hydration_colors[level], alpha=0.2, linestyle='--')
        
        # Add data point labels
        for i, (level, rate) in enumerate(zip(levels, success_rates)):
            ax.annotate(f'{level:.1f}\n{rate:.0%}', 
                       xy=(i, level), xytext=(0, 10), 
                       textcoords='offset points', ha='center',
                       fontsize=9, color=self.colors['text'])
        
        # Apply styling
        self._setup_plot_style(fig, ax)
        
        logger.info(f"Generated weekly trend chart for user {user_id}")
        chart_buf = self._save_chart_to_bytes(fig)
        
        # Cache the chart
        self._cache_chart(cache_key, chart_buf)
        
        return chart_buf
    
    async def generate_monthly_calendar(self, user_id: int, monthly_data: List[Dict], 
                                      year: int, month: int) -> io.BytesIO:
        """Generate monthly calendar view with color-coded hydration levels."""
        fig, ax = plt.subplots(figsize=self.chart_size)
        
        # Get calendar data
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        # Create data lookup
        daily_data = {datetime.fromisoformat(d['date']).day: d for d in monthly_data 
                     if datetime.fromisoformat(d['date']).month == month}
        
        # Draw calendar grid
        rows = len(cal)
        cols = 7
        
        # Day labels
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                x = day_idx
                y = rows - week_idx - 1
                
                if day == 0:
                    # Empty cell
                    color = self.colors['background']
                    text_color = self.colors['background']
                    day_text = ''
                else:
                    # Get hydration data for this day
                    day_info = daily_data.get(day, {})
                    avg_level = day_info.get('avg_level', 2)
                    success_rate = day_info.get('success_rate', 0)
                    
                    # Choose color based on average hydration level
                    if avg_level >= 4.5:
                        color = self.hydration_colors[5]  # Perfect
                    elif avg_level >= 3.5:
                        color = self.hydration_colors[4]  # Great
                    elif avg_level >= 2.5:
                        color = self.hydration_colors[3]  # Good
                    elif avg_level >= 1.5:
                        color = self.hydration_colors[2]  # Moderate
                    elif avg_level >= 0.5:
                        color = self.hydration_colors[1]  # Low
                    else:
                        color = self.hydration_colors[0]  # Dehydrated
                    
                    text_color = 'white' if avg_level < 2.5 else 'black'
                    day_text = str(day)
                
                # Draw cell
                rect = Rectangle((x, y), 1, 1, facecolor=color, edgecolor='white', linewidth=2)
                ax.add_patch(rect)
                
                # Add day number
                if day_text:
                    ax.text(x + 0.5, y + 0.7, day_text, ha='center', va='center',
                           fontsize=12, fontweight='bold', color=text_color)
                    
                    # Add success rate if available
                    if day in daily_data:
                        rate_text = f'{success_rate:.0%}'
                        ax.text(x + 0.5, y + 0.3, rate_text, ha='center', va='center',
                               fontsize=8, color=text_color)
        
        # Add day labels
        for i, day_name in enumerate(day_names):
            ax.text(i + 0.5, rows + 0.2, day_name, ha='center', va='center',
                   fontsize=10, fontweight='bold', color=self.colors['text'])
        
        # Styling
        ax.set_xlim(0, 7)
        ax.set_ylim(0, rows + 0.5)
        ax.set_aspect('equal')
        ax.axis('off')
        
        ax.set_title(f'{month_name} {year} - Hydration Calendar\n'
                    f'Color indicates daily hydration level', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Add color legend
        legend_y = -0.5
        legend_spacing = 1
        for i, (level, color) in enumerate(zip(['Dehydrated', 'Low', 'Moderate', 'Good', 'Great', 'Perfect'], 
                                             self.hydration_colors)):
            x_pos = i * legend_spacing + 0.5
            rect = Rectangle((x_pos, legend_y), 0.8, 0.3, facecolor=color, edgecolor='white')
            ax.add_patch(rect)
            ax.text(x_pos + 0.4, legend_y - 0.5, level, ha='center', va='center',
                   fontsize=8, color=self.colors['text'], rotation=45)
        
        # Apply styling
        self._setup_plot_style(fig, ax)
        
        logger.info(f"Generated monthly calendar chart for user {user_id} for {month_name} {year}")
        return self._save_chart_to_bytes(fig)
    
    async def generate_success_rate_pie(self, user_id: int, stats: Dict) -> io.BytesIO:
        """Generate pie chart showing success rate statistics."""
        fig, ax = plt.subplots(figsize=self.chart_size)
        
        confirmed = stats.get('confirmed', 0)
        missed = stats.get('missed', 0)
        total = confirmed + missed
        
        if total == 0:
            # No data case
            ax.text(0.5, 0.5, 'No hydration data available\nStart confirming reminders!', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=16, color=self.colors['text'])
            ax.set_title('Hydration Success Rate', fontsize=14, fontweight='bold')
        else:
            # Calculate percentages
            confirmed_pct = (confirmed / total) * 100
            missed_pct = (missed / total) * 100
            
            # Data for pie chart
            sizes = [confirmed, missed]
            labels = [f'Confirmed\n{confirmed} ({confirmed_pct:.1f}%)', 
                     f'Missed\n{missed} ({missed_pct:.1f}%)']
            colors = [self.colors['success'], self.colors['danger']]
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='',
                                            startangle=90, textprops={'fontsize': 12})
            
            # Style the text
            for text in texts:
                text.set_color(self.colors['text'])
                text.set_fontweight('bold')
            
            # Add center text with overall success rate
            success_rate = confirmed_pct
            center_text = f'{success_rate:.1f}%\nSuccess Rate'
            ax.text(0, 0, center_text, ha='center', va='center',
                   fontsize=16, fontweight='bold', color=self.colors['text'])
            
            ax.set_title(f'Hydration Success Rate\nTotal Reminders: {total}', 
                        fontsize=14, fontweight='bold')
        
        # Apply styling
        self._setup_plot_style(fig, ax)
        
        logger.info(f"Generated success rate pie chart for user {user_id}")
        return self._save_chart_to_bytes(fig)
    
    async def generate_progress_bar(self, user_id: int, current_level: int, 
                                  target_level: int = 5) -> io.BytesIO:
        """Generate horizontal progress bar showing current hydration level."""
        # Check cache first  
        cache_key = self._generate_cache_key(
            "progress_bar", user_id, 
            level=current_level,
            target=target_level
        )
        
        cached_chart = self._get_cached_chart(cache_key)
        if cached_chart:
            return cached_chart
        
        fig, ax = plt.subplots(figsize=(8, 3))  # Wider, shorter format
        
        # Progress bar dimensions
        bar_width = 1
        bar_height = 0.3
        
        # Background bar
        background_rect = Rectangle((0, 0), target_level, bar_height, 
                                  facecolor=self.colors['grid'], alpha=0.3)
        ax.add_patch(background_rect)
        
        # Progress bar (filled portion)
        if current_level > 0:
            progress_rect = Rectangle((0, 0), current_level, bar_height,
                                    facecolor=self.hydration_colors[min(current_level, 5)])
            ax.add_patch(progress_rect)
        
        # Add level markers
        for level in range(target_level + 1):
            ax.axvline(x=level, color='white', linewidth=2)
            
            # Add level labels
            if level < target_level:
                label = ['Dehydrated', 'Low', 'Moderate', 'Good', 'Great', 'Perfect'][level]
                ax.text(level + 0.5, -0.15, label, ha='center', va='top',
                       fontsize=10, color=self.colors['text'], rotation=45)
        
        # Add water drop emojis
        for level in range(min(current_level, target_level)):
            ax.text(level + 0.5, bar_height/2, '💧', ha='center', va='center', fontsize=20)
        
        # Current level indicator
        if current_level <= target_level:
            ax.text(current_level, bar_height + 0.1, f'Level {current_level}', 
                   ha='center', va='bottom', fontsize=12, fontweight='bold',
                   color=self.colors['text'])
            
            # Arrow pointing to current level
            ax.annotate('', xy=(current_level, bar_height), xytext=(current_level, bar_height + 0.08),
                       arrowprops=dict(arrowstyle='->', color=self.colors['text'], lw=2))
        
        # Styling
        ax.set_xlim(-0.2, target_level + 0.2)
        ax.set_ylim(-0.5, 0.8)
        ax.set_aspect('equal')
        ax.axis('off')
        
        progress_pct = (current_level / target_level) * 100
        ax.set_title(f'Current Hydration Progress: {progress_pct:.0f}%\n'
                    f'Level {current_level} of {target_level}', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Apply styling
        self._setup_plot_style(fig, ax)
        
        logger.info(f"Generated progress bar chart for user {user_id} at level {current_level}")
        chart_buf = self._save_chart_to_bytes(fig)
        
        # Cache the chart
        self._cache_chart(cache_key, chart_buf)
        
        return chart_buf
    
    async def generate_stats_dashboard(self, user_id: int, stats_data: Dict) -> io.BytesIO:
        """Generate comprehensive stats dashboard with multiple metrics."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        
        # Top left: Success rate pie chart (simplified)
        confirmed = stats_data.get('confirmed', 0)
        missed = stats_data.get('missed', 0)
        total = confirmed + missed
        
        if total > 0:
            sizes = [confirmed, missed]
            colors = [self.colors['success'], self.colors['danger']]
            ax1.pie(sizes, colors=colors, startangle=90)
            success_rate = (confirmed / total) * 100
            ax1.text(0, 0, f'{success_rate:.1f}%', ha='center', va='center',
                    fontsize=14, fontweight='bold')
        ax1.set_title('Success Rate', fontweight='bold')
        
        # Top right: Current hydration level
        current_level = stats_data.get('current_level', 2)
        level_colors = [self.hydration_colors[min(i, 5)] for i in range(6)]
        bars = ax2.bar(range(6), [1]*6, color=level_colors, alpha=0.3)
        if current_level < 6:
            bars[current_level].set_alpha(1.0)
        ax2.set_xticks(range(6))
        ax2.set_xticklabels(['0', '1', '2', '3', '4', '5'])
        ax2.set_ylabel('Hydration Level')
        ax2.set_title(f'Current Level: {current_level}', fontweight='bold')
        ax2.set_ylim(0, 1.2)
        
        # Bottom left: Achievement progress
        achievement_count = stats_data.get('achievement_count', 0)
        total_achievements = 21  # From ACHIEVEMENTS in achievements.py
        achievement_pct = (achievement_count / total_achievements) * 100
        
        # Simple bar chart for achievements
        ax3.barh(['Achievements'], [achievement_pct], color=self.colors['primary'])
        ax3.set_xlim(0, 100)
        ax3.set_xlabel('Completion %')
        ax3.set_title(f'Achievements: {achievement_count}/{total_achievements}', fontweight='bold')
        ax3.text(50, 0, f'{achievement_pct:.0f}%', ha='center', va='center',
                fontweight='bold', color='white' if achievement_pct > 50 else 'black')
        
        # Bottom right: Weekly trend (simplified)
        recent_levels = stats_data.get('recent_levels', [2, 2, 3, 2, 3, 4, 3])
        days = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
        ax4.plot(days, recent_levels, marker='o', color=self.colors['primary'], linewidth=2)
        ax4.fill_between(days, recent_levels, alpha=0.3, color=self.colors['primary'])
        ax4.set_ylabel('Level')
        ax4.set_title('7-Day Trend', fontweight='bold')
        ax4.set_ylim(0, 5)
        
        # Apply styling to all subplots
        for ax in [ax1, ax2, ax3, ax4]:
            self._setup_plot_style(fig, ax)
        
        # Main title
        fig.suptitle('Hydration Dashboard', fontsize=16, fontweight='bold', y=0.95)
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        
        logger.info(f"Generated stats dashboard for user {user_id}")
        return self._save_chart_to_bytes(fig)


# Create a global instance
chart_generator = ChartGenerator()