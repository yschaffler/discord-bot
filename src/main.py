import asyncio
import logging
import sys
import os

# Ensure we can find src if running directly (fallback)
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bot import EventManagerBot
from src.config import DISCORD_TOKEN

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logging.error("DISCORD_TOKEN not found in environment variables.")
        exit(1)

    bot = EventManagerBot()
    bot.run(DISCORD_TOKEN)
