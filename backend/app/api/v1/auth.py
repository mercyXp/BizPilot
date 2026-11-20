from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    EmailIn,
    LoginIn,
    PasswordResetConfirmIn,
    RegisterIn,
    RegisterOut,
    TokenOut,
    TotpConfirmIn,
    TotpDisableIn,
    UserOut,
    VerifyEmailIn,
)
from app.core.db import get_db
from app.core.errors import AppError
from app.modules.authorization.deps import get_current_user
from app.modules.identity.cookies import (
    clear_auth_cookies,
    refresh_token_from_request,
    require_csrf,
    set_auth_cookies,
)
from app.modules.identity.models import User
from app.modules.identity.service import (
    confirm_password_reset,
    confirm_totp,
    disable_totp,
    enable_totp,
    expose_dev_token,
    login_user,
    logout_session,
    refresh_session,
    register_user,
    request_password_reset,
    resend_verification,
    verify_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["auth"])


@router.post("/register", response_model=RegisterOut, status_code=201)
async def register(body: RegisterIn, session: AsyncSession = Depends(get_db)) -> RegisterOut:
    user, token = await register_user(
        session,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return RegisterOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        email_verified=False,
        totp_enabled=False,
        verification_token=expose_dev_token(token),
    )


@router.post("/login", response_model=TokenOut)
async def login(
    body: LoginIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenOut:
    result = await login_user(
        session,
        email=body.email,
        password=body.password,
        totp_code=body.totp_code,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    if result.refresh_token and result.csrf_token:
        set_auth_cookies(response, refresh_token=result.refresh_token, csrf_token=result.csrf_token)
    return TokenOut(
        access_token=result.access_token,
        email_verified=result.user.email_verified_at is not None,
        totp_required=result.totp_required,
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenOut:
    require_csrf(request)
    result = await refresh_session(session, refresh_token_from_request(request))
    if result.refresh_token and result.csrf_token:
        set_auth_cookies(response, refresh_token=result.refresh_token, csrf_token=result.csrf_token)
    return TokenOut(
        access_token=result.access_token,
        email_verified=result.user.email_verified_at is not None,
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> None:
    require_csrf(request)
    try:
        raw = refresh_token_from_request(request)
    except AppError:
        clear_auth_cookies(response)
        return
    await logout_session(session, raw)
    clear_auth_cookies(response)


@router.post("/verify-email", response_model=UserOut)
async def verify(body: VerifyEmailIn, session: AsyncSession = Depends(get_db)) -> UserOut:
    user = await verify_email(session, body.token)
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        email_verified=True,
        totp_enabled=user.totp_secret_encrypted is not None,
    )


@router.post("/resend-verification")
async def resend(body: EmailIn, session: AsyncSession = Depends(get_db)) -> dict:
    token = await resend_verification(session, body.email)
    return {"status": "ok", "verification_token": expose_dev_token(token)}


@router.post("/password-reset")
async def password_reset(body: EmailIn, session: AsyncSession = Depends(get_db)) -> dict:
    token = await request_password_reset(session, body.email)
    return {"status": "ok", "reset_token": expose_dev_token(token)}


@router.post("/password-reset/confirm", status_code=204)
async def password_reset_confirm(
    body: PasswordResetConfirmIn, session: AsyncSession = Depends(get_db)
) -> None:
    await confirm_password_reset(session, body.token, body.password)


@router.post("/totp/enable")
async def totp_enable(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    secret, uri = await enable_totp(session, user)
    return {"secret": secret, "otpauth_uri": uri}


@router.post("/totp/confirm", status_code=204)
async def totp_confirm(
    body: TotpConfirmIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await confirm_totp(session, user, body.code)


@router.post("/totp/disable", status_code=204)
async def totp_disable(
    body: TotpDisableIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await disable_totp(session, user, body.password, body.code)


@me_router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        email_verified=user.email_verified_at is not None,
        totp_enabled=user.totp_secret_encrypted is not None,
    )
