FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY main.py ./
COPY publish_test_task.py ./
COPY conn ./conn
COPY utils ./utils
COPY worker ./worker
COPY configs ./configs
COPY deepdoc ./deepdoc

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD ["python", "main.py", "--concurrent", "33"]
