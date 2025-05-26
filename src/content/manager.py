"""
Content manager for Hippo bot - handles poems, images, and themes.
"""

import random
from typing import List, Dict, Any
from pathlib import Path


class ContentManager:
    """Manages content for the Hippo bot including poems and images."""
    
    def __init__(self):
        """Initialize the content manager."""
        self.themes = self._load_themes()
        self.poems = self._load_poems()
        self.confirmation_messages = self._load_confirmation_messages()
    
    def _load_themes(self) -> Dict[str, List[str]]:
        """Load image themes configuration."""
        # Default theme with placeholder images
        return {
            "default": [
                "dehydrated.png",      # 0% - Very dehydrated
                "low_hydration.png",   # 20% - Low hydration  
                "moderate.png",        # 40% - Moderate
                "good_hydration.png",  # 60% - Good hydration
                "great_hydration.png", # 80% - Great hydration
                "perfect_hydration.png" # 100% - Fully hydrated
            ]
        }
    
    def _load_poems(self) -> List[str]:
        """Load hydration poems."""
        return [
            "💧 *Time for Water!*\n\nDrop by drop, sip by sip,\nHydration's on this wellness trip.\nYour body calls, don't make it wait,\nDrink water now, it's never too late! 🦛",
            
            "🌊 *Hydration Station*\n\nLike rivers flow and oceans dance,\nGive your cells a fighting chance.\nA glass of water, clear and bright,\nKeeps your body feeling right! 💙",
            
            "💦 *Wellness Reminder*\n\nEvery cell deserves a drink,\nPause a moment, stop and think.\nNature's gift so pure and free,\nWater brings vitality! 🌿",
            
            "🏊 *Liquid Life*\n\nFrom mountain springs to morning dew,\nFresh water waits to nourish you.\nTake a moment, take a sip,\nHydration's your wellness trip! ⛰️",
            
            "💧 *Thirst No More*\n\nWhen your hippo friend reminds,\nIt's water time for hearts and minds.\nRefresh, renew, and feel so bright,\nHydration makes everything right! ✨",
            
            "🌺 *Daily Dose*\n\nLike flowers need the morning rain,\nYour body needs water again.\nSip slowly, breathe, and take your time,\nHydration's rhythm, so sublime! 🌸"
        ]
    
    def _load_confirmation_messages(self) -> List[str]:
        """Load confirmation messages for different hydration levels."""
        return [
            "You're taking great steps toward better hydration! 🌱",
            "Your body thanks you for that refreshing drink! 💧", 
            "Excellent! Keep up the good hydration habits! ⭐",
            "Way to go! Your cells are dancing with joy! 💃",
            "Fantastic! You're becoming a hydration champion! 🏆",
            "Amazing work! You're glowing with good health! ✨"
        ]
    
    def get_random_poem(self) -> str:
        """Get a random hydration poem."""
        return random.choice(self.poems)
    
    def get_image_for_hydration_level(self, level: int, theme: str = "default") -> str:
        """Get image filename for the given hydration level and theme."""
        if theme not in self.themes:
            theme = "default"
        
        # Ensure level is within valid range
        level = max(0, min(5, level))
        
        return self.themes[theme][level]
    
    def get_confirmation_message(self, hydration_level: int) -> str:
        """Get a confirmation message appropriate for the hydration level."""
        # Use hydration level to influence message selection
        if hydration_level >= 4:
            messages = self.confirmation_messages[3:]  # More enthusiastic messages
        elif hydration_level >= 2:
            messages = self.confirmation_messages[1:4]  # Moderate encouragement
        else:
            messages = self.confirmation_messages[:3]   # Gentle encouragement
        
        return random.choice(messages)
    
    def get_reminder_content(self, hydration_level: int, theme: str = "default") -> Dict[str, Any]:
        """Get complete reminder content (poem + image) for a user."""
        return {
            "poem": self.get_random_poem(),
            "image": self.get_image_for_hydration_level(hydration_level, theme),
            "hydration_level": hydration_level
        }
    
    def add_theme(self, theme_name: str, image_list: List[str]) -> bool:
        """Add a new theme with 6 images for different hydration levels."""
        if len(image_list) != 6:
            return False
        
        self.themes[theme_name] = image_list
        return True
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self.themes.keys())
    
    def create_placeholder_images(self) -> None:
        """Create placeholder image files for development."""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create assets/images directory if it doesn't exist
        assets_dir = Path("assets/images")
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Hydration levels and colors
        levels = [
            ("dehydrated", "#FF6B6B", "😵"),
            ("low_hydration", "#FFA726", "😟"), 
            ("moderate", "#FFEB3B", "😐"),
            ("good_hydration", "#66BB6A", "😊"),
            ("great_hydration", "#42A5F5", "😄"),
            ("perfect_hydration", "#7E57C2", "🤩")
        ]
        
        for filename, color, emoji in levels:
            # Create a simple colored image with emoji
            img = Image.new('RGB', (200, 200), color)
            draw = ImageDraw.Draw(img)
            
            # Add emoji text (simplified - may not render perfectly)
            try:
                draw.text((100, 100), emoji, fill='white', anchor='mm')
            except:
                # Fallback to simple text if emoji doesn't work
                draw.text((100, 100), filename.replace('_', ' ').title(), 
                         fill='white', anchor='mm')
            
            # Save placeholder image
            img.save(assets_dir / f"{filename}.png")
        
        print(f"Created placeholder images in {assets_dir}")


# Create a global instance for easy access
content_manager = ContentManager()