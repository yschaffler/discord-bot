import discord
from discord.ext import commands
import logging

import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
if not os.path.exists("data/logs"):
    os.makedirs("data/logs")

# Configure ROOT logger to capture ALL logs from all modules
# This ensures CPTChecker, EventBridge, and all other loggers write to the log file
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# File Handler - writes to data/logs/bot.log
file_handler = RotatingFileHandler("data/logs/bot.log", maxBytes=5*1024*1024, backupCount=5)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

# Console Handler - writes to stdout/stderr
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO)
root_logger.addHandler(console_handler)

# Get logger for this module
logger = logging.getLogger("DiscordBot")

# Log that logging is configured
logger.info("=" * 80)
logger.info("Logging system initialized")
logger.info(f"Log file: data/logs/bot.log")
logger.info(f"Log level: INFO")
logger.info("=" * 80)

class EventManagerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # intents.message_content = True # Requires "Message Content Intent" in Developer Portal
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        logger.info("Starting bot setup...")
        
        # Load cogs here
        logger.info("Loading cogs...")
        await self.load_extension("src.cogs.cpt_checker")
        logger.info("✓ Loaded cpt_checker")
        await self.load_extension("src.cogs.event_bridge")
        logger.info("✓ Loaded event_bridge")
        
        # Sync commands with Discord (global sync might take an hour, instant for guild)
        # For development, syncing universally is fine but be aware of rate limits.
        try:
            logger.info("Syncing commands with Discord...")
            synced = await self.tree.sync()
            logger.info(f"✓ Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"✗ Failed to sync commands: {e}")
            
        logger.info("Bot setup complete. All cogs loaded.")

    async def on_ready(self):
        logger.info("=" * 80)
        logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info("=" * 80)
