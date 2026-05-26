from sqlalchemy.orm import Session
import logging
from .session import SessionLocal
import app.models
import app.repositories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnitOfWork:
    def __init__(self):
        self._session = None

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = SessionLocal()
        return self._session

    def __enter__(self):

        self.users = app.repositories.UserRepository(self.session)
        self.products = app.repositories.ProductRepository(self.session)
        self.orders = app.repositories.OrderRepository(self.session)
        self.tokens = app.repositories.TokenRepository(self.session)
        self.email_verifications = app.repositories.EmailVerificationRepository(self.session)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if exc_type:
            logger.error(f"An error occurred: {exc_val}")
            self.session.rollback()
        else:
            self.session.commit()

        self.session.close()
        self._session = None