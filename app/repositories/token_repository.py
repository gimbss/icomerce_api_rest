from hashlib import sha256
from datetime import datetime, timezone

from app.models.token import Token


class TokenRepository:
    def __init__(self, session):
        self.session = session

    @staticmethod
    def _hash(token_str: str) -> str:
        return sha256(token_str.encode()).hexdigest()

    def save_token(self, token_str: str, user_id: int, expires_at: datetime) -> Token:
        token = Token(
            token_hash=self._hash(token_str),
            user_id=user_id,
            expires_at=expires_at,
            revoked=False,
        )
        self.session.add(token)
        self.session.flush()
        return token

    def find_valid_token(self, token_str: str) -> Token | None:
        token_hash = self._hash(token_str)
        now = datetime.now(timezone.utc)
        return (
            self.session.query(Token)
            .filter(
                Token.token_hash == token_hash,
                Token.revoked == False,
                Token.expires_at > now,
            )
            .first()
        )

    def revoke_token(self, token_str: str) -> bool:
        token_hash = self._hash(token_str)
        token = (
            self.session.query(Token)
            .filter(Token.token_hash == token_hash)
            .first()
        )
        if not token:
            return False
        token.revoked = True
        self.session.flush()
        return True

    def revoke_all_user_tokens(self, user_id: int) -> int:
        count = (
            self.session.query(Token)
            .filter(Token.user_id == user_id, Token.revoked == False)
            .update({"revoked": True}, synchronize_session="fetch")
        )
        self.session.flush()
        return count

    def delete_expired_tokens(self) -> int:
        now = datetime.now(timezone.utc)
        result = (
            self.session.query(Token)
            .filter(Token.expires_at <= now)
            .delete(synchronize_session="fetch")
        )
        self.session.flush()
        return result
