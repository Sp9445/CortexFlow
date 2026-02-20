from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from datetime import timedelta
from uuid import UUID

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_token_hash,
)
from app.config.settings import settings
from app.utils.timestamps import now_ist
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["Auth"])

def _refresh_token_expires_in_days(remember_me: bool) -> int:
    return settings.REMEMBER_ME_EXPIRE_DAYS if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS

def _set_refresh_cookie(response: Response, refresh_token: str, max_age: int) -> None:
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
        path=settings.REFRESH_TOKEN_COOKIE_PATH,
        max_age=max_age,
    )

def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path=settings.REFRESH_TOKEN_COOKIE_PATH,
    )

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check existing username
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    # Check existing email
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed,
        is_deleted=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    # Find user (not deleted)
    user = db.query(User).filter(
        User.username == login_data.username,
        User.is_deleted == False
    ).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create tokens
    remember_me = bool(login_data.remember_me)
    refresh_days = _refresh_token_expires_in_days(remember_me)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token(
        {"sub": str(user.id), "remember_me": remember_me},
        expires_days=refresh_days,
    )

    # Store hashed refresh token
    expires_at = now_ist() + timedelta(days=refresh_days)
    token_hash = hash_token(refresh_token)
    db_refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(db_refresh)
    db.commit()

    cookie_max_age = refresh_days * 24 * 60 * 60
    _set_refresh_cookie(response, refresh_token, cookie_max_age)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token:
        user_id: Optional[str] = None
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") == "refresh":
                user_id = payload.get("sub")
        except JWTError:
            user_id = None

        if user_id:
            stored_tokens = db.query(RefreshToken).filter(
                RefreshToken.user_id == UUID(user_id),
                RefreshToken.is_revoked == False,
            ).all()
            for token in stored_tokens:
                if verify_token_hash(refresh_token, token.token_hash):
                    token.is_revoked = True
                    db.commit()
                    break

    _clear_refresh_cookie(response)
    return {"detail": "Logged out"}

@router.post("/refresh", response_model=TokenResponse)
def refresh(
    token_data: RefreshRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    # Decode the refresh token (ignore expiration for now)
    refresh_token = (
        token_data.refresh_token
        or request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    )

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Find a non‑revoked, not‑expired refresh token for this user
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > now_ist()
    ).first()
    if not stored_token or not verify_token_hash(refresh_token, stored_token.token_hash):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Mark old token as revoked
    stored_token.is_revoked = True

    # Issue new tokens
    remember_me = bool(payload.get("remember_me", False))
    refresh_days = _refresh_token_expires_in_days(remember_me)

    new_access = create_access_token({"sub": user_id})
    new_refresh = create_refresh_token(
        {"sub": user_id, "remember_me": remember_me},
        expires_days=refresh_days,
    )

    # Store new hashed refresh token
    expires_at = now_ist() + timedelta(days=refresh_days)
    new_token_hash = hash_token(new_refresh)
    new_db_refresh = RefreshToken(
        user_id=user_id,
        token_hash=new_token_hash,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(new_db_refresh)
    db.commit()

    cookie_max_age = refresh_days * 24 * 60 * 60
    _set_refresh_cookie(response, new_refresh, cookie_max_age)

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)
