import logging
import os
import sys
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import bot module to trigger logging config
import src.bot

# Get logger
logger = logging.getLogger("DiscordBot")

# Log a test message
test_msg = f"Verification Test Message {time.time()}"
logger.info(test_msg)

# Check if log file exists and contains message
log_file = "data/logs/bot.log"
if os.path.exists(log_file):
    print(f"Log file {log_file} exists.")
    with open(log_file, "r") as f:
        content = f.read()
        if test_msg in content:
            print("SUCCESS: Log message found in file.")
        else:
            print("FAILURE: Log message NOT found in file.")
else:
    print(f"FAILURE: Log file {log_file} NOT found.")
