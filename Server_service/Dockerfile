# Sử dụng Python image nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file requirements trước để tận dụng cache của Docker khi build
COPY requirements.txt .

# Cài đặt các thư viện
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào thư mục /app trong container
COPY . .

# Mở cổng 8000
EXPOSE 8000

# Lệnh khởi chạy server (uvicorn)
# Chú ý: trỏ vào app.main:app vì code nằm trong thư mục app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]