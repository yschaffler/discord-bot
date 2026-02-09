import unittest
from unittest.mock import MagicMock, AsyncMock
from aiohttp import web
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cogs.event_bridge import EventBridge
from src.config import EVENT_MANAGER_API_TOKEN

class TestEventBridgeRolePing(unittest.TestCase):
    def setUp(self):
        self.bot_mock = MagicMock()
        self.cog = EventBridge(self.bot_mock)
        
        # Mock channel
        self.channel_mock = AsyncMock()
        self.bot_mock.get_channel.return_value = self.channel_mock

    async def test_notify_handler_with_role(self):
        # Create request
        payload = {
            "channel_id": 123,
            "message": "Test Message",
            "role_id": 999
        }
        
        request = MagicMock()
        request.json = AsyncMock(return_value=payload)
        request.headers = {"Authorization": f"Bearer {EVENT_MANAGER_API_TOKEN}"}
        
        # Execute handler
        response = await self.cog.notify_handler(request)
        
        # Verify response
        self.assertEqual(response.status, 200)
        
        # Verify channel.send called with correct content
        self.channel_mock.send.assert_called_once()
        call_args = self.channel_mock.send.call_args
        
        # Check both positional and keyword args
        content = call_args.kwargs.get('content')
        if content is None and call_args.args:
            content = call_args.args[0]
            
        print(f"DEBUG: Call args: {call_args}")
        self.assertEqual(content, "<@&999> Test Message")
        print("Role ping verification passed.")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    t = TestEventBridgeRolePing()
    t.setUp()
    loop.run_until_complete(t.test_notify_handler_with_role())
