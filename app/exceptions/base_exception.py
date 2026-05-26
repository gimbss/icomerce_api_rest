class AppException(Exception):
    """Base exception for all application exceptions."""

    def __init__(self, message: str = "An error occurred", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.message
