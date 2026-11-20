from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.cookies import (
    clear_refresh_cookie,
    read_csrf_header,
    read_refresh_cookie,
    set_refresh_cookie,
)
from app.api.v1.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.errors import ApiError
from app.core.rate_limit import allow_attempt
from app.models.user import User
from app.modules.identity import service as identity
from app.modules.identity.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserPublic,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _token_response(
    response: Response,
    settings: Settings,
    user: User,
    access: str,
    refresh: str,
    csrf: str,
) -> TokenResponse:
    set_refresh_cookie(response, settings, refresh)
    return TokenResponse(
        access_token=access,
        expires_in=settings.access_token_minutes * 60,
        csrf_token=csrf,
        user=UserPublic(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            email_verified=user.email_verified_at is not None,
            created_at=user.created_at,
        ),
    )


@router.post("/register", status_code=201)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    key = f"register:{normalize_ip_email(_client_ip(request), payload.email)}"
    if not await allow_attempt(key, settings.auth_rate_limit_attempts, settings.auth_rate_limit_window_seconds):
        raise ApiError(429, "rate_limited", "Too many attempts. Try again later.")
    user, _token = await identity.register_user(
        db,
        settings,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "email_verified": False,
        "message": "Check your email to verify your account.",
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    key = f"login:{normalize_ip_email(_client_ip(request), payload.email)}"
    if not await allow_attempt(key, settings.auth_rate_limit_attempts, settings.auth_rate_limit_window_seconds):
        raise ApiError(429, "rate_limited", "Too many attempts. Try again later.")
    user, _session, access, refresh, csrf = await identity.authenticate(
        db,
        settings,
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
        ip=_client_ip(request),
    )
    return _token_response(response, settings, user, access, refresh, csrf)


def normalize_ip_email(ip: str | None, email: str) -> str:
    return f"{ip or '-'}:{email.strip().lower()}"


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    refresh_token = read_refresh_cookie(request, settings)
    csrf = read_csrf_header(request)
    user, _session, access, new_refresh, new_csrf = await identity.rotate_refresh(
        db,
        settings,
        refresh_token=refresh_token,
        csrf_token=csrf,
        user_agent=request.headers.get("user-agent"),
        ip=_client_ip(request),
    )
    return _token_response(response, settings, user, access, new_refresh, new_csrf)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_user),
) -> None:
    await identity.logout(db, request.state.session)
    clear_refresh_cookie(response, settings)


@router.post("/verify-email")
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await identity.verify_email(db, payload.token)
    return {"email": user.email, "email_verified": True}


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    key = f"forgot:{_client_ip(request)}"
    if not await allow_attempt(key, settings.auth_rate_limit_attempts, settings.auth_rate_limit_window_seconds):
        raise ApiError(429, "rate_limited", "Too many attempts. Try again later.")
    await identity.request_password_reset(db, settings, payload.email)
    return {"message": "If that account exists, a reset email has been sent."}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await identity.reset_password(db, payload.token, payload.password)
    return {"message": "Password updated. You can sign in with your new password."}


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        email_verified=user.email_verified_at is not None,
        created_at=user.created_at,
    )
