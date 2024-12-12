import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Define variables
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")
GROUP_NAMES = [group.strip() for group in os.getenv("TELEGRAM_GROUPS", "").split(",")]
rpc_url = os.getenv("rpc_url", "")
public_key = os.getenv("public_key", "")
private_key = os.getenv("private_key", "")
ONEINCH_API_KEY = os.getenv("ONEINCH_API_KEY", "")

# Validate required variables
if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, GROUP_NAMES, rpc_url, public_key, private_key, ONEINCH_API_KEY]):
    raise ValueError("Missing one or more required environment variables.")
