from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker,DeclarativeBase


# Base class for models
class Base(DeclarativeBase): 
    pass


# User model
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String, nullable=True)