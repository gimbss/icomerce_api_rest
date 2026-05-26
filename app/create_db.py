from app.models.base import Base
import app.models
from app.database.connection import engine, DATABASE_URL
import os


def create_db():
    if DATABASE_URL.startswith('sqlite'):
        path = DATABASE_URL.replace('sqlite:///', '')
        if os.path.exists(path):
            print('Database already exists. Skipping creation.')
            return
        db_dir = os.path.dirname(path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    print('Database tables created successfully.')


if __name__ == '__main__':
    create_db()