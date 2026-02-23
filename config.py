"""
Seth Bot Configuration
Loads environment variables and bot settings
"""
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
# Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
# Database Configuration
DATABASE_PATH = 'data/seth.db'
# Game Configuration
STARTING_HEALTH = 100
STARTING_HUNGER = 0
MAX_HUNGER = 100
MINE_COOLDOWN = 60  # seconds
PREMIUM_MINE_COOLDOWN = 30  # seconds for premium users

def verify_token():
    """Call this before starting the bot, not on import"""
    if not DISCORD_TOKEN:
        raise ValueError("No Discord token found! Add DISCORD_TOKEN to .env file")
    print(f"✅ Config loaded! Prefix: {BOT_PREFIX}")
