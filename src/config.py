import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TRAINING_API_URL = os.getenv("TRAINING_API_URL")
TRAINING_API_TOKEN = os.getenv("TRAINING_API_TOKEN") # Bearer Token
CPT_CHANNEL_ID = int(os.getenv("CPT_CHANNEL_ID", 0))
EVENT_MANAGER_API_TOKEN = os.getenv("EVENT_MANAGER_API_TOKEN")
EVENT_API_PORT = int(os.getenv("EVENT_API_PORT", 8081))
USE_MOCK_API = os.getenv("USE_MOCK_API", "False").lower() == "true"
FIR_PREFIXES = os.getenv("FIR_PREFIXES", "EDMM,EDDM,EDDN,ETSI,ETSL,ETSN,EDJA,EDMA,EDMO,EDMS,EDMT,EDMV,EDMY,EDDP,EDDC,EDDE").split(",")
CPT_ROLE_ID = int(os.getenv("CPT_ROLE_ID", 0))
