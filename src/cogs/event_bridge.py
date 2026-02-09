from discord.ext import commands
import logging
from aiohttp import web
import discord
from src.config import EVENT_MANAGER_API_TOKEN, EVENT_API_PORT

logger = logging.getLogger("EventBridge")

class EventBridge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.app.router.add_post('/api/notify', self.notify_handler)
        self.runner = None
        self.site = None

    async def notify_handler(self, request):
        # Security check
        auth_header = request.headers.get("Authorization")
        if auth_header != f"Bearer {EVENT_MANAGER_API_TOKEN}":
            return web.json_response({"error": "Unauthorized"}, status=401)

        try:
            data = await request.json()
            channel_id = data.get("channel_id")
            message = data.get("message", "")
            embed_data = data.get("embed")
            role_id = data.get("role_id")

            if not channel_id:
                return web.json_response({"error": "channel_id is required"}, status=400)

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return web.json_response({"error": "Channel not found"}, status=404)

            # Prepend role ping if provided
            if role_id:
                message = f"<@&{role_id}> {message}"

            embed = None
            if embed_data:
                embed = discord.Embed.from_dict(embed_data)

            await channel.send(content=message, embed=embed)
            return web.json_response({"status": "ok", "message": "Notification sent"})

        except Exception as e:
            logger.error(f"Error handling notification: {e}")
            return web.json_response({"error": "Internal Server Error"}, status=500)

    async def start_server(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', EVENT_API_PORT)
        await self.site.start()
        logger.info(f"Event Bridge API started on port {EVENT_API_PORT}")

    async def cog_load(self):
        await self.start_server()

    async def cog_unload(self):
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

async def setup(bot):
    await bot.add_cog(EventBridge(bot))
