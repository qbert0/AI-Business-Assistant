from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    # Ví dụ thông tin về Digital Twin: Trạng thái mô phỏng
    dt_status = Column(String(50), default="Idle") # Idle, Running, Error
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())