FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONNOUSERSITE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    aiohttp>=3.9.0 \
    cryptography>=42.0 \
    fastapi>=0.115.0 \
    httpx>=0.27.0 \
    pydantic>=2.0 \
    pytest==8.3.5 \
    pytest-asyncio>=0.23.0 \
    python-dotenv>=1.0.0 \
    "uvicorn[standard]>=0.30.0"

WORKDIR /workspace
USER 65534:65534
