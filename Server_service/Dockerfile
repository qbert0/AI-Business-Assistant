# Sử dụng Python 3.10 (hoặc bản bạn đang dùng)
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy và cài đặt thư viện trước (giúp build nhanh hơn ở các lần sau)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Chạy server FastAPI (Lưu ý: do code của bạn nằm trong thư mục 'app', nên gọi là app.main:app)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]