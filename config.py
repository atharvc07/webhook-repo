import os
from dotenv import load_dotenv
from pymongo import MongoClient
import logging

# Load environment variables
load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/github_webhooks")
    DB_NAME = "github_events_db"
    COLLECTION_NAME = "events"

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB Setup
def get_db():
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client[Config.DB_NAME]
        # Test connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB.")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

db = get_db()
events_collection = db[Config.COLLECTION_NAME] if db is not None else None
