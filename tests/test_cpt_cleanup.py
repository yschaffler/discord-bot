import unittest
from datetime import datetime, timedelta, timezone
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cogs.cpt_checker import CPTChecker

class TestCPTCleanup(unittest.TestCase):
    def setUp(self):
        # Patch Loop.start to prevent it from trying to get a running loop
        with unittest.mock.patch('discord.ext.tasks.Loop.start'):
            self.bot_mock = MagicMock()
            self.checker = CPTChecker(self.bot_mock)
        # Prevent loop start (redundant if patched, but safety)
        if hasattr(self.checker.cpt_check_loop, 'cancel'):
             self.checker.cpt_check_loop.cancel()

    def test_cleanup_old_cpts(self):
        now = datetime.now(timezone.utc)
        past_date = now - timedelta(days=2)
        future_date = now + timedelta(days=2)
        
        # Setup data
        self.checker.cpts_announced = {
            "past_event": past_date.isoformat(),
            "future_event": future_date.isoformat(),
            "legacy_item": None 
        }
        
        # Run cleanup
        self.checker.cleanup_old_cpts()
        
        # Verify
        self.assertNotIn("past_event", self.checker.cpts_announced, "Past event should be removed")
        self.assertIn("future_event", self.checker.cpts_announced, "Future event should be kept")
        self.assertIn("legacy_item", self.checker.cpts_announced, "Legacy item (None) should be kept (or removed based on logic, currently kept)")

        print("Cleanup logic verified successfully.")

if __name__ == '__main__':
    unittest.main()
