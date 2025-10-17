import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .schemas import GenerateRequest, GenerateAcceptedResponse
from .llm_generator import generate_app_files
from .github_utils import create_repo_and_commit, create_issue
from .notify import notify_evaluator, send_email_notification
from .ui import router as ui_router
from .auth import router as auth_router, add_session
try:
    from github import Github as _GithubClient
except Exception:
    _GithubClient = None


load_dotenv()

app = FastAPI(title="TDS_4 FastAPI App", version="0.1.0")
add_session(app)

# Allow CORS and browser preflight (OPTIONS) during local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():

    return {"status": "ok"}


class ValidateRequest(BaseModel):
    secret_key: str


@app.post("/validate")
@app.post("/validate/")
def validate_secret(request: ValidateRequest):

    expected = os.getenv("SECRET_KEY", "secret123")
    if request.secret_key != expected:
        raise HTTPException(status_code=401, detail="Invalid secret key")
    return {"valid": True}


def _process_generation(req: GenerateRequest, token: str | None = None) -> None:

    if os.getenv("SECRET_KEY") and req.secret_key and req.secret_key != os.getenv("SECRET_KEY"):
        return

    files = generate_app_files(description=req.description, requirements=req.requirements)

    effective_token = token or os.getenv("GITHUB_TOKEN")
    if not effective_token:
        return
    repo_info = create_repo_and_commit(token=effective_token, repo_name=req.project_name, files=files)

    notify_url = req.notify_url or os.getenv("EVAL_SERVER_URL")
    if notify_url:
        payload = {
            "project_name": req.project_name,
            "repo_url": repo_info.get("clone_url"),
            "metadata": req.metadata or {},
        }
        notify_evaluator(url=notify_url, payload=payload)

    if os.getenv("ENABLE_GITHUB_ISSUE", "true").lower() in ("1", "true", "yes"):
        title = f"Generation completed for {req.project_name}"
        body = f"Repository: {repo_info.get('html_url')}\n\nMetadata: {req.metadata or {}}"
        try:
            create_issue(token=effective_token, full_name=repo_info.get("full_name", ""), title=title, body=body)
        except Exception:
            pass

    target_email = req.notify_email or os.getenv("MAIL_TO")
    if target_email:
        subject = f"Repo created: {req.project_name}"
        body = (
            f"Project: {req.project_name}\n"
            f"Repo: {repo_info.get('html_url')}\n"
            f"Clone: {repo_info.get('clone_url')}\n"
        )
        try:
            # Temporarily override MAIL_TO via environment for this call
            os.environ["MAIL_TO"] = target_email
            send_email_notification(subject=subject, body=body)
        except Exception:
            pass


@app.post("/generate", response_model=GenerateAcceptedResponse, status_code=202)
def generate_endpoint(request: GenerateRequest, background: BackgroundTasks, http_request: Request):

    if os.getenv("SECRET_KEY") and request.secret_key and request.secret_key != os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Invalid secret key")

    # Require user GitHub login and use their token for repo creation
    session_token = http_request.session.get("gh_token") if hasattr(http_request, "session") else None
    if not session_token:
        raise HTTPException(status_code=401, detail="GitHub login required. Go to /login/github")

    background.add_task(_process_generation, request, session_token)

    expected_repo_html = None
    gh_user = None
    # Prefer to derive the username from the available token to avoid mismatches
    effective_token = session_token or os.getenv("GITHUB_TOKEN")
    if _GithubClient and effective_token:
        try:
            gh_user = _GithubClient(effective_token).get_user().login
        except Exception:
            gh_user = None
    if not gh_user:
        gh_user = os.getenv("GITHUB_USER_HINT")
    if gh_user:
        expected_repo_html = f"https://github.com/{gh_user}/{request.project_name}"
    return GenerateAcceptedResponse(status="accepted", project_name=request.project_name, message="Generation started", expected_repo_html=expected_repo_html)


@app.get("/me")
def whoami(http_request: Request):

    session_token = http_request.session.get("gh_token") if hasattr(http_request, "session") else None
    if not session_token or not _GithubClient:
        raise HTTPException(status_code=401, detail="Not logged in with GitHub")
    try:
        user = _GithubClient(session_token).get_user()
        return {"login": user.login, "html_url": user.html_url}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid GitHub session. Please login again.")


@app.get("/check/{project_name}")
def check_repo(project_name: str, http_request: Request):

    session_token = http_request.session.get("gh_token") if hasattr(http_request, "session") else None
    token = session_token or os.getenv("GITHUB_TOKEN")
    if not token or not _GithubClient:
        raise HTTPException(status_code=401, detail="No GitHub token available")
    try:
        gh = _GithubClient(token)
        login = gh.get_user().login
        full_name = f"{login}/{project_name}"
        repo = gh.get_repo(full_name)
        return {"exists": True, "full_name": repo.full_name, "html_url": repo.html_url}
    except Exception:
        return {"exists": False}


@app.post("/deploy")
def deploy_endpoint(request: GenerateRequest, http_request: Request):

    """
    Synchronous deploy endpoint that uses the logged-in user's GitHub token (session)
    to create the repository immediately and return repo information.
    """

    # Require user GitHub login and use their token for repo creation
    session_token = http_request.session.get("gh_token") if hasattr(http_request, "session") else None
    if not session_token:
        raise HTTPException(status_code=401, detail="GitHub login required. Go to /login/github")

    # Validate secret if needed
    if os.getenv("SECRET_KEY") and request.secret_key and request.secret_key != os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Invalid secret key")

    try:
        files = generate_app_files(description=request.description, requirements=request.requirements)
        repo_info = create_repo_and_commit(token=session_token, repo_name=request.project_name, files=files)

        # Best-effort: create issue
        try:
            if os.getenv("ENABLE_GITHUB_ISSUE", "true").lower() in ("1", "true", "yes"):
                title = f"Generation completed for {request.project_name}"
                body = f"Repository: {repo_info.get('html_url')}\n\nMetadata: {request.metadata or {}}"
                create_issue(token=session_token, full_name=repo_info.get("full_name", ""), title=title, body=body)
        except Exception:
            pass

        # Best-effort: notify evaluator
        try:
            notify_url = request.notify_url or os.getenv("EVAL_SERVER_URL")
            if notify_url:
                payload = {"project_name": request.project_name, "repo_url": repo_info.get("clone_url"), "metadata": request.metadata or {}}
                notify_evaluator(url=notify_url, payload=payload)
        except Exception:
            pass

        # Best-effort: send email
        try:
            target_email = request.notify_email or os.getenv("MAIL_TO")
            if target_email:
                os.environ["MAIL_TO"] = target_email
                subject = f"Repo created: {request.project_name}"
                body = (
                    f"Project: {request.project_name}\n"
                    f"Repo: {repo_info.get('html_url')}\n"
                    f"Clone: {repo_info.get('clone_url')}\n"
                )
                send_email_notification(subject=subject, body=body)
        except Exception:
            pass

        return {"status": "deployed", "repo": repo_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# UI routes
app.include_router(ui_router)
app.include_router(auth_router)


