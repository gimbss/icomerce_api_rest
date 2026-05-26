from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError('DATABASE_URL not configured')

# PostgreSQL uses connection pooling and pre-ping for reliability
engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("postgresql"):
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_engine(DATABASE_URL, **engine_kwargs)