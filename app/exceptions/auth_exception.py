from .base_exception import AppException


class AuthException(AppException):
    """Base exception for auth-related errors."""
    pass


class EmailAlreadyRegisteredError(AuthException):
    def __init__(self, email: str):
        super().__init__(
            message="Email already registered",
            status_code=409,
        )
        self.email = email


class InvalidCredentialsError(AuthException):
    def __init__(self, message: str = None):
        super().__init__(
            message=message or "Invalid email or password",
            status_code=401,
        )


class UserNotFoundError(AuthException):
    def __init__(self, user_id: int = None):
        msg = "User not found"
        super().__init__(
            message=msg,
            status_code=404,
        )
        self.user_id = user_id


class EmailNotVerifiedError(AuthException):
    def __init__(self, email: str = None):
        super().__init__(
            message="Email not verified. Please verify your email before logging in.",
            status_code=403,
        )
        self.email = email


class InvalidVerificationCodeError(AuthException):
    def __init__(self, message: str = None):
        super().__init__(
            message=message or "Invalid or expired verification code",
            status_code=400,
        )


class CannotDemoteLastAdminError(AuthException):
    def __init__(self):
        super().__init__(
            message="Cannot demote the last admin user. Promote another user to admin first.",
            status_code=403,
        )
