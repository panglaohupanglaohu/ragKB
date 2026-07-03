FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/ /app/src/
COPY config/ /app/config/

RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.0" \
    "httpx>=0.27.0" \
    "aiohttp>=3.9.0" \
    "cryptography>=42.0" \
    "python-dotenv>=1.0.0"

ENV PYTHONPATH=/app/src/backend

EXPOSE 8080

CMD ["python", "src/backend/main.py", "--host", "0.0.0.0", "--port", "8080"]
