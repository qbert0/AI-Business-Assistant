FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY main.py ./
COPY worker_main.py ./
COPY conn ./conn
COPY services ./services
COPY configs ./configs
COPY prompts ./prompts
COPY utils ./utils

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
