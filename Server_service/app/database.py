import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Lấy URL từ biến môi trường (do Docker Compose truyền vào). 
# Nếu không có (ví dụ khi bạn chạy code trực tiếp trên máy không dùng docker), nó sẽ dùng localhost để dự phòng.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://precisioncast:precisioncast123@localhost:3306/precisioncast"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()