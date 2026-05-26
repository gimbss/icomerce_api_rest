from datetime import datetime, timedelta, timezone
from os import getenv
from uuid import uuid4

import jwt
from dotenv import load_dotenv

from app.exceptions.auth_exception import InvalidCredentialsError

load_dotenv()

ALGORITHM = "HS256"


def _get_secret() -> str:
    secret = getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not configured")
    return secret


def _get_expiration_hours() -> int:
    try:
        return int(getenv("JWT_EXPIRATION_HOURS", "24"))
    except (ValueError, TypeError):
        return 24


class JwtService:
    """Criação e validação de tokens JWT."""

    def create_token(self, user_id: int, expires_in_hours: int | None = None) -> tuple[str, datetime]:
        hours = expires_in_hours or _get_expiration_hours()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=hours)
        payload = {
            "jti": uuid4().hex,
            "sub": str(user_id),
            "iat": now,
            "exp": expires_at,
        }
        token = jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)
        return token, expires_at

    def validate_token(self, token: str) -> dict:
        """Decodifica e valida a assinatura JWT. Retorna o payload ou levanta InvalidCredentialsError."""
        try:
            payload = jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise InvalidCredentialsError("Token expired")
        except jwt.InvalidTokenError:
            raise InvalidCredentialsError("Invalid token")

    def get_user_id_from_token(self, token: str) -> int:
        """Extrai o user_id de um token válido (valida assinatura JWT)."""
        payload = self.validate_token(token)
        return int(payload["sub"])
