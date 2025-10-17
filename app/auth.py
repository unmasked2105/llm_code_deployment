import os
import secrets
from typing import Optional

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware


router = APIRouter()
templates = Jinja2Templates(directory="templates")


def add_session(app):

    secret = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)
    app.add_middleware(SessionMiddleware, secret_key=secret)


@router.get("/login/github")
async def login_github(request: Request):

    client_id = os.getenv("GITHUB_CLIENT_ID")
    redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/callback")
    scope = "repo"
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}"
    )
    return RedirectResponse(url)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):

    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/auth/callback")
async def github_callback(request: Request):

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or state != request.session.get("oauth_state"):
        return RedirectResponse("/ui")

    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    token_url = "https://github.com/login/oauth/access_token"

    async with httpx.AsyncClient() as client:
        headers = {"Accept": "application/json"}
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        }
        resp = await client.post(token_url, headers=headers, data=data, timeout=20)
        resp.raise_for_status()
        token_data = resp.json()

    access_token: Optional[str] = token_data.get("access_token")
    if access_token:
        request.session["gh_token"] = access_token
    return RedirectResponse("/login")


@router.get("/logout")
async def logout(request: Request):

    request.session.clear()
    return RedirectResponse("/login")


