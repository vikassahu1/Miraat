from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker,DeclarativeBase

# Database URL - Update these credentials to match your PostgreSQL setup
DATABASE_URL = "postgresql://postgres:postgresvikas@localhost:5432/miraat"  # Changed 'user' to 'postgres'

# Create engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
class Base(DeclarativeBase): 
    pass

# User model
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    email = Column(String, unique=True)



    

