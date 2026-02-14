#!/usr/bin/env python3
"""
Demonstration script to show improved logging for training system integration.
This simulates what the bot will log when fetching CPTs.
"""
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging to see output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("CPTChecker")

def demonstrate_logging():
    """Demonstrate the improved logging."""
    print("=" * 80)
    print("DEMONSTRATION: Improved Logging for Training System Integration")
    print("=" * 80)
    print()
    
    print("1. API AUTHENTICATION LOGGING:")
    print("-" * 80)
    # Simulate with token
    token = "test_token_abc123"
    logger.info(f"Using Bearer token authentication (token length: {len(token)})")
    logger.info(f"Fetching CPTs from https://api.vatsim-germany.org/training/api/v1/cpts")
    print()
    
    # Simulate without token
    logger.warning("No TRAINING_API_TOKEN configured - API may reject request")
    print()
    
    print("2. API RESPONSE LOGGING:")
    print("-" * 80)
    # Simulate API response
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
    
    logger.info(f"Raw API response: {sample_response}")
    cpts = sample_response.get("data", [])
    logger.info(f"Fetched {len(cpts)} CPTs from API")
    if cpts:
        logger.info(f"Sample CPT data: {cpts[0]}")
    print()
    
    print("3. CPT FILTERING LOGGING:")
    print("-" * 80)
    fir_prefixes = ["EDMM", "EDDM", "EDDN", "ETSI"]
    
    # CPT in FIR
    logger.info(f"Processing 2 CPTs (current time: 2026-02-14T16:00:00+00:00)")
    logger.info(f"CPT 123 (EDDM_TWR): date=2026-02-17T18:00:00+00:00, hours_left=74.0, days_diff=3")
    
    # CPT outside FIR
    logger.info(f"CPT 124 position 'EDDF_APP' not in FIR (allowed prefixes: {fir_prefixes}), skipping")
    
    logger.info(f"Processed 1 CPTs in FIR (filtered out 1), sent 1 notifications")
    print()
    
    print("4. /testcpt COMMAND LOGGING:")
    print("-" * 80)
    logger.info(f"Manual CPT check triggered by user TestUser#1234")
    logger.info(f"Found 1 CPTs in FIR out of 2 total CPTs")
    
    # This is what the user will see in Discord
    print("\n>>> Discord Response:")
    print("Fertig. 1 neue Benachrichtigungen gesendet.")
    print("CPTs in FIR gefunden: 1/2")
    print("\nBeispiel CPTs:")
    print("- EDDM_TWR am 2026-02-17T18:00:00Z: Max Mustermann")
    print()
    
    print("5. ERROR LOGGING (when API fails):")
    print("-" * 80)
    logger.error(f"Failed to fetch CPTs: HTTP 401")
    logger.error(f"Response body: {{\"error\": \"Unauthorized\", \"message\": \"Invalid Bearer token\"}}")
    print()
    
    print("=" * 80)
    print("END OF DEMONSTRATION")
    print("=" * 80)
    print()
    print("KEY IMPROVEMENTS:")
    print("✓ API authentication status is now logged")
    print("✓ Raw API responses are logged for debugging")
    print("✓ CPT filtering decisions are logged with reasons")
    print("✓ /testcpt command shows actual CPT data")
    print("✓ Error responses include full body for troubleshooting")
    print()

if __name__ == "__main__":
    demonstrate_logging()
