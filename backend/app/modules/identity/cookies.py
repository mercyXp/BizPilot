from fastapi import Request, Response

from app.core.config import Settings, get_settings
from app.core.errors import AppError

REFRESH_COOKIE = "bp_refresh"
CSRF_COOKIE = "bp_csrf"
COOKIE_PATH = "/api/v1/auth"


def set_auth_cookies(response: Response, *, refresh_token: str, csrf_token: str) -> None:
    settings = get_settings()
    max_age = settings.refresh_token_ttl_days * 86400
    _set_cookie(
        response,
        REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        max_age=max_age,
        settings=settings,
    )
    _set_cookie(
        response,
        CSRF_COOKIE,
        csrf_token,
        httponly=False,
        max_age=max_age,
        settings=settings,
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    _set_cookie(response, REFRESH_COOKIE, "", httponly=True, max_age=0, settings=settings)
    _set_cookie(response, CSRF_COOKIE, "", httponly=False, max_age=0, settings=settings)


def refresh_token_from_request(request: Request) -> str:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise AppError(401, "Refresh token missing", code="unauthenticated")
    return token


def require_csrf(request: Request) -> None:
    header = request.headers.get("x-csrf-token")
    cookie = request.cookies.get(CSRF_COOKIE)
    if not header or not cookie or header != cookie:
        raise AppError(403, "CSRF token missing or invalid", code="csrf_denied")


def _set_cookie(
    response: Response,
    name: str,
    value: str,
    *,
    httponly: bool,
    max_age: int,
    settings: Settings,
) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        httponly=httponly,
        secure=settings.is_production,
        samesite="lax",
        path=COOKIE_PATH,
    )
