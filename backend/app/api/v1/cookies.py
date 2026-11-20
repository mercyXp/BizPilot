from fastapi import Request, Response

from app.core.config import Settings


def set_refresh_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/api/v1/auth",
        max_age=settings.refresh_token_days * 24 * 60 * 60,
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path="/api/v1/auth",
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
    )


def read_refresh_cookie(request: Request, settings: Settings) -> str:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        from app.core.errors import ApiError

        raise ApiError(401, "unauthenticated", "Refresh token missing")
    return token


def read_csrf_header(request: Request) -> str:
    token = request.headers.get("x-csrf-token")
    if not token:
        from app.core.errors import ApiError

        raise ApiError(403, "permission_denied", "CSRF token missing")
    return token
