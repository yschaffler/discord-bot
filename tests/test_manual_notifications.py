import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cogs.cpt_checker import CPTChecker

class TestCPTNotifications(unittest.TestCase):
    def setUp(self):
        with unittest.mock.patch('discord.ext.tasks.Loop.start'):
            self.bot_mock = MagicMock()
            self.checker = CPTChecker(self.bot_mock)
            self.checker.send_notification = AsyncMock(return_value=True)
            self.checker.save_announced_cpts = MagicMock()
        
        if hasattr(self.checker.cpt_check_loop, 'cancel'):
             self.checker.cpt_check_loop.cancel()

    async def test_notification_timings(self):
        now = datetime.now(timezone.utc)
        
        # Test Case 1: CPT in 2 days (48h) -> Should trigger "3day" type (Upcoming)
        cpt_2days = {
            "id": "1",
            "date": (now + timedelta(hours=48)).isoformat(),
            "position": "EDDM_TWR" # Valid prefix
        }
        
        # Test Case 2: CPT in 4 hours -> Should trigger "today" type
        cpt_4hours = {
            "id": "2",
            "date": (now + timedelta(hours=4)).isoformat(),
            "position": "EDDM_TWR"
        }

        # Test Case 3: CPT in 13 hours -> Should NOT trigger notification (outside notification windows)
        cpt_13hours = {
            "id": "3",
            "date": (now + timedelta(hours=13)).isoformat(),
            "position": "EDDM_TWR"
        }

        # Test Case 4: CPT in 3 days -> Should trigger "3day" type (Upcoming)
        cpt_3days = {
            "id": "4",
            "date": (now + timedelta(days=3)).isoformat(),
            "position": "EDDM_TWR"
        }

        # Test Case 5: CPT in 5 days -> Should NOT trigger notification (outside 2-4 day window)
        cpt_5days = {
            "id": "5",
            "date": (now + timedelta(days=5)).isoformat(),
            "position": "EDDM_TWR"
        }

        # Process
        await self.checker.process_cpts([cpt_2days, cpt_4hours, cpt_13hours, cpt_3days, cpt_5days])
        
        # Verify 2 days away
        key_2days = "1_3day"
        self.assertIn(key_2days, self.checker.cpts_announced, "CPT 2 days away should be announced as '3day' type")
        
        # Verify 4 hours away (Today)
        key_4hours = "2_today"
        self.assertIn(key_4hours, self.checker.cpts_announced, "CPT 4 hours away should be announced as 'today' type")

        # Verify 13 hours away (should NOT be announced)
        key_13hours = "3_3day"
        self.assertNotIn(key_13hours, self.checker.cpts_announced, "CPT 13 hours away should NOT be announced (outside notification windows)")
        key_13hours_today = "3_today"
        self.assertNotIn(key_13hours_today, self.checker.cpts_announced, "CPT 13 hours away should NOT be announced as 'today' (>12 hours)")

        # Verify 3 days away
        key_3days = "4_3day"
        self.assertIn(key_3days, self.checker.cpts_announced, "CPT 3 days away should be announced as '3day' type")

        # Verify 5 days away (should NOT be announced)
        key_5days = "5_3day"
        self.assertNotIn(key_5days, self.checker.cpts_announced, "CPT 5 days away should NOT be announced (outside 2-4 day window)")

        print("Notification logic verified.")

if __name__ == '__main__':
    # Run async test
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    t = TestCPTNotifications()
    t.setUp()
    loop.run_until_complete(t.test_notification_timings())
