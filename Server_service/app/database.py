import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Lấy chuỗi kết nối từ biến môi trường của Docker Compose
# Mặc định sẽ là kết nối tới MariaDB nếu không tìm thấy biến môi trường
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://precisioncast:precisioncast123@mariadb:3306/precisioncast"
)

# 2. Tạo Engine kết nối
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Tạo SessionLocal - dùng để tạo ra các phiên làm việc với DB cho mỗi request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class để các models khác kế thừa
Base = declarative_base()

# 5. Dependency dùng cho API endpoints để lấy DB session và tự động đóng khi xong việc
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()