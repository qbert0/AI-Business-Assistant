from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, text
from app.database import Base, engine, get_db
from pydantic import BaseModel

# Khởi tạo app FastAPI
app = FastAPI(
    title="My System API",
    description="API document với Swagger cho hệ thống quản lý File và Chat",
    version="1.0.0"
)

# ---------------------------------------------------------
# Định nghĩa Model (ORM) đại diện cho bảng 'users' trong MariaDB
# ---------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    # Dùng String(36) để lưu UUID dạng chuỗi cho dễ thao tác trong Python
    id = Column(String(36), primary_key=True, index=True, server_default=text("UUID()"))
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)

# ---------------------------------------------------------
# Định nghĩa Schema (Pydantic) dùng để Validate dữ liệu đầu vào/ra
# ---------------------------------------------------------
class UserCreate(BaseModel):
    email: str
    full_name: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True

# ---------------------------------------------------------
# Các API Endpoints
# ---------------------------------------------------------

@app.get("/", tags=["Trang chủ"])
def read_root():
    return {"message": "Server đang chạy! Hãy truy cập /docs để xem Swagger UI"}

# API Lấy danh sách user
@app.get("/users/", response_model=list[UserResponse], tags=["Users"])
def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# API Tạo user mới
@app.post("/users/", response_model=UserResponse, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Kiểm tra email trùng
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký")
    
    # Tạo user mới
    new_user = User(email=user.email, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user