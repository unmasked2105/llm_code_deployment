from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import status


templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/ui", response_class=HTMLResponse)
def get_ui(request: Request):

    return templates.TemplateResponse("ui.html", {"request": request})


