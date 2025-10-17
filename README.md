TDS_4 FastAPI App

Setup

1) Create and activate a virtual environment (Windows PowerShell):
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2) Install dependencies:
```
pip install -r requirements.txt
```

Run

```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Environment via .env

Create a file named `.env` in the project root with:

```
SECRET_KEY=secret123
GITHUB_TOKEN=ghp_yourtokenhere
EVAL_SERVER_URL=https://webhook.site/your-uuid
EVAL_FORMAT=json
# Optional if wiring real OpenAI generation later
OPENAI_API_KEY=sk-yourkey
ENABLE_GITHUB_ISSUE=true

# SMTP (optional - enable email notifications if set)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASS=yourpassword
MAIL_FROM=you@example.com
MAIL_TO=recipient@example.com

# GitHub OAuth (to create repos as the logged-in user)
SESSION_SECRET=change-me
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
# For local dev, set to your app callback: http://localhost:8000/auth/callback
GITHUB_REDIRECT_URI=http://localhost:8000/auth/callback
# Optional: hint to show repo link in the UI immediately
GITHUB_USER_HINT=your-github-username

Request options:
- notify_url: override evaluator endpoint per request
- notify_email: send notification to this email (uses SMTP settings)
```

Endpoints

- GET /health -> {"status":"ok"}
- POST /validate -> Validates secret key
 - POST /generate -> Accepts generation request, returns 202, processes in background
 - GET /ui -> Minimal form UI to trigger generation

Environment (optional)

```
$env:SECRET_KEY = "secret123"
$env:GITHUB_TOKEN = "ghp_..."
$env:EVAL_SERVER_URL = "https://example.com/evaluate"
```


