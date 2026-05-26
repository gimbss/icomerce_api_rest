from datetime import datetime, timezone

from app.models.email_verification import EmailVerification


class EmailVerificationRepository:
    def __init__(self, session):
        self.session = session

    def create_verification(self, user_id: int, code: str, expires_at: datetime) -> EmailVerification:
        verification = EmailVerification(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
            used=False,
        )
        self.session.add(verification)
        self.session.flush()
        return verification

    def find_valid_code(self, user_id: int, code: str) -> EmailVerification | None:
        now = datetime.now(timezone.utc)
        return (
            self.session.query(EmailVerification)
            .filter(
                EmailVerification.user_id == user_id,
                EmailVerification.code == code,
                EmailVerification.used == False,
                EmailVerification.expires_at > now,
            )
            .first()
        )

    def find_valid_code_by_email(self, email: str, code: str):
        """Find a valid verification code by email and code.
        Returns the EmailVerification object or None."""
        from app.models.user import User
        now = datetime.now(timezone.utc)
        return (
            self.session.query(EmailVerification)
            .join(User, EmailVerification.user_id == User.id)
            .filter(
                User.email == email,
                EmailVerification.code == code,
                EmailVerification.used == False,
                EmailVerification.expires_at > now,
            )
            .first()
        )

    def mark_as_used(self, verification_id: int) -> bool:
        verification = self.session.query(EmailVerification).filter(
            EmailVerification.id == verification_id
        ).first()
        if not verification:
            return False
        verification.used = True
        self.session.flush()
        return True

    def invalidate_all_user_codes(self, user_id: int) -> int:
        count = (
            self.session.query(EmailVerification)
            .filter(EmailVerification.user_id == user_id, EmailVerification.used == False)
            .update({"used": True}, synchronize_session="fetch")
        )
        self.session.flush()
        return count

    def delete_expired_codes(self) -> int:
        now = datetime.now(timezone.utc)
        result = (
            self.session.query(EmailVerification)
            .filter(EmailVerification.expires_at <= now)
            .delete(synchronize_session="fetch")
        )
        self.session.flush()
        return result