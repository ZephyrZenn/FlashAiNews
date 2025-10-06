###########
# Builder #
###########
FROM python:3.11-slim AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    --prefix=/install torch==2.4.1 typing_extensions>=4.8.0

COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install cython numpy scikit-learn
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt --no-binary=hdbscan

# 精简
RUN find /install -type d -name "tests" -prune -exec rm -rf {} + \
 && find /install -type d -name "__pycache__" -prune -exec rm -rf {} + \
 && find /install -type f -name "*.pyc" -delete -o -name "*.pyo" -delete \
 && (command -v strip >/dev/null && find /install -type f -name "*.so" -exec strip --strip-unneeded {} + || true)

RUN python - <<'PY'
import sys
sys.path.insert(0,"/install/lib/python3.11/site-packages")
import typing_extensions, torch
print("deps ok")
PY

###########
# Runtime #
###########
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/cache/hf TRANSFORMERS_CACHE=/cache/hf
WORKDIR /app

COPY --from=build /install /usr/local
COPY app ./app
COPY run.py ./run.py

EXPOSE 8000
CMD ["python", "run.py"]
