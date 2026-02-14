#!/usr/bin/env python3
"""
Test script to demonstrate comprehensive logging from all bot components.
This shows what will be written to data/logs/bot.log when the bot runs.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import to trigger logging configuration
import src.bot
import logging

# Get loggers (these will all write to data/logs/bot.log now)
bot_logger = logging.getLogger('DiscordBot')
cpt_logger = logging.getLogger('CPTChecker')
event_logger = logging.getLogger('EventBridge')

def simulate_bot_startup():
    """Simulate bot startup sequence."""
    print("\n" + "=" * 80)
    print("SIMULATING BOT STARTUP")
    print("=" * 80 + "\n")
    
    bot_logger.info("Starting bot setup...")
    bot_logger.info("Loading cogs...")
    bot_logger.info("✓ Loaded cpt_checker")
    bot_logger.info("✓ Loaded event_bridge")
    bot_logger.info("Syncing commands with Discord...")
    bot_logger.info("✓ Synced 1 command(s)")
    bot_logger.info("Bot setup complete. All cogs loaded.")
    bot_logger.info("=" * 80)
    bot_logger.info("Bot is ready! Logged in as TestBot#1234 (ID: 123456789)")
    bot_logger.info("Connected to 1 guild(s)")
    bot_logger.info("=" * 80)

def simulate_cpt_checker_init():
    """Simulate CPT checker initialization."""
    print("\n" + "=" * 80)
    print("SIMULATING CPT CHECKER INITIALIZATION")
    print("=" * 80 + "\n")
    
    cpt_logger.info("Waiting for bot to be ready before starting CPT check loop...")
    cpt_logger.info("Bot is ready. Initializing CPT checker...")
    cpt_logger.info("Loaded 5 previously announced CPTs")
    cpt_logger.info("CPT check loop will run every 3 hours")
    cpt_logger.info("Monitoring FIR prefixes: EDMM, EDDM, EDDN, ETSI, ETSL, ETSN")

def simulate_cpt_check():
    """Simulate a CPT check cycle."""
    print("\n" + "=" * 80)
    print("SIMULATING CPT CHECK CYCLE")
    print("=" * 80 + "\n")
    
    cpt_logger.info("=" * 80)
    cpt_logger.info("Starting scheduled CPT check (runs every 3 hours)")
    cpt_logger.info("=" * 80)
    
    # Cleanup
    cpt_logger.debug("Running cleanup of old CPTs (total tracked: 5)")
    cpt_logger.info("Cleaning up 2 old CPT entries.")
    
    # Fetch CPTs
    cpt_logger.info("Using Bearer token authentication (token length: 42)")
    cpt_logger.info("Fetching CPTs from https://api.vatsim-germany.org/training/api/v1/cpts")
    
    # Simulate successful response
    sample_response = {
        "data": [
            {
                "id": 123,
                "position": "EDDM_TWR",
                "date": "2026-02-17T18:00:00Z",
                "trainee_name": "Max Mustermann",
                "trainee_vatsim_id": "1234567",
                "course_name": "Tower Controller",
                "local_name": "John Mentor"
            },
            {
                "id": 124,
                "position": "EDDF_APP",
                "date": "2026-02-18T19:00:00Z",
                "trainee_name": "Lisa Beispiel",
                "trainee_vatsim_id": "7654321",
                "course_name": "Approach Controller",
                "local_name": "Jane Instructor"
            }
        ]
    }
    
    cpt_logger.info(f"Raw API response: {sample_response}")
    cpt_logger.info("Fetched 2 CPTs from API")
    cpt_logger.info(f"Sample CPT data: {sample_response['data'][0]}")
    
    # Process CPTs
    cpt_logger.info("Processing 2 CPTs (current time: 2026-02-14T16:41:00+00:00)")
    
    # CPT 1 - in FIR
    cpt_logger.info("CPT 123 (EDDM_TWR): date=2026-02-17T18:00:00+00:00, hours_left=74.0, days_diff=3")
    cpt_logger.info("Sending notification for CPT 123 (3day): CPT in 3 Tagen!")
    cpt_logger.info("Sent notification to channel 1234567890: CPT in 3 Tagen!")
    cpt_logger.info("Successfully sent notification for CPT 123")
    
    # CPT 2 - outside FIR
    cpt_logger.info("CPT 124 position 'EDDF_APP' not in FIR (allowed prefixes: ['EDMM', 'EDDM', 'EDDN', 'ETSI', 'ETSL', 'ETSN']), skipping")
    
    # Summary
    cpt_logger.info("Processed 1 CPT in FIR (filtered out 1), sent 1 notification")
    
    # Save state
    cpt_logger.debug("Saved 6 announced CPTs to disk")
    
    cpt_logger.info("CPT check complete")
    cpt_logger.info("=" * 80)

def simulate_manual_testcpt():
    """Simulate /testcpt command."""
    print("\n" + "=" * 80)
    print("SIMULATING /testcpt COMMAND")
    print("=" * 80 + "\n")
    
    cpt_logger.info("Manual CPT check triggered by user TestUser#1234")
    cpt_logger.info("Using Bearer token authentication (token length: 42)")
    cpt_logger.info("Fetching CPTs from https://api.vatsim-germany.org/training/api/v1/cpts")
    cpt_logger.info("Fetched 2 CPTs from API")
    cpt_logger.info("Found 1 CPT in FIR out of 2 total CPTs")
    cpt_logger.info("Fertig. Keine neuen CPTs gefunden.\nCPTs in FIR: 1/2\n\nBeispiel CPTs:\n- EDDM_TWR am 2026-02-17T18:00:00Z: Max Mustermann")

def simulate_api_error():
    """Simulate API error."""
    print("\n" + "=" * 80)
    print("SIMULATING API ERROR")
    print("=" * 80 + "\n")
    
    cpt_logger.info("Using Bearer token authentication (token length: 42)")
    cpt_logger.info("Fetching CPTs from https://api.vatsim-germany.org/training/api/v1/cpts")
    cpt_logger.error("Failed to fetch CPTs: HTTP 401")
    cpt_logger.error("Response body: {\"error\": \"Unauthorized\", \"message\": \"Invalid or expired token\"}")

def simulate_event_bridge():
    """Simulate event bridge activity."""
    print("\n" + "=" * 80)
    print("SIMULATING EVENT BRIDGE")
    print("=" * 80 + "\n")
    
    event_logger.info("Starting event notification API server on port 8080")
    event_logger.info("Event API is ready and listening")
    event_logger.info("Received event notification from 192.168.1.100")
    event_logger.info("Successfully sent event notification to Discord")

def verify_log_file():
    """Verify all logs are in the log file."""
    print("\n" + "=" * 80)
    print("VERIFYING LOG FILE")
    print("=" * 80 + "\n")
    
    log_file = "data/logs/bot.log"
    
    if not os.path.exists(log_file):
        print(f"❌ ERROR: Log file {log_file} does not exist!")
        return False
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    checks = [
        ("DiscordBot startup", "Bot is ready!"),
        ("CPTChecker init", "CPT check loop will run"),
        ("CPTChecker API fetch", "Fetching CPTs from"),
        ("CPTChecker processing", "Processing"),
        ("CPTChecker notifications", "Sent notification"),
        ("EventBridge activity", "Event API is ready"),
        ("API errors", "Failed to fetch CPTs"),
    ]
    
    all_passed = True
    for name, keyword in checks:
        if keyword in content:
            print(f"✅ {name}: Found in log file")
        else:
            print(f"❌ {name}: NOT found in log file")
            all_passed = False
    
    print(f"\nLog file size: {len(content)} bytes")
    print(f"Log file location: {os.path.abspath(log_file)}")
    
    return all_passed

if __name__ == "__main__":
    # Run all simulations
    simulate_bot_startup()
    simulate_cpt_checker_init()
    simulate_cpt_check()
    simulate_manual_testcpt()
    simulate_api_error()
    simulate_event_bridge()
    
    # Verify everything was logged
    if verify_log_file():
        print("\n✅ SUCCESS: All logs are being written to data/logs/bot.log")
        print("\nYou can now monitor the bot by running:")
        print("  tail -f data/logs/bot.log")
    else:
        print("\n❌ FAILURE: Some logs are missing from the log file")
        sys.exit(1)
