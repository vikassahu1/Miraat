from sqlalchemy import create_engine, Column, String, Integer,DateTime
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from datetime import datetime  
# Database URL - Update these credentials to match your PostgreSQL setup
DATABASE_URL = "postgresql://postgres:postgresvikas@localhost:5432/miraat"  # Changed 'user' to 'postgres'

# Create engine
engine = create_engine(DATABASE_URL,echo=True)

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
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_name = Column(String(50), nullable=False)  # Added length constraint
    userinput = Column(String(500), nullable=False)  # Added length constraint
    response = Column(String(5000), nullable=False)  # Increased length for responses

    

