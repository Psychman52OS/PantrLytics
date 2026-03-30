# ---------- Builder ----------
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libheif-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY app/requirements.txt /build/requirements.txt

RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r /build/requirements.txt

# ---------- Final ----------
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cups-client \
    fonts-dejavu-core \
    libfreetype6 \
    fontconfig \
    libjpeg62-turbo \
    zlib1g \
    libheif1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/wheels /wheels
COPY app/ /app/

RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

ENV PYTHONUNBUFFERED=1
ENV PORT=8099
VOLUME ["/data"]
EXPOSE ${PORT}

CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8099} --proxy-headers --forwarded-allow-ips '*'"]
