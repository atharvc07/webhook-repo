# GitHub Webhook Tracker (Hardened Edition)

A production-ready Flask + MongoDB application designed to track and display GitHub webhook events with strict security and high robustness.

## 🚀 Features & Enhancements

- **Security**: Validates payload integrity using `X-Hub-Signature-256` (HMAC SHA256).
- **Hardened Event Logic**: Specifically tracks `push`, `pull_request` (opened), and `merge` events while filtering out noise.
- **Robust Storage**: Optimized MongoDB indices for fast delivery and duplication prevention (unique `request_id`).
- **UTC Consistency**: Automated timestamp formatting to a human-readable UTC string.
- **Health Monitoring**: Integrated `/health` endpoint for monitoring database status.
- **Improved UI**: Live dashboard with polling, loading indicators, and "Last Updated" status.

---

## 🛠 Prerequisites

- Python 3.9+
- MongoDB (Local or Atlas)
- **ngrok** (Required for receiving real webhooks during local development)

---

## ⚙️ Environment Setup

> [!IMPORTANT]
> The application will **fail fast** and exit if a properly configured `.env` file is not found in the project root.

1.  **Create `.env`**: Copy the provided template to create your local environment file.
    ```bash
    cp .env.example .env
    ```
2.  **Required Variables**: Open `.env` and provide your specific values:
    - `MONGO_URI`: Your MongoDB connection string (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/dbname`).
    - `WEBHOOK_SECRET`: A secure token you'll also enter in GitHub Webhook settings.
3.  **Location Check**: Ensure the `.env` file is in the same directory as `app.py`.

---

## 🚀 Installation & Exposure

### 1. External Exposure (ngrok)
GitHub needs a public URL to send webhooks.
1. Run ngrok on port 5000:
   ```bash
   ngrok http 5000
   ```
2. Copy the **Forwarding** URL (e.g., `https://abcd-123.ngrok-free.app`).
3. **Debug Tip**: Inspect real-time webhook requests by visiting [http://localhost:4040](http://localhost:4040) while ngrok is running.

---

## 🔧 GitHub Webhook Configuration

1. In your repo: **Settings** > **Webhooks** > **Add webhook**.
2. **Payload URL**: `https://your-ngrok-url.app/webhook` (e.g., `https://abcd-123.ngrok-free.app/webhook`).
3. **Content type**: `application/json`.
4. **Secret**: Enter the **same** `WEBHOOK_SECRET` you put in your `.env`.
5. **Events**: Select "Let me select individual events" and check:
   - [x] Pushes
   - [x] Pull requests
6. Click **Add webhook**.

---

## 🧪 Testing Methods

### Method A: Real Actions (Recommended)
1. **Push**: Commit and push any change to your repository.
2. **Pull Request**: Create a new PR from a feature branch to `main`.
3. **Merge**: Merge that PR into `main`.
Check the dashboard at `http://localhost:5000` to see events appear in < 15s.

### Method B: cURL Simulation (Bypassing Signature)
*Note: This only works if `WEBHOOK_SECRET` is NOT set in your `.env`. If it is set, you must provide a valid HMAC signature header.*

**Push Simulation:**
```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{
    "ref": "refs/heads/main",
    "head_commit": {
      "id": "simulated-push-001",
      "author": {"name": "DevTester"},
      "timestamp": "2024-03-02T19:45:00Z"
    }
  }'
```

**PR Simulation:**
```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d '{
    "action": "opened",
    "pull_request": {
      "id": 202,
      "user": {"login": "FeatureBuilder"},
      "head": {"ref": "patch-1"},
      "base": {"ref": "main"},
      "created_at": "2024-03-02T20:00:00Z"
    }
  }'
```

---

## 📁 Project Overview

- `app.py`: Core logic, signature verification, and event processing.
- `config.py`: MongoDB initialization, indexing (unique IDs), and logging setup.
- `templates/index.html`: Responsive Dark-themed Dashboard.
- `static/script.js`: Polling logic and dynamic DOM updates.

---

## 🏥 Troubleshooting & Inspection

### Common Errors:
- **403 Forbidden**: Your `WEBHOOK_SECRET` in `.env` does not match the one in GitHub.
- **Event Ignored**: The system only tracks `opened` PRs and `merged` PRs. Other actions like `labeled` or `edited` are filtered out.
- **Duplicate ID**: If GitHub retries a delivery, the system will ignore the duplicate `request_id` to maintain data integrity.

### Verification:
- **GitHub**: Visit the "Recent Deliveries" tab in your Repo Webhook settings to see payload details and response codes.
- **MongoDB**: Check the `github_events_db.events` collection to see raw stored data.
