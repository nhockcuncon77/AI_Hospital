"""Load config from environment."""
import os
from dotenv import load_dotenv

load_dotenv()

# Twilio
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
TWILIO_WEBHOOK_BASE_URL = os.environ.get("TWILIO_WEBHOOK_BASE_URL", "").rstrip("/")

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE") or None

# Test line
TEST_LINE_NUMBER = os.environ.get("TEST_LINE_NUMBER", "+18054398008")

# Patient identity (for bot persona)
PATIENT_NAME = "Minh Huynh"
PATIENT_DOB = "July 14th, 2001"

# Audio: Twilio uses 8kHz mulaw
SAMPLE_RATE_TWILIO = 8000
# OpenAI TTS default
SAMPLE_RATE_TTS = 24000

# Paths
TRANSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "transcripts")
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)
