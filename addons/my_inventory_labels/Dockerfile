FROM python:3.11-slim

# Install minimal system deps if your app needs them (adjust as necessary)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential netcat \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copy application code
COPY app/ ./app
COPY app/requirements.txt ./requirements.txt
COPY run.sh /run.sh

# Install Python dependencies and gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn
RUN chmod +x /run.sh

# Default port and worker configuration (can be overridden by env)
ENV PORT=5000
ENV GUNICORN_WORKERS=2

EXPOSE ${PORT}

# Run the FastAPI app via gunicorn using uvicorn workers
# Uses environment variables PORT and GUNICORN_WORKERS
CMD ["/run.sh"]
