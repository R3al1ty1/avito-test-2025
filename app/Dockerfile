FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN pip install pytest pytest-asyncio httpx sqlalchemy coverage pytest-cov

COPY . .

CMD ["python", "main.py"]