from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pin(pin: str) -> str:
    return pwd_ctx.hash(pin)


def verify_pin(pin: str, hashed: str) -> bool:
    return pwd_ctx.verify(pin, hashed)


def create_access_token(user_id: UUID, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_access_ttl)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "exp": expire, "type": "access"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_refresh_ttl)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return {}


def normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    return f"+{digits}"
