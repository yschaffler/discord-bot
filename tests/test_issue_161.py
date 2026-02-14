"""
Test for the specific issue reported: CPT #161 not being notified.

The issue: On Feb 14 at 17:00, no notification was sent for CPT scheduled on Feb 16 at 20:00.
This is ~2 days and 3 hours before the CPT.

With the fix, notifications should be sent when CPTs are 2-4 days away.
"""
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cogs.cpt_checker import CPTChecker

class TestIssue161(unittest.TestCase):
    def setUp(self):
        with unittest.mock.patch('discord.ext.tasks.Loop.start'):
            self.bot_mock = MagicMock()
            self.checker = CPTChecker(self.bot_mock)
            self.checker.send_notification = AsyncMock(return_value=True)
            self.checker.save_announced_cpts = MagicMock()
        
        if hasattr(self.checker.cpt_check_loop, 'cancel'):
            self.checker.cpt_check_loop.cancel()

    async def test_cpt_161_notification(self):
        """Test that CPT #161 would be notified on Feb 14 17:00"""
        
        # Simulate current time: Feb 14, 2026 17:00 UTC
        # CPT time: Feb 16, 2026 20:00 UTC
        # This is ~2 days and 3 hours away, should trigger notification
        
        cpt_161 = {
            "id": 161,
            "trainee_vatsim_id": 1667030,
            "trainee_name": "Holger",
            "examiner_vatsim_id": None,
            "examiner_name": None,
            "local_vatsim_id": 1470223,
            "local_name": "Masa",
            "course_name": "Leipzig Approach",
            "position": "EDDP_APP",
            "date": "2026-02-16T20:00:00+00:00",
            "confirmed": False
        }
        
        # Process the CPT
        await self.checker.process_cpts([cpt_161])
        
        # Verify notification was triggered
        key = "161_3day"
        self.assertIn(key, self.checker.cpts_announced, 
                     "CPT 161 should be notified when checked on Feb 14 17:00 (2+ days before)")
        
        # Verify the notification was sent
        self.checker.send_notification.assert_called_once()
        
        # Check the title contains the right information
        call_args = self.checker.send_notification.call_args[0]
        title = call_args[1]
        self.assertIn("CPT in 2 Tagen", title, "Title should indicate 2 days")
        
        print("✓ CPT #161 notification test passed")

    async def test_cpt_outside_window(self):
        """Test that CPT 5+ days away is NOT notified"""
        
        # CPT 5 days away should NOT trigger notification (outside 2-4 day window)
        now = datetime.now(timezone.utc)
        cpt_5days = {
            "id": 999,
            "trainee_name": "Test User",
            "local_name": "Test Mentor",
            "course_name": "Test Course",
            "position": "EDDP_APP",
            "date": (now.replace(hour=20, minute=0, second=0, microsecond=0) + 
                    __import__('datetime').timedelta(days=5)).isoformat(),
            "confirmed": False
        }
        
        await self.checker.process_cpts([cpt_5days])
        
        # Should NOT be in announced list
        key = "999_3day"
        self.assertNotIn(key, self.checker.cpts_announced,
                        "CPT 5 days away should NOT be notified (outside 2-4 day window)")
        
        print("✓ CPT outside notification window test passed")

if __name__ == '__main__':
    import asyncio
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    t = TestIssue161()
    t.setUp()
    loop.run_until_complete(t.test_cpt_161_notification())
    
    t.setUp()  # Reset
    loop.run_until_complete(t.test_cpt_outside_window())
    
    print("\n✓ All Issue #161 tests passed!")
