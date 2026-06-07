"""
Authentication router — handles login, register, and logout flows.
Serves both HTML pages (Jinja2) and JSON API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserRegister, UserLogin, UserOut, Token
from app.services import create_user, authenticate_user, get_user_by_email
from app.utils.auth import create_access_token, get_current_user_from_cookie

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ─── Page Routes ─────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    """Render login page; redirect to dashboard if already authenticated."""
    if get_current_user_from_cookie(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_page(request: Request):
    if get_current_user_from_cookie(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process login form; set JWT cookie on success."""
    try:
        user = authenticate_user(db, email, password)
        token = create_access_token({"sub": user.email, "user_id": user.id})
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=60 * 60 * 8,  # 8 hours
            samesite="lax",
        )
        return response
    except HTTPException as e:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": e.detail},
            status_code=200,
        )


@router.post("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process registration form."""
    try:
        data = UserRegister(full_name=full_name, email=email, password=password)
        create_user(db, data)
        return RedirectResponse(
            url="/login?registered=1", status_code=302
        )
    except Exception as e:
        error_msg = getattr(e, "detail", str(e))
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": error_msg},
            status_code=200,
        )


@router.get("/logout", include_in_schema=False)
async def logout():
    """Clear the auth cookie and redirect to login."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ─── REST API Endpoints ───────────────────────────────────────────────────────

@router.post("/api/auth/register", response_model=UserOut, tags=["Auth API"])
async def api_register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user via the REST API."""
    return create_user(db, data)


@router.post("/api/auth/login", response_model=Token, tags=["Auth API"])
async def api_login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and return a JWT token."""
    user = authenticate_user(db, data.email, data.password)
    token = create_access_token({"sub": user.email, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}
