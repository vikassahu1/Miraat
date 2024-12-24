from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker,DeclarativeBase

# Database URL - Update these credentials to match your PostgreSQL setup
DATABASE_URL = "postgresql://postgres:postgresvikas@localhost:5432/miraat"  # Changed 'user' to 'postgres'

# Create engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get database session
def get_db():
    try:
        db = SessionLocal()
        yield db
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        raise
    finally:
        db.close()