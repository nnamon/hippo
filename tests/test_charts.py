"""
Tests for chart generation functionality.
"""

import pytest
import io
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.content.charts import ChartGenerator


class TestChartGenerator:
    """Test chart generation functionality."""
    
    @pytest.fixture
    def chart_generator(self):
        """Create a chart generator instance."""
        return ChartGenerator()
    
    def test_chart_generator_initialization(self, chart_generator):
        """Test that chart generator initializes correctly."""
        assert chart_generator is not None
        assert chart_generator.colors is not None
        assert chart_generator.chart_size == (8, 6)
        assert chart_generator.dpi == 100
        assert len(chart_generator.hydration_colors) == 6
    
    def test_cache_key_generation(self, chart_generator):
        """Test cache key generation."""
        key1 = chart_generator._generate_cache_key("daily", 123, date="2024-01-01", level=3)
        key2 = chart_generator._generate_cache_key("daily", 123, date="2024-01-01", level=3)
        key3 = chart_generator._generate_cache_key("daily", 123, date="2024-01-02", level=3)
        
        # Same parameters should generate same key
        assert key1 == key2
        # Different parameters should generate different keys
        assert key1 != key3
        # Keys should be hash strings
        assert len(key1) == 32  # MD5 hash length
    
    @pytest.mark.asyncio
    async def test_generate_daily_timeline_no_events(self, chart_generator):
        """Test daily timeline generation with no events."""
        user_id = 123
        events = []
        current_level = 2
        date = datetime(2024, 1, 15)
        
        chart_buf = await chart_generator.generate_daily_timeline(user_id, events, current_level, date)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_daily_timeline_with_events(self, chart_generator):
        """Test daily timeline generation with hydration events."""
        user_id = 123
        events = [
            {
                'event_type': 'confirmed',
                'created_at': '2024-01-15 09:30:00',
                'reminder_id': 'test1'
            },
            {
                'event_type': 'missed',
                'created_at': '2024-01-15 14:45:00',
                'reminder_id': 'test2'
            },
            {
                'event_type': 'confirmed',
                'created_at': '2024-01-15 18:15:00',
                'reminder_id': 'test3'
            }
        ]
        current_level = 4
        date = datetime(2024, 1, 15)
        
        chart_buf = await chart_generator.generate_daily_timeline(user_id, events, current_level, date)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_weekly_trend_empty_data(self, chart_generator):
        """Test weekly trend generation with empty data."""
        user_id = 123
        weekly_data = []
        
        chart_buf = await chart_generator.generate_weekly_trend(user_id, weekly_data)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_weekly_trend_with_data(self, chart_generator):
        """Test weekly trend generation with sample data."""
        user_id = 123
        weekly_data = []
        
        # Generate 7 days of sample data
        for i in range(7):
            date = datetime.now() - timedelta(days=6-i)
            weekly_data.append({
                'date': date.isoformat(),
                'confirmed': 3 + i,
                'missed': 2 - (i % 2),
                'total': 5,
                'success_rate': (3 + i) / 5,
                'avg_level': min(5, i + 1)
            })
        
        chart_buf = await chart_generator.generate_weekly_trend(user_id, weekly_data)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_monthly_calendar(self, chart_generator):
        """Test monthly calendar generation."""
        user_id = 123
        year = 2024
        month = 1
        monthly_data = []
        
        # Generate sample data for first 15 days
        for day in range(1, 16):
            date = datetime(year, month, day)
            monthly_data.append({
                'date': date.isoformat(),
                'confirmed': 4,
                'missed': 1,
                'total': 5,
                'success_rate': 0.8,
                'avg_level': 3
            })
        
        chart_buf = await chart_generator.generate_monthly_calendar(user_id, monthly_data, year, month)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_success_rate_pie_no_data(self, chart_generator):
        """Test success rate pie chart with no data."""
        user_id = 123
        stats = {'confirmed': 0, 'missed': 0}
        
        chart_buf = await chart_generator.generate_success_rate_pie(user_id, stats)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_success_rate_pie_with_data(self, chart_generator):
        """Test success rate pie chart with data."""
        user_id = 123
        stats = {'confirmed': 8, 'missed': 2}
        
        chart_buf = await chart_generator.generate_success_rate_pie(user_id, stats)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_progress_bar(self, chart_generator):
        """Test progress bar generation."""
        user_id = 123
        current_level = 3
        target_level = 5
        
        chart_buf = await chart_generator.generate_progress_bar(user_id, current_level, target_level)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_progress_bar_full_level(self, chart_generator):
        """Test progress bar generation at full level."""
        user_id = 123
        current_level = 5
        target_level = 5
        
        chart_buf = await chart_generator.generate_progress_bar(user_id, current_level, target_level)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_generate_stats_dashboard(self, chart_generator):
        """Test stats dashboard generation."""
        user_id = 123
        stats_data = {
            'confirmed': 15,
            'missed': 5,
            'current_level': 4,
            'achievement_count': 8,
            'recent_levels': [2, 3, 3, 4, 4, 5, 4]
        }
        
        chart_buf = await chart_generator.generate_stats_dashboard(user_id, stats_data)
        
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()  # Should have chart data
        chart_buf.seek(0)
        assert chart_buf.read(4) == b'\x89PNG'  # PNG header
    
    def test_setup_plot_style(self, chart_generator):
        """Test plot styling application."""
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots()
        chart_generator._setup_plot_style(fig, ax)
        
        # Check that styling was applied
        assert fig.get_facecolor() == (1.0, 1.0, 1.0, 1.0)  # White background
        assert ax.get_facecolor() == (1.0, 1.0, 1.0, 1.0)   # White background
        
        plt.close(fig)
    
    def test_save_chart_to_bytes(self, chart_generator):
        """Test saving chart to bytes buffer."""
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        
        buf = chart_generator._save_chart_to_bytes(fig)
        
        assert isinstance(buf, io.BytesIO)
        assert buf.getvalue()  # Should have data
        buf.seek(0)
        assert buf.read(4) == b'\x89PNG'  # PNG header
    
    @pytest.mark.asyncio
    async def test_chart_caching(self, chart_generator):
        """Test chart caching functionality."""
        user_id = 123
        current_level = 3
        
        # Generate chart twice - second should be cached
        chart_buf1 = await chart_generator.generate_progress_bar(user_id, current_level)
        chart_buf2 = await chart_generator.generate_progress_bar(user_id, current_level)
        
        # Both should be valid charts
        assert isinstance(chart_buf1, io.BytesIO)
        assert isinstance(chart_buf2, io.BytesIO)
        
        # Content should be the same (both PNG)
        chart_buf1.seek(0)
        chart_buf2.seek(0)
        assert chart_buf1.read(4) == b'\x89PNG'
        assert chart_buf2.read(4) == b'\x89PNG'
    
    def test_cache_operations(self, chart_generator):
        """Test cache get/set operations."""
        cache_key = "test_cache_key"
        
        # Test cache miss
        cached_chart = chart_generator._get_cached_chart(cache_key)
        assert cached_chart is None
        
        # Create a sample chart buffer
        sample_buf = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'test_data')
        
        # Cache the chart
        chart_generator._cache_chart(cache_key, sample_buf)
        
        # Test cache hit
        cached_chart = chart_generator._get_cached_chart(cache_key)
        assert cached_chart is not None
        assert isinstance(cached_chart, io.BytesIO)
        
        # Verify content
        cached_chart.seek(0)
        sample_buf.seek(0)
        assert cached_chart.read() == sample_buf.read()


class TestChartIntegration:
    """Test chart generation integration with other components."""
    
    @pytest.mark.asyncio
    async def test_chart_generator_error_handling(self):
        """Test chart generator handles errors gracefully."""
        chart_generator = ChartGenerator()
        
        # Test with invalid data types
        try:
            # This should not crash the system
            await chart_generator.generate_daily_timeline(
                user_id="invalid",  # Should be int
                hydration_events=[],
                current_level=3
            )
        except Exception as e:
            # Should handle gracefully without system crash
            assert isinstance(e, (TypeError, ValueError))
    
    @pytest.mark.asyncio 
    async def test_chart_with_extreme_data(self):
        """Test chart generation with extreme data values."""
        chart_generator = ChartGenerator()
        
        # Test with very high numbers
        stats_data = {
            'confirmed': 10000,
            'missed': 5000,
            'current_level': 5,
            'achievement_count': 21,
            'recent_levels': [5, 5, 5, 5, 5, 5, 5]
        }
        
        chart_buf = await chart_generator.generate_stats_dashboard(999999, stats_data)
        assert isinstance(chart_buf, io.BytesIO)
        assert chart_buf.getvalue()
    
    @pytest.mark.asyncio
    async def test_concurrent_chart_generation(self):
        """Test concurrent chart generation doesn't cause issues."""
        import asyncio
        
        chart_generator = ChartGenerator()
        
        # Generate multiple charts concurrently
        tasks = []
        for i in range(5):
            tasks.append(chart_generator.generate_progress_bar(user_id=i, current_level=i % 6))
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 5
        for result in results:
            assert isinstance(result, io.BytesIO)
            assert result.getvalue()