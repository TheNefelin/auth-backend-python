"""Base model class for SQLAlchemy ORM."""

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# Naming convention for indexes and constraints
# This helps avoid conflicts and makes migrations more predictable
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(referred_table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}

Base = declarative_base(metadata=MetaData(naming_convention=naming_convention))