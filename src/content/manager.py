"""
Content manager for Hippo bot - handles poems, images, and themes.
"""

import random
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx


class ContentManager:
    """Manages content for the Hippo bot including poems and images."""
    
    def __init__(self):
        """Initialize the content manager."""
        self.themes = self._load_themes()
        self.fallback_poems = self._load_poems()  # Renamed for clarity
        self.confirmation_messages = self._load_confirmation_messages()
        self.recent_poems = []  # Track recently used poems to avoid repetition
        
        # Dynamic poem system
        self.poem_cache = []  # Cache of fetched poems from PoetryDB
        self.cache_size = 20  # Number of poems to keep in cache
        self.poetrydb_url = "https://poetrydb.org/random,linecount/{};4"
        self.api_timeout = 5.0  # 5 second timeout for API calls
        self.logger = logging.getLogger(__name__)
    
    def _load_themes(self) -> Dict[str, List[str]]:
        """Load image themes configuration."""
        # Order mapping: 0_0, 1_0, 0_1, 1_1, 0_2, 1_2 corresponds to hydration levels 0-5
        return {
            "bluey": [
                "bluey/tile_0_0.png",  # Level 0 - Dehydrated
                "bluey/tile_1_0.png",  # Level 1 - Low hydration
                "bluey/tile_0_1.png",  # Level 2 - Moderate
                "bluey/tile_1_1.png",  # Level 3 - Good hydration
                "bluey/tile_0_2.png",  # Level 4 - Great hydration
                "bluey/tile_1_2.png"   # Level 5 - Perfect hydration
            ],
            "desert": [
                "desert/tile_0_0.png", # Level 0 - Dehydrated
                "desert/tile_1_0.png", # Level 1 - Low hydration
                "desert/tile_0_1.png", # Level 2 - Moderate
                "desert/tile_1_1.png", # Level 3 - Good hydration
                "desert/tile_0_2.png", # Level 4 - Great hydration
                "desert/tile_1_2.png"  # Level 5 - Perfect hydration
            ],
            "spring": [
                "spring/tile_0_0.png", # Level 0 - Dehydrated
                "spring/tile_1_0.png", # Level 1 - Low hydration
                "spring/tile_0_1.png", # Level 2 - Moderate
                "spring/tile_1_1.png", # Level 3 - Good hydration
                "spring/tile_0_2.png", # Level 4 - Great hydration
                "spring/tile_1_2.png"  # Level 5 - Perfect hydration
            ],
            "vivid": [
                "vivid/tile_0_0.png",  # Level 0 - Dehydrated
                "vivid/tile_1_0.png",  # Level 1 - Low hydration
                "vivid/tile_0_1.png",  # Level 2 - Moderate
                "vivid/tile_1_1.png",  # Level 3 - Good hydration
                "vivid/tile_0_2.png",  # Level 4 - Great hydration
                "vivid/tile_1_2.png"   # Level 5 - Perfect hydration
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
            
            "🌺 *Daily Dose*\n\nLike flowers need the morning rain,\nYour body needs water again.\nSip slowly, breathe, and take your time,\nHydration's rhythm, so sublime! 🌸",
            
            "🦛 *Hippo's Wisdom*\n\nJust like hippos love the stream,\nWater makes your body gleam.\nTake a break from work or play,\nHydrate yourself throughout the day! 💫",
            
            "🌈 *Rainbow Refresh*\n\nAfter rain comes colors bright,\nWater brings your cells delight.\nEach sip a step to feeling great,\nDon't let hydration come too late! 🌤️",
            
            "🎯 *Target: Hydration*\n\nYour mission, should you choose to accept:\nDrink water with no regret!\nYour body's counting on you now,\nTake a water-drinking vow! 🎪",
            
            "🌙 *Moonlit Sips*\n\nDay or night, the rule's the same,\nHydration is the winning game.\nLet water be your faithful friend,\nFrom morning start to evening's end! ⭐",
            
            "🎨 *Aqua Art*\n\nPaint your health with water clear,\nEvery drop brings wellness near.\nYour masterpiece needs H2O,\nWatch your energy levels grow! 🖌️",
            
            "🚀 *Hydration Launch*\n\nCountdown starts: 3... 2... 1...\nWater time has just begun!\nFuel your body's inner space,\nHydration at a steady pace! 🛸",
            
            "🎵 *Water Symphony*\n\nListen to your body's song,\nIt's been singing all along:\n'Water, water, crystal clear,\nBring me health throughout the year!' 🎶",
            
            "🌸 *Blossom & Bloom*\n\nLike a garden needs the rain,\nWater soothes away the strain.\nBloom with health, grow strong and tall,\nHydration conquers all! 🌻",
            
            "⚡ *Energy Boost*\n\nFeeling sluggish? Here's the key:\nWater sets your energy free!\nNo more fatigue, no more yawns,\nHydration brings the brightest dawns! 🌅",
            
            "🎭 *Hydration Theater*\n\nLife's a stage, and you're the star,\nWater helps you go so far.\nTake your cue, don't miss your line:\n'It's always water-drinking time!' 🎬",
            
            "🏖️ *Beach Vibes*\n\nWaves of wellness wash ashore,\nEvery sip brings so much more.\nSurf the tide of good hydration,\nJoin the water celebration! 🏄",
            
            "🔮 *Crystal Clear*\n\nGaze into your water glass,\nSee your healthy future pass.\nDestiny says 'Hydrate well!'\nBreak dehydration's spell! ✨",
            
            "🎪 *Circus of Sips*\n\nStep right up, don't be shy,\nWater's here to satisfy!\nThe greatest show for health on Earth,\nDiscover hydration's worth! 🤹",
            
            "🌿 *Nature's Call*\n\nBirds and bees all know it's true,\nWater's essential through and through.\nAnswer nature's gentle plea,\nSip some water, wild and free! 🦋",
            
            "🎈 *Balloon of Bliss*\n\nFill your body like a balloon,\nWater makes you feel in tune.\nRise above the daily stress,\nHydration brings pure happiness! 🎉",
            
            "🌊 *Ocean of Opportunity*\n\nDive deep into wellness today,\nLet water wash fatigue away.\nSurf the waves of energy new,\nHydration's calling out to you! 🏄‍♀️",
            
            "🎯 *Bullseye Hydration*\n\nAim for health with every sip,\nWater's your championship chip.\nHit the target, feel the rush,\nNo more thirst, no need to crush! 🏹",
            
            "🌅 *Dawn of Wellness*\n\nSunrise brings a brand new day,\nStart it right the water way.\nGolden light and crystal clear,\nHydration makes the path appear! ☀️",
            
            "🎠 *Carousel of Care*\n\nRound and round, the water flows,\nWhere it stops, your wellness grows.\nTake a ride on health's bright track,\nHydration keeps you on the back! 🎪",
            
            "🌟 *Stellar Sipping*\n\nLike the stars that light the night,\nWater makes your future bright.\nNavigate through life with ease,\nHydration is your master key! 🔑",
            
            "🦋 *Butterfly Effect*\n\nOne small sip can change your day,\nChase the sluggish blues away.\nSpread your wings and feel so light,\nWater makes everything right! 💫",
            
            "🎨 *Palette of Purity*\n\nMix your colors with H2O,\nWatch your energy levels grow.\nBrush away fatigue and pain,\nPaint your life with water's gain! 🖼️",
            
            "🌸 *Cherry Blossom Dreams*\n\nPetals fall like drops of dew,\nNature's message straight to you:\nBeauty comes from being well,\nLet hydration cast its spell! 🌺",
            
            "🎵 *Rhythm & Hydration*\n\nTap your feet to water's beat,\nMake your wellness feel complete.\nDance with health throughout the day,\nLet hydration lead the way! 💃"
        ]
    
    def _load_confirmation_messages(self) -> Dict[str, List[str]]:
        """Load confirmation messages organized by hydration level."""
        return {
            "low": [
                "Great start! Every sip counts toward better hydration. 🌱💧",
                "Your body is grateful for that refreshing drink! Keep it up! 💙", 
                "Excellent choice! You're on the path to better wellness. 🎯",
                "Way to go! Your hippo friend is proud of your effort! 🦛💫",
                "Nice work! Building healthy habits one sip at a time. ✨"
            ],
            "moderate": [
                "Fantastic! You're building excellent hydration momentum! 🚀💧",
                "Your cells are celebrating that refreshing drink! 💃✨", 
                "Great progress! Your dedication to health really shows. 🌟",
                "Wonderful! You're becoming a true hydration champion! 🏆",
                "Excellent habit! Your body feels the positive energy. ⚡💙"
            ],
            "high": [
                "Outstanding! You're absolutely crushing your hydration goals! 🏆💧",
                "Incredible dedication! Your body is radiating with health! ✨🌟", 
                "You're a hydration superstar! Keep that amazing streak going! 🌈",
                "Perfect! Your commitment to wellness is truly inspiring! 💎",
                "Phenomenal work! You've mastered the art of staying hydrated! 🎉💧"
            ]
        }
    
    def _classify_poem_emoji(self, title: str, author: str, lines: List[str]) -> str:
        """Classify a poem and return an appropriate emoji based on keywords."""
        import re
        text = f"{title} {author} {' '.join(lines)}".lower()
        
        def has_word(word_list):
            """Check if any whole words from word_list are in text."""
            for word in word_list:
                if re.search(r'\b' + re.escape(word) + r'\b', text):
                    return True
            return False
        
        # Water/hydration themed emojis (most relevant)
        if has_word(['water', 'river', 'ocean', 'sea', 'rain', 'drop', 'flow', 'stream', 'wave']):
            return random.choice(['💧', '🌊', '💦', '🏊'])
        
        # Nature themed
        if has_word(['flower', 'rose', 'tree', 'garden', 'leaf', 'bloom', 'spring', 'nature']):
            return random.choice(['🌸', '🌺', '🌿', '🌱', '🌳', '🌷'])
        
        # Celestial/time themed  
        if has_word(['moon', 'star', 'sun', 'night', 'dawn', 'morning', 'evening']):
            return random.choice(['🌙', '🌟', '🌅', '⭐', '☀️'])
        
        # Joy/celebration themed
        if has_word(['joy', 'happy', 'celebration', 'dance', 'song', 'music', 'laugh']):
            return random.choice(['🎉', '🎵', '💃', '🎭', '🎪'])
        
        # Love/heart themed
        if has_word(['love', 'heart', 'dear', 'sweet', 'beauty', 'beautiful']):
            return random.choice(['💕', '💖', '💝', '❤️'])
        
        # Adventure/journey themed
        if has_word(['journey', 'road', 'path', 'travel', 'adventure', 'mountain']):
            return random.choice(['🗺️', '⛰️', '🚀', '🎯'])
        
        # Death/memorial themed
        if has_word(['death', 'die', 'grave', 'tomb', 'funeral', 'memory', 'farewell', 'goodbye']):
            return random.choice(['🕯️', '⚰️', '🌹', '🙏', '😢'])
        
        # War/conflict themed
        if has_word(['war', 'battle', 'fight', 'soldier', 'sword', 'conflict', 'victory', 'defeat']):
            return random.choice(['⚔️', '🛡️', '🏺', '⚡', '🔥'])
        
        # Wisdom/philosophy themed
        if has_word(['wisdom', 'truth', 'knowledge', 'think', 'mind', 'soul', 'spirit', 'philosophy']):
            return random.choice(['🧠', '💭', '📚', '🔮', '⚖️'])
        
        # Animals/creatures themed
        if has_word(['bird', 'cat', 'dog', 'horse', 'lion', 'wolf', 'deer', 'rabbit', 'mouse']):
            return random.choice(['🐦', '🦅', '🐺', '🦌', '🐰', '🐱', '🐴'])
        
        # Food/feast themed
        if has_word(['food', 'bread', 'wine', 'feast', 'drink', 'eat', 'hunger', 'fruit', 'apple']):
            return random.choice(['🍎', '🍞', '🍷', '🍯', '🥖', '🍇'])
        
        # Work/labor themed
        if has_word(['work', 'labor', 'toil', 'craft', 'build', 'create', 'make', 'forge', 'tool']):
            return random.choice(['🔨', '⚙️', '🛠️', '👷', '🏗️', '⚒️'])
        
        # Fire/heat themed
        if has_word(['fire', 'flame', 'burn', 'hot', 'heat', 'warm', 'ember', 'blaze', 'light']):
            return random.choice(['🔥', '🕯️', '💡', '🌋', '☄️', '✨'])
        
        # Cold/winter themed
        if has_word(['cold', 'ice', 'snow', 'winter', 'frost', 'freeze', 'chill', 'frozen']):
            return random.choice(['❄️', '🧊', '🌨️', '⛄', '🥶', '🌬️'])
        
        # Time/age themed
        if has_word(['time', 'age', 'old', 'young', 'past', 'future', 'year', 'hour', 'clock']):
            return random.choice(['⏰', '⌛', '🕐', '📅', '⏳', '🔄'])
        
        # Magic/mystery themed
        if has_word(['magic', 'spell', 'witch', 'mystery', 'secret', 'enchant', 'curse', 'fortune']):
            return random.choice(['🔮', '✨', '🎩', '🃏', '🌟', '🪄'])
        
        # Default water-related emoji for hydration context
        return random.choice(['💧', '🎭', '📜', '✨'])
    
    async def _fetch_poems_from_api(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch poems from PoetryDB API."""
        try:
            url = self.poetrydb_url.format(count)
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                poems_data = response.json()
                formatted_poems = []
                
                for poem_data in poems_data:
                    if poem_data.get('title') and poem_data.get('author') and poem_data.get('lines'):
                        emoji = self._classify_poem_emoji(
                            poem_data['title'], 
                            poem_data['author'], 
                            poem_data['lines']
                        )
                        
                        # Format similar to our existing poems
                        formatted_poem = f"{emoji} *{poem_data['title']}*\n\n"
                        formatted_poem += "\n".join(poem_data['lines'])
                        formatted_poem += f"\n\n— _{poem_data['author']}_"
                        
                        formatted_poems.append(formatted_poem)
                
                self.logger.info(f"Successfully fetched {len(formatted_poems)} poems from PoetryDB")
                return formatted_poems
                
        except Exception as e:
            self.logger.warning(f"Failed to fetch poems from PoetryDB: {e}")
            return []
    
    async def _replenish_poem_cache(self):
        """Replenish the poem cache when it's running low."""
        if len(self.poem_cache) < 5:  # Replenish when cache is low
            new_poems = await self._fetch_poems_from_api(self.cache_size)
            self.poem_cache.extend(new_poems)
            self.logger.info(f"Replenished poem cache. Now has {len(self.poem_cache)} poems")
    
    async def get_random_poem_async(self) -> str:
        """Get a random poem (async version) - tries API first, falls back to hardcoded."""
        try:
            # Try to replenish cache if needed
            await self._replenish_poem_cache()
            
            # Use cached poem if available
            if self.poem_cache:
                # Remove poem from cache to avoid repetition
                poem = self.poem_cache.pop(0)
                return poem
            
        except Exception as e:
            self.logger.warning(f"Error with dynamic poem system: {e}")
        
        # Fallback to hardcoded poems
        self.logger.info("Using fallback poems")
        return self._get_fallback_poem()
    
    def _get_fallback_poem(self) -> str:
        """Get a poem from the fallback collection."""
        # If we've used more than half the poems, reset to allow all again
        if len(self.recent_poems) >= len(self.fallback_poems) // 2:
            self.recent_poems = self.recent_poems[-3:]  # Keep only last 3
        
        # Get available poems (not recently used)
        available_poems = [poem for poem in self.fallback_poems if poem not in self.recent_poems]
        
        # If somehow all poems are recent (shouldn't happen), use all poems
        if not available_poems:
            available_poems = self.fallback_poems
        
        # Select a random poem from available ones
        selected_poem = random.choice(available_poems)
        
        # Track this poem as recently used
        self.recent_poems.append(selected_poem)
        
        return selected_poem
    
    def get_random_poem(self) -> str:
        """Get a random poem (sync wrapper) - tries API first, falls back to hardcoded."""
        try:
            # Try to run the async version
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.get_random_poem_async())
                    return future.result(timeout=self.api_timeout + 1)
            else:
                # We can run async directly
                return asyncio.run(self.get_random_poem_async())
        except Exception as e:
            self.logger.warning(f"Failed to get dynamic poem: {e}")
            # Fallback to hardcoded poems
            return self._get_fallback_poem()
    
    def get_image_for_hydration_level(self, level: int, theme: str = "bluey") -> str:
        """Get image filename for the given hydration level and theme."""
        if theme not in self.themes:
            theme = "bluey"  # Default to bluey theme
        
        # Ensure level is within valid range
        level = max(0, min(5, level))
        
        return self.themes[theme][level]
    
    def get_confirmation_message(self, hydration_level: int) -> str:
        """Get a confirmation message appropriate for the hydration level."""
        # Select message category based on hydration level
        if hydration_level >= 4:
            category = "high"    # Levels 4-5: Enthusiastic messages
        elif hydration_level >= 2:
            category = "moderate"  # Levels 2-3: Encouraging messages
        else:
            category = "low"     # Levels 0-1: Gentle encouragement
        
        return random.choice(self.confirmation_messages[category])
    
    def get_reminder_content(self, hydration_level: int, theme: str = "bluey") -> Dict[str, Any]:
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
    


# Create a global instance for easy access
content_manager = ContentManager()