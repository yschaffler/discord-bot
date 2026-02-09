import discord
from discord.ext import commands
import logging

import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
if not os.path.exists("data/logs"):
    os.makedirs("data/logs")

# Configure Logging
logger = logging.getLogger("DiscordBot")
logger.setLevel(logging.INFO)

# File Handler
file_handler = RotatingFileHandler("data/logs/bot.log", maxBytes=5*1024*1024, backupCount=5)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console Handler
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

class EventManagerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # intents.message_content = True # Requires "Message Content Intent" in Developer Portal
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Load cogs here
        await self.load_extension("src.cogs.cpt_checker")
        await self.load_extension("src.cogs.event_bridge")
        
        # Sync commands with Discord (global sync might take an hour, instant for guild)
        # For development, syncing universally is fine but be aware of rate limits.
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
            
        logger.info("Cogs loaded.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
