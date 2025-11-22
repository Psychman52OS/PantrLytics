# ---------- Builder ----------
FROM python:3.12-alpine AS builder
# Build deps for Pillow/Pillow-Heif
RUN apk add --no-cache build-base jpeg-dev zlib-dev libjpeg-turbo-dev libheif-dev

WORKDIR /build

# requirements.txt lives inside the app/ folder in the add-on repo
COPY app/requirements.txt /build/requirements.txt

RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r /build/requirements.txt

# ---------- Final ----------
FROM python:3.12-alpine

# Pillow font dependencies + printing tools
RUN apk add --no-cache cups-client ttf-dejavu freetype fontconfig jpeg zlib libjpeg-turbo libheif

WORKDIR /app

# Bring wheels from builder
COPY --from=builder /build/wheels /wheels

# Copy the entire app directory (includes main.py, static/, templates/, etc.)
COPY app/ /app/

RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

ENV PYTHONUNBUFFERED=1
VOLUME ["/data"]
EXPOSE 8099

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8099", "--proxy-headers", "--forwarded-allow-ips", "*"]
