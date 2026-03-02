import os
import sys
import logging
import shutil
from urllib.parse import urlparse
from dotenv import load_dotenv
from pymongo import MongoClient, errors, ASCENDING, DESCENDING

# 1. Initialize Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("webhook-receiver.config")

# 2. Path Configuration (Requirement #7)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")
EXAMPLE_PATH = os.path.join(BASE_DIR, ".env.example")

def print_setup_guide():
    """Print step-by-step instructions for the developer (Requirement #3)."""
    guide = f"""
{'='*60}
🛠️  GITHUB WEBHOOK TRACKER - SETUP GUIDE
{'='*60}

It looks like your environment is not fully configured yet.

1. DATABASE (MONGO_URI):
   - Get your URI from MongoDB Atlas (Database -> Connect -> Drivers).
   - Format: mongodb+srv://<username>:<password>@cluster.mongodb.net/dbname
   - Make sure to replace <password> with your real database user password!

2. SECURITY (WEBHOOK_SECRET):
   - This can be any secure random string.
   - You MUST use this same string when configuring the GitHub Webhook.

3. FILE LOCATION:
   - Your configuration is stored at: {DOTENV_PATH}

ACTION REQUIRED: 
Open '.env' and replace the placeholder values with your real credentials.
{'='*60}
"""
    print(guide)

# 3. Handle Missing .env with Self-Healing (Requirement #1)
if not os.path.exists(DOTENV_PATH):
    if os.path.exists(EXAMPLE_PATH):
        logger.warning(f"⚠️  .env file missing at {DOTENV_PATH}. Creating .env from .env.example template.")
        try:
            shutil.copy(EXAMPLE_PATH, DOTENV_PATH)
            logger.info("✅ Created .env from template. Loading environment variables...")
        except Exception as e:
            logger.critical(f"❌ Failed to copy .env.example to .env: {e}")
            sys.exit(1)
    else:
        logger.critical("❌ FATAL: .env.example not found. Please ensure it exists in the project root.")
        sys.exit(1)

# Load the file
load_dotenv(dotenv_path=DOTENV_PATH)

def mask_mongo_uri(uri):
    """Safely mask the password in the MongoDB URI."""
    if not uri: return "None"
    try:
        parsed = urlparse(uri)
        if parsed.password:
            masked = parsed.netloc.replace(parsed.password, "********")
            return parsed._replace(netloc=masked).geturl()
        return uri
    except: return "Invalid URI Format"

# 4. Validate Environment & Placeholders (Requirement #2)
def validate_environment():
    """Ensure required variables exist and are not placeholders."""
    mongo_uri = os.getenv("MONGO_URI")
    webhook_secret = os.getenv("WEBHOOK_SECRET")

    # Requirement #2: Placeholder detection
    is_placeholder = False
    if mongo_uri and ("localhost" in mongo_uri or "your_mongo_uri" in mongo_uri):
        is_placeholder = True
    if webhook_secret in ["your_secret_here", "CHANGE_ME", "your_secret"]:
        is_placeholder = True

    if not mongo_uri or not webhook_secret or is_placeholder:
        logger.error("❌ Environment Error: Missing or placeholder values detected in .env")
        logger.warning("Please update your .env file with real credentials before running.")
        print_setup_guide()
        sys.exit(0) # Exit safely as requested
    
    logger.info(f"✅ Environment Validated. Host: {mask_mongo_uri(mongo_uri)}")

# Run validation
validate_environment()

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
    DB_NAME = "github_events_db"
    COLLECTION_NAME = "events"

# 5. Hardened MongoDB Initialization
def init_mongodb():
    """Connect to MongoDB with strict diagnostic checks."""
    uri = Config.MONGO_URI
    try:
        client = MongoClient(
            uri, 
            serverSelectionTimeoutMS=5000,
            tlsAllowInvalidCertificates=False
        )
        client.admin.command('ping')
        
        db = client[Config.DB_NAME]
        collection = db[Config.COLLECTION_NAME]

        # Ensure Indexes
        collection.create_index([("request_id", ASCENDING)], unique=True)
        collection.create_index([("timestamp", DESCENDING)])
        
        logger.info("✅ Successfully connected to MongoDB Atlas.")
        return client, db, collection

    except errors.ServerSelectionTimeoutError:
        logger.error("❌ MongoDB Connection Timeout. Check your IP Whitelist/Network.")
    except Exception as e:
        logger.error(f"❌ Database Initialization Failed: {e}")
    return None, None, None

def ping_db(client):
    """Live health check."""
    if client is None: return False
    try:
        client.admin.command('ping')
        return True
    except: return False

# Final connection objects
client, db, events_collection = init_mongodb()
