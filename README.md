# GitHub Webhook Event Tracking System

A production-ready Flask + MongoDB application designed to track and display GitHub webhook events (`push`, `pull_request`, `merge`) in a clean, modern UI.

## Features
- **Real-time Event Tracking**: Specialized handling for Push and Pull Request events.
- **Persistent Storage**: MongoDB backend for storing only essential metadata.
- **Modern UI**: Dark mode dashboard with glassmorphism and live polling (15s interval).
- **Error Handling & Logging**: Fully instrumented for production observability.

---

## 🛠 Prerequisites
- **Python 3.9+**
- **MongoDB** (Local or [Atlas](https://www.mongodb.com/cloud/atlas))
- **ngrok** (for local development/testing)

---

## 🚀 Setup & Installation

### 1. Clone & Initialize
```bash
git clone <repository-url>
cd webhook-repo
```

### 2. Configure Environment
Copy `.env.example` to `.env` and provide your MongoDB URI:
```bash
cp .env.example .env
```
Update `MONGO_URI` in `.env`:
```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net/test
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Locally
```bash
python app.py
```
The app will be accessible at [http://localhost:5000](http://localhost:5000).

---

## 🌐 Exposing to Public (ngrok)

To receive webhooks from GitHub, your local development server must be publicly accessible.

1. Install and authenticate ngrok.
2. Run ngrok on port 5000:
   ```bash
   ngrok http 5000
   ```
3. Copy the **Forwarding** URL (e.g., `https://xxxx-xxxx.ngrok-free.app`).

---

## ⚙️ GitHub Webhook Configuration

1. Go to your GitHub Repository > **Settings** > **Webhooks** > **Add webhook**.
2. **Payload URL**: Use your ngrok URL + `/webhook` (e.g., `https://xxxx-xxxx.ngrok-free.app/webhook`).
3. **Content type**: `application/json`.
4. **Events**: Select "Let me select individual events" and check:
   - [x] Pushes
   - [x] Pull requests
5. Click **Add webhook**.

---

## 🧪 Testing with cURL

You can simulate events without a real repository using these payloads:

### Simulate 'Push'
```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{
    "ref": "refs/heads/main",
    "head_commit": {
      "id": "push-12345",
      "author": {"name": "TestUser"},
      "timestamp": "2024-03-02T12:00:00Z"
    }
  }'
```

### Simulate 'Pull Request Opened'
```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d '{
    "action": "opened",
    "pull_request": {
      "id": 101,
      "user": {"login": "DeveloperAlpha"},
      "head": {"ref": "feature-branch"},
      "base": {"ref": "main"},
      "created_at": "2024-03-02T13:30:00Z"
    }
  }'
```

---

## 📂 Project Structure
```
webhook-repo/
├── app.py             # Main Flask application
├── config.py          # Database & logging configuration
├── requirements.txt   # Exact dependency list
├── .env.example       # Environment template
├── README.md          # Documentation
├── templates/
│     └── index.html   # Main dashboard (HTML/CSS)
└── static/
      └── script.js    # UI Logic & Polling
```

---

## 🛡 License
This project is part of a developer assessment and is for demonstration purposes.
