from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Cấu trúc chung cho dữ liệu Product
class ProductBase(BaseModel):
    product_code: str
    name: str
    dt_status: Optional[str] = "Idle"

# Cấu trúc khi Client gửi lên để tạo mới (không cần ID, không cần CreatedAt)
class ProductCreate(ProductBase):
    pass

# Cấu trúc khi Server trả về (bao gồm ID và CreatedAt)
class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    # Cấu hình để Pydantic đọc được dữ liệu từ SQLAlchemy Model
    class Config:
        from_attributes = True