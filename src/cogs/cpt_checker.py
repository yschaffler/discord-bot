from discord.ext import commands, tasks
import discord
import logging
import aiohttp
import os
from datetime import datetime, timedelta, timezone
from src.config import TRAINING_API_URL, CPT_CHANNEL_ID, TRAINING_API_TOKEN, FIR_PREFIXES, CPT_ROLE_ID

logger = logging.getLogger("CPTChecker")

# Constants
MAX_ERROR_RESPONSE_LENGTH = 500  # Maximum characters to log from error responses

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
                logger.info(f"Using Bearer token authentication (token length: {len(TRAINING_API_TOKEN)})")
            else:
                logger.warning("No TRAINING_API_TOKEN configured - API may reject request")
            
            logger.info(f"Fetching CPTs from {TRAINING_API_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(TRAINING_API_URL, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch CPTs: HTTP {response.status}")
                        response_text = await response.text()
                        logger.error(f"Response body: {response_text[:MAX_ERROR_RESPONSE_LENGTH]}")
                        return []
                    data = await response.json()
                    logger.info(f"Raw API response: {data}")
                    cpts = data.get("data", [])
                    logger.info(f"Fetched {len(cpts)} CPTs from API")
                    if cpts:
                        logger.info(f"Sample CPT data: {cpts[0]}")
                    return cpts
        except Exception as e:
            logger.error(f"Error fetching CPTs: {e}", exc_info=True)
            return []

    @tasks.loop(hours=3)
    async def cpt_check_loop(self):
        logger.info("=" * 80)
        logger.info("Starting scheduled CPT check (runs every 3 hours)")
        logger.info("=" * 80)
        # self.load_announced_cpts() # Removed to prevent overwriting in-memory state
        self.cleanup_old_cpts()
        cpts = await self.fetch_cpts()
        await self.process_cpts(cpts)
        self.save_announced_cpts()
        logger.info("CPT check complete")
        logger.info("=" * 80)

    async def process_cpts(self, cpts):
        now = datetime.now(timezone.utc)
        logger.info(f"Processing {len(cpts)} CPTs (current time: {now.isoformat()})")
        
        processed_count = 0
        notified_count = 0
        filtered_count = 0
        
        for cpt in cpts:
            position = cpt.get("position", "")
            
            # Check if position starts with any of the allowed prefixes
            is_in_fir = False
            for prefix in self.fir_prefixes:
                if position.startswith(prefix):
                    is_in_fir = True
                    break
            
            if not is_in_fir:
                filtered_count += 1
                logger.info(f"CPT {cpt.get('id')} position '{position}' not in FIR (allowed prefixes: {self.fir_prefixes}), skipping")
                continue

            processed_count += 1

            cpt_date_str = cpt.get("date")
            if not cpt_date_str:
                logger.warning(f"CPT {cpt.get('id')} has no date, skipping")
                continue

            try:
                cpt_date = datetime.fromisoformat(cpt_date_str)
            except ValueError:
                logger.error(f"CPT {cpt.get('id')} has invalid date format: {cpt_date_str}")
                continue
            
            time_diff = cpt_date - now
            hours_left = time_diff.total_seconds() / 3600
            
            # Calculate days difference ignoring time of day
            # This ensures notifications are sent based on calendar days, not exact hours
            # Example: If CPT is on 20th at 7 PM, notification is sent on 17th morning (3 days)
            cpt_date_day = cpt_date.date()
            now_day = now.date()
            days_diff = (cpt_date_day - now_day).days

            cpt_id = str(cpt.get("id"))
            
            logger.info(f"CPT {cpt_id} ({position}): date={cpt_date.isoformat()}, "
                        f"hours_left={hours_left:.1f}, days_diff={days_diff}")
            
            # Notification Types
            notification_type = None
            title = ""

            # "Today/Now" Notification (approx 0 to 12 hours before)
            if 0 < hours_left <= 12:
                notification_type = "today"
                title = "CPT Heute!"
                logger.debug(f"CPT {cpt_id}: Triggering 'today' notification (hours_left={hours_left:.1f})")
            
            # "Upcoming" Notification (only when 2-4 days before)
            # Send advance notification only within the 2-4 day window to ensure
            # users receive timely notifications without being spammed too early
            elif days_diff >= 2 and days_diff <= 4:
                notification_type = "3day"
                # Use days_diff for the title calculation
                if days_diff == 1:
                    title = "CPT Morgen!"
                else:
                    title = f"CPT in {days_diff} Tagen!"
                logger.debug(f"CPT {cpt_id}: Triggering '3day' notification (days_diff={days_diff}, hours_left={hours_left:.1f})")

            if notification_type:
                # Key for persistence: "ID_TYPE" e.g. "139_3day"
                key = f"{cpt_id}_{notification_type}"
                
                # Check if already announced
                if key not in self.cpts_announced:
                    logger.info(f"Sending notification for CPT {cpt_id} ({notification_type}): {title}")
                    if await self.send_notification(cpt, title):
                        self.cpts_announced[key] = cpt_date_str
                        notified_count += 1
                        logger.info(f"Successfully sent notification for CPT {cpt_id}")
                    else:
                        logger.error(f"Failed to send notification for CPT {cpt_id}")
                else:
                    logger.debug(f"CPT {cpt_id} already announced as {notification_type}, skipping")
            else:
                logger.debug(f"CPT {cpt_id}: No notification needed (hours_left={hours_left:.1f})")
        
        logger.info(f"Processed {processed_count} CPTs in FIR (filtered out {filtered_count}), sent {notified_count} notifications")

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
                        logger.info(f"Loaded {len(self.cpts_announced)} previously announced CPTs")
                    else:
                        logger.warning("cpts.json format unrecognized. Starting with empty record.")
                        self.cpts_announced = {}
            else:
                logger.info("No existing cpts.json found, starting fresh")
                self.cpts_announced = {}

        except Exception as e:
            logger.error(f"Failed to load announced CPTs: {e}", exc_info=True)
            self.cpts_announced = {}

    def save_announced_cpts(self):
        try:
            import json
            os.makedirs("data", exist_ok=True)
            with open("data/cpts.json", "w") as f:
                json.dump(self.cpts_announced, f, indent=2)
            logger.debug(f"Saved {len(self.cpts_announced)} announced CPTs to disk")
        except Exception as e:
            logger.error(f"Failed to save announced CPTs: {e}", exc_info=True)

    def cleanup_old_cpts(self):
        """Removes CPTs that have already passed from the announced list."""
        try:
            now = datetime.now(timezone.utc)
            keys_to_remove = []
            
            logger.debug(f"Running cleanup of old CPTs (total tracked: {len(self.cpts_announced)})")
            
            for key, date_str in self.cpts_announced.items():
                if date_str is None:
                    # Legacy data without date.
                    # Optional: Remove if we want to enforce cleanup, or keep until manual purge.
                    # Let's keep them to avoid re-announcing if the bot restarts quickly after migration.
                    logger.debug(f"Keeping legacy entry without date: {key}")
                    continue
                
                try:
                    event_date = datetime.fromisoformat(date_str)
                    # If event is in the past (plus a buffer, e.g., 1 day), remove it
                    if event_date + timedelta(days=1) < now:
                        keys_to_remove.append(key)
                        logger.debug(f"Marking {key} for removal (event date: {event_date.isoformat()})")
                except ValueError:
                    # Invalid date format, remove to be safe
                    logger.warning(f"Invalid date format for {key}: {date_str}, removing")
                    keys_to_remove.append(key)
            
            if keys_to_remove:
                logger.info(f"Cleaning up {len(keys_to_remove)} old CPT entries.")
                for k in keys_to_remove:
                    del self.cpts_announced[k]
                self.save_announced_cpts()
            else:
                logger.debug("No old CPT entries to clean up")
                
        except Exception as e:
            logger.error(f"Error during CPT cleanup: {e}", exc_info=True)

    @commands.hybrid_command(name="testcpt", description="Manually triggers the CPT check.")
    async def test_cpt_manual(self, ctx):
        """Manually triggers the CPT check."""
        # Defer response since it might take a while
        await ctx.defer()
        
        logger.info(f"Manual CPT check triggered by user {ctx.author}")
        try:
            cpts = await self.fetch_cpts()
            
            if not cpts:
                msg = "Keine CPTs vom API erhalten. Prüfe die Logs für Details."
                logger.warning(msg)
                await ctx.send(msg)
                return

            # Filter CPTs by FIR
            filtered_cpts = []
            for cpt in cpts:
                position = cpt.get("position", "")
                is_in_fir = any(position.startswith(prefix) for prefix in self.fir_prefixes)
                if is_in_fir:
                    filtered_cpts.append(cpt)
            
            logger.info(f"Found {len(filtered_cpts)} CPTs in FIR out of {len(cpts)} total CPTs")
            
            # Create summary of CPTs
            cpt_summary = []
            for cpt in filtered_cpts[:5]:  # Show first 5
                date_str = cpt.get('date', 'N/A')
                position = cpt.get('position', 'N/A')
                trainee = cpt.get('trainee_name', 'N/A')
                cpt_summary.append(f"- {position} am {date_str}: {trainee}")
            
            count_before = len(self.cpts_announced)
            await self.process_cpts(cpts)
            count_after = len(self.cpts_announced)
            
            if count_after > count_before:
                self.save_announced_cpts()
                msg = f"Fertig. {count_after - count_before} neue Benachrichtigungen gesendet.\n"
                msg += f"CPTs in FIR gefunden: {len(filtered_cpts)}/{len(cpts)}"
                if cpt_summary:
                    msg += f"\n\nBeispiel CPTs:\n" + "\n".join(cpt_summary)
                logger.info(msg)
                await ctx.send(msg)
            else:
                msg = f"Fertig. Keine neuen CPTs gefunden.\n"
                msg += f"CPTs in FIR: {len(filtered_cpts)}/{len(cpts)}"
                if cpt_summary:
                    msg += f"\n\nBeispiel CPTs:\n" + "\n".join(cpt_summary)
                else:
                    msg += f"\nKeine CPTs in der FIR ({', '.join(self.fir_prefixes)}) gefunden."
                logger.info(msg)
                await ctx.send(msg)

        except Exception as e:
            logger.error(f"Error in manual CPT check: {e}", exc_info=True)
            await ctx.send(f"Fehler aufgetreten: {e}")

    async def send_notification(self, cpt, title_prefix):
        channel = self.bot.get_channel(CPT_CHANNEL_ID)
        if not channel:
            logger.error(f"Channel {CPT_CHANNEL_ID} not found.")
            return False

        try:
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
            
            await channel.send(content=message, embed=embed)
            logger.info(f"Sent notification to channel {CPT_CHANNEL_ID}: {title_prefix}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}", exc_info=True)
            return False

    @cpt_check_loop.before_loop
    async def before_cpt_check(self):
        logger.info("Waiting for bot to be ready before starting CPT check loop...")
        await self.bot.wait_until_ready()
        logger.info("Bot is ready. Initializing CPT checker...")
        # Load once here to ensure in-memory state is primed before loop starts
        self.load_announced_cpts()
        logger.info(f"CPT check loop will run every 3 hours")
        logger.info(f"Monitoring FIR prefixes: {', '.join(self.fir_prefixes)}")

async def setup(bot):
    await bot.add_cog(CPTChecker(bot))
