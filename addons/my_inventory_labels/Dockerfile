FROM python:3.11-slim

# Install minimal system deps if your app needs them (adjust as necessary)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential netcat \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copy application code
COPY app/ ./app
COPY app/requirements.txt ./requirements.txt

# Install Python dependencies and gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Default port and worker configuration (can be overridden by env)
ENV PORT=5000
ENV GUNICORN_WORKERS=2

EXPOSE ${PORT}

# Run the FastAPI app via gunicorn using uvicorn workers
# Uses environment variables PORT and GUNICORN_WORKERS
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS} --threads 4"]
