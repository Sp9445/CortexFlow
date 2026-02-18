import bcrypt
import hashlib
import base64
from jose import jwt
from datetime import datetime, timedelta
from app.config.settings import settings

def pre_hash_password(password: str) -> str:
    """SHA‑256 + base64 – output is always 44 characters."""
    hash_bytes = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(hash_bytes).decode("ascii")

def get_password_hash(password: str) -> str:
    pre_hashed = pre_hash_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pre_hashed = pre_hash_password(plain_password)
    return bcrypt.checkpw(pre_hashed.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def hash_token(token: str) -> str:
    """Hash a refresh token – pre‑hash with SHA‑256 first."""
    pre_hashed = pre_hash_password(token)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_token_hash(plain_token: str, hashed_token: str) -> bool:
    pre_hashed = pre_hash_password(plain_token)
    return bcrypt.checkpw(pre_hashed.encode("utf-8"), hashed_token.encode("utf-8"))