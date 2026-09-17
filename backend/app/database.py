"""
Database connection and session setup.

Uses SQLite for local development. To move to Postgres later (e.g. Supabase
or Neon for deployment), you only need to change DATABASE_URL below and add
`psycopg2-binary` to packages.txt — nothing else in the app changes,
because SQLAlchemy abstracts the actual database engine.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./affordability.db"

# check_same_thread=False is only needed for SQLite (FastAPI runs multiple
# threads); it's ignored automatically once you switch to Postgres.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
