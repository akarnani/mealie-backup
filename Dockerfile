# Use stable Python 3.14 (released Oct 2025)
FROM python:3.14.3-slim

WORKDIR /app

# Ensure logs are sent to the terminal immediately
ENV PYTHONUNBUFFERED=1

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

# Default values for environment variables
ENV BACKUP_PATH=/backups
ENV MEALIE_URL=""
ENV MEALIE_TOKEN=""
ENV SUCCESS_URL=""

ENTRYPOINT ["python", "backup.py"]
