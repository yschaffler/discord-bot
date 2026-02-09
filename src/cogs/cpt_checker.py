from discord.ext import commands, tasks
import discord
import logging
import aiohttp
import os
from datetime import datetime, timedelta, timezone
from src.config import TRAINING_API_URL, CPT_CHANNEL_ID, TRAINING_API_TOKEN, FIR_PREFIXES, CPT_ROLE_ID

logger = logging.getLogger("CPTChecker")

class CPTChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cpts_announced = {} # Keep track of announced IDs to avoid duplicates in a single run: {key: expiry_date_iso}
        self.cpt_check_loop.start()
        self.fir_prefixes = FIR_PREFIXES

    def cog_unload(self):
        self.cpt_check_loop.cancel()

    async def fetch_cpts(self):
        """Fetches CPTs from API."""

        try:
            headers = {}
            if TRAINING_API_TOKEN:
                headers["Authorization"] = f"Bearer {TRAINING_API_TOKEN}"
                
            async with aiohttp.ClientSession() as session:
                async with session.get(TRAINING_API_URL, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch CPTs: {response.status}")
                        return []
                    data = await response.json()
                    return data.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching CPTs: {e}")
            return []

    @tasks.loop(hours=3)
    async def cpt_check_loop(self):
        logger.info("Checking for CPTs...")
        # self.load_announced_cpts() # Removed to prevent overwriting in-memory state
        self.cleanup_old_cpts()
        cpts = await self.fetch_cpts()
        await self.process_cpts(cpts)
        self.save_announced_cpts()

    async def process_cpts(self, cpts):
        now = datetime.now(timezone.utc)
        
        for cpt in cpts:
            position = cpt.get("position", "")
            
            # Check if position starts with any of the allowed prefixes
            is_in_fir = False
            for prefix in self.fir_prefixes:
                if position.startswith(prefix):
                    is_in_fir = True
                    break
            
            if not is_in_fir:
                continue


            cpt_date_str = cpt.get("date")
            if not cpt_date_str:
                continue

            try:
                cpt_date = datetime.fromisoformat(cpt_date_str)
            except ValueError:
                logger.error(f"Invalid date format: {cpt_date_str}")
                continue
            
            time_diff = cpt_date - now
            days_diff = time_diff.days

            cpt_id = str(cpt.get("id"))
            
            # Notification Types
            notification_type = None
            title = ""
            hours_left = time_diff.total_seconds() / 3600

            # "Today/Now" Notification (approx 0 to 12 hours before)
            if 0 < hours_left <= 12:
                notification_type = "today"
                title = "CPT Heute!"
            
            # "Upcoming" Notification (approx 12 to 73 hours before)
            # We check if we already sent the '3day' (upcoming) notification.
            # If not, we send it now, regardless of whether it is exactly 72h or just 24h before.
            elif 12 < hours_left <= 73:
                notification_type = "3day" 
                # Calculate simple days difference for display
                if days_diff == 0:
                     title = "CPT Morgen!"
                else:
                     title = f"CPT in {days_diff} Tagen!"

            if notification_type:
                # Key for persistence: "ID_TYPE" e.g. "139_3day"
                key = f"{cpt_id}_{notification_type}"
                
                # Check if already announced
                if key not in self.cpts_announced:
                    if await self.send_notification(cpt, title):
                         self.cpts_announced[key] = cpt_date_str

    def load_announced_cpts(self):
        try:
            if os.path.exists("data/cpts.json"):
                import json
                with open("data/cpts.json", "r") as f:
                    data = json.load(f)
                    
                    # Migration Logic: Convert list to dict if necessary
                    if isinstance(data, list):
                        logger.info("Migrating cpts.json from list to dict format.")
                        # We don't have dates for old entries, so we can't efficiently clean them up yet.
                        # We'll just migrate them with a dummy past date or keep them as keys with None, 
                        # but to be safe and allow cleanup, we might just clear them or set a far future date?
                        # Better approach: Set them to expiring soon or just keep them without date 
                        # and let cleanup handle 'None' if we wanted, but simplest is to just start fresh 
                        # OR migrate as keys with a flag. 
                        # Let's map them to a localized "now" so they eventually get cleaned up if we implement a timeout, 
                        # or just don't clean them up if they lack a date?
                        # DECISION: Convert to dict with None date. Cleanup will skip or remove None dates?
                        # Actually, if we don't know the date, we can't verify if it's passed.
                        # Let's just import them as keys.
                        self.cpts_announced = {k: None for k in data}
                    elif isinstance(data, dict):
                         self.cpts_announced = data
                    else:
                        logger.warning("cpts.json format unrecognized. Starting with empty record.")
                        self.cpts_announced = {}
            else:
                self.cpts_announced = {}

        except Exception as e:
            logger.error(f"Failed to load announced CPTs: {e}")
            self.cpts_announced = {}

    def save_announced_cpts(self):
        try:
            import json
            os.makedirs("data", exist_ok=True)
            with open("data/cpts.json", "w") as f:
                json.dump(self.cpts_announced, f)
        except Exception as e:
            logger.error(f"Failed to save announced CPTs: {e}")

    def cleanup_old_cpts(self):
        """Removes CPTs that have already passed from the announced list."""
        try:
            now = datetime.now(timezone.utc)
            keys_to_remove = []
            
            for key, date_str in self.cpts_announced.items():
                if date_str is None:
                    # Legacy data without date.
                    # Optional: Remove if we want to enforce cleanup, or keep until manual purge.
                    # Let's keep them to avoid re-announcing if the bot restarts quickly after migration.
                    continue
                
                try:
                    event_date = datetime.fromisoformat(date_str)
                    # If event is in the past (plus a buffer, e.g., 1 day), remove it
                    if event_date + timedelta(days=1) < now:
                        keys_to_remove.append(key)
                except ValueError:
                    # Invalid date format, remove to be safe
                    keys_to_remove.append(key)
            
            if keys_to_remove:
                logger.info(f"Cleaning up {len(keys_to_remove)} old CPT entries.")
                for k in keys_to_remove:
                    del self.cpts_announced[k]
                self.save_announced_cpts()
                
        except Exception as e:
            logger.error(f"Error during CPT cleanup: {e}")

    @commands.hybrid_command(name="testcpt", description="Manually triggers the CPT check.")
    async def test_cpt_manual(self, ctx):
        """Manually triggers the CPT check."""
        # Defer response since it might take a while
        await ctx.defer()
        
        logger.info("Manual CPT check triggered by user.")
        try:
            cpts = await self.fetch_cpts()

            count_before = len(self.cpts_announced)
            await self.process_cpts(cpts)
            count_after = len(self.cpts_announced)
            
            if count_after > count_before:
                self.save_announced_cpts()
                await ctx.send(f"Fertig. {count_after - count_before} neue Benachrichtigungen gesendet.")
            else:
                 msg = "Fertig. Keine neues CPTs gefunden."
                 await ctx.send(msg)

        except Exception as e:
            logger.error(f"Error in manual CPT check: {e}")
            await ctx.send(f"Fehler aufgetreten: {e}")

    async def send_notification(self, cpt, title_prefix):
        channel = self.bot.get_channel(CPT_CHANNEL_ID)
        if not channel:
            logger.warning(f"Channel {CPT_CHANNEL_ID} not found.")
            return

        embed = discord.Embed(
            title=f"{title_prefix}: {cpt.get('course_name')}",
            description=f"Ein neues CPT steht an!",
            color=discord.Color.blue(),
            timestamp=datetime.fromisoformat(cpt.get('date')).replace(tzinfo=None)
        )
        embed.add_field(name="Trainee", value=f"{cpt.get('trainee_name')} ({cpt.get('trainee_vatsim_id')})", inline=True)
        embed.add_field(name="Position", value=cpt.get('position'), inline=True)
        embed.add_field(name="Mentor", value=f"{cpt.get('local_name')}", inline=True)
        
        message = ""
        role_id = CPT_ROLE_ID
        if role_id:
            message = f"<@&{role_id}> "
        try:
            await channel.send(content=message, embed=embed)
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    @cpt_check_loop.before_loop
    async def before_cpt_check(self):
        await self.bot.wait_until_ready()
        # Load once here to ensure in-memory state is primed before loop starts
        self.load_announced_cpts()

async def setup(bot):
    await bot.add_cog(CPTChecker(bot))
