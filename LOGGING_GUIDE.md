# Discord Bot Logging Guide

## Logging Location

All bot logs are written to: **`data/logs/bot.log`**

The log file:
- Rotates automatically when it reaches 5 MB
- Keeps 5 backup files (bot.log.1, bot.log.2, etc.)
- Is created automatically when the bot starts

## What Gets Logged

### Bot Startup
```
2026-02-14 16:42:04,936 - DiscordBot - INFO - ================================================================================
2026-02-14 16:42:04,936 - DiscordBot - INFO - Logging system initialized
2026-02-14 16:42:04,936 - DiscordBot - INFO - Log file: data/logs/bot.log
2026-02-14 16:42:04,936 - DiscordBot - INFO - Log level: INFO
2026-02-14 16:42:04,936 - DiscordBot - INFO - ================================================================================
2026-02-14 16:42:04,937 - DiscordBot - INFO - Starting bot setup...
2026-02-14 16:42:04,937 - DiscordBot - INFO - ✓ Loaded cpt_checker
2026-02-14 16:42:04,937 - DiscordBot - INFO - ✓ Loaded event_bridge
2026-02-14 16:42:04,937 - DiscordBot - INFO - Bot is ready! Logged in as YourBot#1234
```

### CPT Checker Activity

#### Initialization
```
2026-02-14 16:42:04,937 - CPTChecker - INFO - Waiting for bot to be ready before starting CPT check loop...
2026-02-14 16:42:04,937 - CPTChecker - INFO - Bot is ready. Initializing CPT checker...
2026-02-14 16:42:04,937 - CPTChecker - INFO - CPT check loop will run every 3 hours
2026-02-14 16:42:04,938 - CPTChecker - INFO - Monitoring FIR prefixes: EDMM, EDDM, EDDN, ETSI, ETSL, ETSN
```

#### Scheduled Checks (Every 3 Hours)
```
2026-02-14 16:42:04,938 - CPTChecker - INFO - ================================================================================
2026-02-14 16:42:04,938 - CPTChecker - INFO - Starting scheduled CPT check (runs every 3 hours)
2026-02-14 16:42:04,938 - CPTChecker - INFO - ================================================================================
```

#### API Interaction
```
2026-02-14 16:42:04,938 - CPTChecker - INFO - Using Bearer token authentication (token length: 42)
2026-02-14 16:42:04,938 - CPTChecker - INFO - Fetching CPTs from https://api.vatsim-germany.org/training/api/v1/cpts
2026-02-14 16:42:04,938 - CPTChecker - INFO - Fetched 2 CPTs from API
2026-02-14 16:42:04,938 - CPTChecker - INFO - Sample CPT data: {'id': 123, 'position': 'EDDM_TWR', ...}
```

#### CPT Processing
```
2026-02-14 16:42:04,938 - CPTChecker - INFO - Processing 2 CPTs (current time: 2026-02-14T16:41:00+00:00)
2026-02-14 16:42:04,938 - CPTChecker - INFO - CPT 123 (EDDM_TWR): date=2026-02-17T18:00:00+00:00, hours_left=74.0, days_diff=3
2026-02-14 16:42:04,939 - CPTChecker - INFO - Sent notification to channel 1234567890: CPT in 3 Tagen!
```

#### Filtering
```
2026-02-14 16:42:04,939 - CPTChecker - INFO - CPT 124 position 'EDDF_APP' not in FIR (allowed prefixes: ['EDMM', 'EDDM', ...]), skipping
2026-02-14 16:42:04,939 - CPTChecker - INFO - Processed 1 CPT in FIR (filtered out 1), sent 1 notification
```

### Error Scenarios

#### API Errors
```
2026-02-14 16:42:04,940 - CPTChecker - ERROR - Failed to fetch CPTs: HTTP 401
2026-02-14 16:42:04,940 - CPTChecker - ERROR - Response body: {"error": "Unauthorized", "message": "Invalid or expired token"}
```

#### Missing Configuration
```
2026-02-14 16:42:04,938 - CPTChecker - WARNING - No TRAINING_API_TOKEN configured - API may reject request
```

## How to Monitor Logs

### View Last 50 Lines
```bash
tail -50 data/logs/bot.log
```

### Follow Logs in Real-Time
```bash
tail -f data/logs/bot.log
```

### Search for Errors
```bash
grep ERROR data/logs/bot.log
grep -i error data/logs/bot.log  # case-insensitive
```

### Search for Specific CPT ID
```bash
grep "CPT 123" data/logs/bot.log
```

### View Logs from Today
```bash
grep "2026-02-14" data/logs/bot.log
```

### Check API Communication
```bash
grep "Fetching CPTs" data/logs/bot.log
grep "Fetched .* CPTs from API" data/logs/bot.log
```

### See Notifications Sent
```bash
grep "Sent notification" data/logs/bot.log
```

## Log Levels

The bot uses these log levels:

- **INFO**: Normal operations (most common)
  - Bot startup
  - Scheduled checks
  - API calls
  - CPT processing
  - Notifications sent

- **WARNING**: Unusual but not critical
  - Missing API token
  - No CPTs found

- **ERROR**: Problems that prevent normal operation
  - API failures
  - Network errors
  - Discord communication failures

## Troubleshooting with Logs

### Bot Not Starting
Check for:
```bash
grep "ERROR" data/logs/bot.log
grep "Failed" data/logs/bot.log
```

### No CPTs Being Announced
Check:
1. Are CPTs being fetched?
   ```bash
   grep "Fetched .* CPTs from API" data/logs/bot.log
   ```

2. Are they being filtered out?
   ```bash
   grep "not in FIR" data/logs/bot.log
   ```

3. Are they already announced?
   ```bash
   grep "already announced" data/logs/bot.log
   ```

4. Wrong timing?
   ```bash
   grep "hours_left=" data/logs/bot.log
   ```

### API Connection Issues
Check:
```bash
grep "Failed to fetch CPTs" data/logs/bot.log
grep "HTTP" data/logs/bot.log
```

### Testing with /testcpt
When you run `/testcpt` in Discord, check the logs:
```bash
grep "Manual CPT check triggered" data/logs/bot.log
tail -20 data/logs/bot.log
```

## Log File Management

The logs rotate automatically, but you can manually clean old logs:

```bash
# Remove all backup logs (keeps current bot.log)
rm data/logs/bot.log.*

# Archive logs before cleaning
tar -czf logs-backup-$(date +%Y%m%d).tar.gz data/logs/
rm data/logs/bot.log.*
```

## Performance

The logging system:
- ✅ Writes to file asynchronously (non-blocking)
- ✅ Automatically rotates files to prevent disk space issues
- ✅ Logs at INFO level by default (not too verbose, not too quiet)
- ✅ Captures all components (DiscordBot, CPTChecker, EventBridge)
- ✅ Thread-safe for concurrent logging

## Summary

**To see what the bot is doing right now:**
```bash
tail -f data/logs/bot.log
```

**To see if something went wrong:**
```bash
grep -E "ERROR|WARNING" data/logs/bot.log | tail -20
```

**To verify API is working:**
```bash
grep "Fetched .* CPTs from API" data/logs/bot.log | tail -5
```

All the information you need to debug the bot is now in the log file! 🎉
