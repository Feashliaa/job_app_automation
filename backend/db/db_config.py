# Expected env vars: SQL_USER, SQL_PASSWORD (loaded via utils.load_env_variables)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..services.utils import load_env_variables

env_vars = load_env_variables()
USERNAME = env_vars["SQL_USER"]
PASSWORD = env_vars["SQL_PASSWORD"]
HOST = "db"
PORT = 3306
DATABASE = "jobs"

# SQLAlchemy connection URL
DB_URL = (
    f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4"
)

# Create engine and session
# Change "echo" to false if you dont want to see raw SQL queries in the console
engine = create_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=5
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Provide a session for database operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
