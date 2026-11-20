from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.core.db import get_db
from app.modules.authorization.deps import get_current_user
from app.modules.identity.models import User
from app.modules.identity.service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: RegisterIn, session: AsyncSession = Depends(get_db)) -> UserOut:
    user = await register_user(
        session,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return UserOut(id=user.id, email=user.email, full_name=user.full_name)


@router.post("/login", response_model=TokenOut)
async def login(
    body: LoginIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> TokenOut:
    _user, token = await login_user(
        session,
        email=body.email,
        password=body.password,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    return TokenOut(access_token=token)


@me_router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, full_name=user.full_name)
