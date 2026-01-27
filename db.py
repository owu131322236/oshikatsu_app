import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

FLASK_ENV = os.getenv("FLASK_ENV")

from dotenv import load_dotenv
if FLASK_ENV == "development":
    load_dotenv(".env.development")
elif FLASK_ENV == "production":
    load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    echo=False, 
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
