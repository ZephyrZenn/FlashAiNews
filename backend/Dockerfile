# syntax=docker/dockerfile:1.7

###########
# Builder #
###########
FROM python:3.11-slim AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# 固定 CPU 版 torch，避免拉到 CUDA
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.4.1

COPY requirements.txt ./
# 若 requirements.txt 里还有 torch，请去掉或改成 --no-deps 安装
RUN pip install --no-cache-dir -r requirements.txt --no-binary=hdbscan --prefix=/install

# 裁剪：删测试与缓存，瘦身 .so
RUN find /install -type d -name "tests" -prune -exec rm -rf {} + \
 && find /install -type d -name "__pycache__" -prune -exec rm -rf {} + \
 && find /install -type f -name "*.pyc" -delete -o -name "*.pyo" -delete \
 && (command -v strip >/dev/null && find /install -type f -name "*.so" -exec strip --strip-unneeded {} + || true)

# 如误装了不需要的包（常见：torchvision/torchaudio），删除之
RUN python - <<'PY'
import shutil, sys
base="/install"
for bad in ("torchvision","torchaudio"):
    for p in (f"{base}/lib/python3.11/site-packages/{bad}",
              f"{base}/lib/python3.11/site-packages/{bad}-*.dist-info"):
        for gl in __import__("glob").glob(p):
            shutil.rmtree(gl, ignore_errors=True)
PY

###########
# Runtime #
###########
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/cache/hf TRANSFORMERS_CACHE=/cache/hf
WORKDIR /app

# 若使用 psycopg 原生版才需要；用 psycopg[binary]/psycopg2-binary 可删
# RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

# 只复制“前缀安装”的内容，而不是整块 site-packages
COPY --from=build /install /usr/local

COPY app ./app
COPY run.py ./run.py

EXPOSE 8000
CMD ["python", "run.py"]
