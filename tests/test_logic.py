import unittest
from datetime import datetime, timedelta, timezone
import json
import asyncio

# Mocking the CPTChecker class structure for testing logic without full bot setup
class MockCPTChecker:
    def __init__(self):
        self.cpts_announced = set()
        self.notifications = []

    async def send_notification(self, cpt, title_prefix):
        self.notifications.append((cpt, title_prefix))
        pass
    
    # Copying the process_cpts logic manually or importing if possible.
    # To avoid dependency issues with discord.py in this simple test script, I will duplicate the logic logic here 
    # OR better, verify the logic by extracting it.
    # For this task, I will replicate the critical filtering/timing logic to verify my assumptions.
    
    async def process_cpts(self, cpts, now_mock):
        # Modified to accept now_mock
        now = now_mock
        
        for cpt in cpts:
            position = cpt.get("position", "")
            if "EDMM" not in position:
                continue

            cpt_date_str = cpt.get("date")
            if not cpt_date_str:
                continue

            try:
                cpt_date = datetime.fromisoformat(cpt_date_str)
            except ValueError:
                print(f"Invalid date format: {cpt_date_str}")
                continue

            time_diff = cpt_date - now
            
            cpt_id = str(cpt.get("id"))
            
            # Notification Types
            notification_type = None
            if 71 <= (time_diff.total_seconds() / 3600) <= 73:
                notification_type = "3day"
            elif 3 <= (time_diff.total_seconds() / 3600) <= 5:
                notification_type = "today"
            
            if notification_type:
                key = f"{cpt_id}_{notification_type}"
                
                if key not in self.cpts_announced:
                    title_prefix = "CPT in 3 Tagen!" if notification_type == "3day" else "CPT Heute!"
                    await self.send_notification(cpt, title_prefix)
                    self.cpts_announced.add(key)

class TestCPTLogic(unittest.IsolatedAsyncioTestCase):
    async def test_filtering(self):
        checker = MockCPTChecker()
        
        # Test Data
        cpts = [
            {
                "id": 1,
                "position": "EDMM_CTR",
                "date": "2026-02-10T19:00:00+00:00" # 3 days from "now"
            },
            {
                "id": 2,
                "position": "EDGG_CTR", # Should be filtered out
                "date": "2026-02-10T19:00:00+00:00"
            },
            {
                "id": 3,
                "position": "EDMM_APP",
                "date": "2026-02-07T23:00:00+00:00" # "Today" (approx 4 hours from 19:00)
            }
        ]
        
        # Set "Now" to 2026-02-07 19:00:00 UTC
        # CPT 1: 2026-02-10 19:00 (Exactly 72 hours later) -> Should trigger 3day
        # CPT 3: 2026-02-07 23:00 (4 hours later) -> Should trigger today
        
        mock_now = datetime(2026, 2, 7, 19, 0, 0, tzinfo=timezone.utc)
        
        await checker.process_cpts(cpts, mock_now)
        
        # Assertions
        self.assertEqual(len(checker.notifications), 2)
        
        # Check CPT 1 (EDMM_CTR)
        self.assertEqual(checker.notifications[0][0]["id"], 1)
        self.assertEqual(checker.notifications[0][1], "CPT in 3 Tagen!")
        
        # Check CPT 3 (EDMM_APP)
        self.assertEqual(checker.notifications[1][0]["id"], 3)
        self.assertEqual(checker.notifications[1][1], "CPT Heute!")
        
        # Check Duplicate Prevention
        await checker.process_cpts(cpts, mock_now)
        self.assertEqual(len(checker.notifications), 2) # Should still be 2

if __name__ == '__main__':
    unittest.main()
