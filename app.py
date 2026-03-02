from flask import Flask, request, jsonify, render_template
from config import logger, events_collection
import datetime
from bson import json_util
import json

app = Flask(__name__)

# Helper to extract branch from ref (e.g., "refs/heads/main" -> "main")
def get_branch_name(ref):
    if not ref:
        return "unknown"
    return ref.split('/')[-1]

@app.route('/', methods=['GET'])
def index():
    """Render the main UI."""
    return render_template('index.html')

@app.route('/events', methods=['GET'])
def get_events():
    """Fetch the latest 20 events from MongoDB."""
    try:
        if events_collection is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Get latest 20 sorted by timestamp descending
        events = list(events_collection.find().sort("timestamp", -1).limit(20))
        
        # Convert BSON to JSON serializable objects
        return json.loads(json_util.dumps(events)), 200
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Receive and process GitHub webhook payloads."""
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.json
    
    if not payload:
        return jsonify({"message": "No payload received"}), 400

    logger.info(f"Received GitHub event: {event_type}")
    
    event_data = None
    
    try:
        if event_type == 'push':
            # Extract push details
            head_commit = payload.get('head_commit', {})
            if head_commit:
                event_data = {
                    "request_id": head_commit.get('id'),
                    "author": head_commit.get('author', {}).get('name'),
                    "action": "PUSH",
                    "from_branch": "N/A", # Push doesn't typically have a 'from' branch in this context
                    "to_branch": get_branch_name(payload.get('ref')),
                    "timestamp": head_commit.get('timestamp') # Already ISO format usually
                }
                
        elif event_type == 'pull_request':
            # Extract PR details
            action = payload.get('action')
            pull_request = payload.get('pull_request', {})
            
            # Determine internal action type
            internal_action = None
            if action == 'opened':
                internal_action = "PULL_REQUEST"
            elif action == 'closed' and pull_request.get('merged') == True:
                internal_action = "MERGE"
            
            if internal_action:
                event_data = {
                    "request_id": str(pull_request.get('id')),
                    "author": pull_request.get('user', {}).get('login'),
                    "action": internal_action,
                    "from_branch": pull_request.get('head', {}).get('ref'),
                    "to_branch": pull_request.get('base', {}).get('ref'),
                    "timestamp": pull_request.get('created_at') # Already ISO format usually
                }
        
        # Save to database if it's an event we track
        if event_data:
            if events_collection is not None:
                events_collection.insert_one(event_data)
                logger.info(f"Successfully stored {event_data['action']} event: {event_data['request_id']}")
                return jsonify({"message": "Webhook received and stored"}), 201
            else:
                logger.error("Database collection not initialized.")
                return jsonify({"error": "Database connection error"}), 500
        
        return jsonify({"message": f"Event type '{event_type}' was not tracked or action ignored"}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Running on 0.0.0.0 for easier ngrok tunneling
    app.run(host='0.0.0.0', port=5000, debug=True)
