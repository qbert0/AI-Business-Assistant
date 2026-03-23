from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Import các file nội bộ
from . import models, schemas, database

# 1. Khởi tạo FastAPI app
app = FastAPI(title="PrecisionCast Backend API", version="1.0.0")

# 2. Tạo bảng trong Database nếu chưa tồn tại (chỉ dùng cho lúc Dev/Demo)
# Trong thực tế sản xuất, nên dùng tool migration như Alembic
models.Base.metadata.create_engine(bind=database.engine)

# 3. Định nghĩa các API Endpoints (Routes)

@app.get("/")
def read_root():
    """Trang chào mừng cơ bản"""
    return {"message": "Welcome to PrecisionCast Backend API", "docs": "/docs"}

@app.get("/api/health", tags=["System"])
def health_check():
    """API kiểm tra xem server có sống không"""
    return {"status": "healthy"}


@app.post("/api/products/", response_model=schemas.ProductResponse, tags=["Products"])
def create_product(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):
    """API tạo mới một sản phẩm vào Database"""
    # Kiểm tra xem mã sản phẩm đã tồn tại chưa
    db_product = db.query(models.ProductModel).filter(
        models.ProductModel.product_code == product.product_code
    ).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Product code already registered")
    
    # Tạo object Model từ dữ liệu Client gửi lên
    new_product = models.ProductModel(**product.model_dump())
    
    # Lưu vào DB
    db.add(new_product)
    db.commit()
    db.refresh(new_product) # Lấy lại object sau khi đã có ID từ DB
    return new_product


@app.get("/api/products/", response_model=List[schemas.ProductResponse], tags=["Products"])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """API lấy danh sách sản phẩm"""
    products = db.query(models.ProductModel).offset(skip).limit(limit).all()
    return products

# Dòng này để tiện nếu muốn chạy trực tiếp file main.py bằng python (không qua docker CMD)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)