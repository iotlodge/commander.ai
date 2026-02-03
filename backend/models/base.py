"""
Shared SQLAlchemy declarative base for all models
"""

from sqlalchemy.orm import declarative_base

# Single shared Base for all SQLAlchemy models
Base = declarative_base()
