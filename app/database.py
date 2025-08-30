from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# For PostgreSQL (change username, password, dbname)
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost/kmrl_db"

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()
