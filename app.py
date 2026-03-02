import hmac
import hashlib
import json
import sys
from datetime import datetime
from flask import Flask, request, jsonify, render_template, abort
from bson import json_util
import pymongo

# Import config early to ensure environment validation and MongoDB init
from config import logger, events_collection, client, Config, ping_db

app = Flask(__name__)

# --- Helper Functions ---

def verify_signature(payload_body, secret, signature_header):
    """Verify that the webhook payload was sent from GitHub."""
    if not secret:
        logger.warning("WEBHOOK_SECRET not configured. Skipping verification.")
        return True
    
    if not signature_header:
        logger.error("X-Hub-Signature-256 header missing.")
        return False

    hash_object = hmac.new(secret.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        logger.error("Signature verification failed.")
        return False
    
    return True

def format_timestamp(iso_str):
    """Converts ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        day = dt.day
        suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        return dt.strftime(f"{day}{suffix} %B %Y - %I:%M %p UTC")
    except Exception as e:
        logger.error(f"Timestamp formatting error: {e}")
        return iso_str

def get_branch_name(ref):
    """Extract branch from ref."""
    if not ref:
        return "unknown"
    return ref.split('/')[-1]

# --- Routes ---

@app.route('/', methods=['GET'])
def index():
    """Render the Dashboard UI."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """
    Enhanced Health Check Endpoint.
    Requirement #3: Live ping check.
    """
    is_connected = ping_db(client)
    
    status_code = 200 if is_connected else 503
    return jsonify({
        "status": "ok" if is_connected else "degraded",
        "mongodb": "connected" if is_connected else "disconnected",
        "details": "Ready to receive events" if is_connected else "Check MONGO_URI, IP Whitelist, and dnspython",
        "timestamp": datetime.utcnow().isoformat()
    }), status_code

@app.route('/events', methods=['GET'])
def get_events():
    """
    Fetch events safely even if DB is offline.
    Requirement #8: Detailed Error Visibility.
    """
    try:
        # Check connection before query
        if not ping_db(client) or events_collection is None:
            return jsonify({
                "error": "database_offline", 
                "message": "MongoDB is currently disconnected. Check server logs.",
                "events": []
            }), 200 # Return 200 with empty list to prevent UI crash

        events = list(events_collection.find().sort("timestamp", -1).limit(20))
        return json.loads(json_util.dumps(events)), 200
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return jsonify({"error": "Failed to retrieve events", "events": []}), 200

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Process incoming webhooks with DB connectivity checks."""
    event_type = request.headers.get('X-GitHub-Event')
    signature = request.headers.get('X-Hub-Signature-256')
    
    # 1. Verify Signature
    if not verify_signature(request.data, Config.WEBHOOK_SECRET, signature):
        abort(403, description="Invalid signature")

    payload = request.json
    if not payload:
        logger.error("Payload missing in request.")
        return jsonify({"error": "Payload required"}), 400

    logger.info(f"Received GitHub Event: {event_type}")
    
    event_data = None

    try:
        if event_type == 'push':
            head_commit = payload.get('head_commit')
            if head_commit:
                event_data = {
                    "request_id": head_commit.get('id'),
                    "author": head_commit.get('author', {}).get('name'),
                    "action": "PUSH",
                    "from_branch": "N/A",
                    "to_branch": get_branch_name(payload.get('ref')),
                    "timestamp": format_timestamp(head_commit.get('timestamp'))
                }
        elif event_type == 'pull_request':
            action = payload.get('action')
            pr = payload.get('pull_request', {})
            
            internal_action = None
            if action == 'opened':
                internal_action = "PULL_REQUEST"
            elif action == 'closed' and pr.get('merged') is True:
                internal_action = "MERGE"
            
            if internal_action:
                event_data = {
                    "request_id": str(pr.get('id')),
                    "author": pr.get('user', {}).get('login'),
                    "action": internal_action,
                    "from_branch": pr.get('head', {}).get('ref'),
                    "to_branch": pr.get('base', {}).get('ref'),
                    "timestamp": format_timestamp(pr.get('created_at'))
                }

        # 2. Store to Database
        if event_data:
            if not ping_db(client) or events_collection is None:
                logger.error("Webhook dropped! Database is disconnected.")
                return jsonify({"error": "database_offline"}), 503

            try:
                events_collection.insert_one(event_data)
                logger.info(f"Stored {event_data['action']} event ({event_data['request_id']}) successfully.")
                return jsonify({"message": "Success"}), 201
            except pymongo.errors.DuplicateKeyError:
                logger.info(f"Duplicate event ignored: {event_data['request_id']}")
                return jsonify({"message": "Duplicate ignored"}), 200
        
        return jsonify({"message": "Event ignored"}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal processor error"}), 500

if __name__ == '__main__':
    # Final Startup Logic (Requirement #6)
    if not ping_db(client):
        logger.error("❌ App starting in DEGRADED mode - MongoDB disconnected.")
    else:
        logger.info("🚀 App starting with live MongoDB connection.")
        
    app.run(host='0.0.0.0', port=5000)
