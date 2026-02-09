try:
    import discord
    from discord.ext import commands
    import aiohttp
    import dotenv
    print("SUCCESS: All modules found.")
except ImportError as e:
    print(f"ERROR: {e}")
