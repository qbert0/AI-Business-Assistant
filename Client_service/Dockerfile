# Sử dụng image Python nhẹ nhàng
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cập nhật hệ thống cơ bản
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Mở cổng mặc định của Streamlit
EXPOSE 8501

# Lệnh khởi chạy ứng dụng khi container bắt đầu
CMD ["streamlit", "run", "app.main.py", "--server.port=8501", "--server.address=0.0.0.0"]