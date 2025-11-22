FROM python:3.11-slim

# Install minimal system deps if your app needs them (adjust as necessary)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential netcat \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copy application code
COPY app/ ./app
COPY app/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# Ensure the app listens on 0.0.0.0 and uses the configured port (defaults to 5000)
# Adjust this command if your app uses gunicorn/uvicorn or a different entrypoint.
CMD ["python", "app/main.py"]
