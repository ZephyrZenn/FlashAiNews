###########
# Builder #
###########
FROM python:3.11-slim AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Install torch from the CPU wheels first to avoid pulling GPU builds
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        --prefix=/install torch==2.4.1 typing_extensions>=4.8.0

# Install the remaining Python dependencies into /install
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt --no-binary=hdbscan

# Trim unneeded test files, caches, and debug symbols
RUN find /install -type d -name "tests" -prune -exec rm -rf {} + \
 && find /install -type d -name "__pycache__" -prune -exec rm -rf {} + \
 && find /install -type f -name "*.pyc" -delete -o -name "*.pyo" -delete \
 && (command -v strip >/dev/null && find /install -type f -name "*.so" -exec strip --strip-unneeded {} + || true)


###########
# Runtime #
###########
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/cache/hf \
    TRANSFORMERS_CACHE=/cache/hf \
    ENV=prod \
    PYTHONPATH=/app
WORKDIR /app

COPY --from=build /install /usr/local

COPY apps/backend ./apps/backend
COPY core ./core
# COPY config.toml ./config.toml

EXPOSE 8000

CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
