from sqlalchemy import create_engine, Column, String, Integer,DateTime
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Text # Import Text
from datetime import datetime  
from dotenv import load_dotenv
import os
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL,echo=False)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
class Base(DeclarativeBase): 
    pass

# User model
class User(Base):
    __tablename__ = "user_info"
    name = Column(String, primary_key=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)


class TestHistory(Base):
    __tablename__ = "test_history"
    test_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.now, nullable=False)
    user_name = Column(String(50), nullable=False)
    encrypted_session_data = Column(Text, nullable=False) 
    encrypted_final_report = Column(Text, nullable=False)

    

