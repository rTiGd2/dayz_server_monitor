FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y cron gettext

# Copy only needed files and folders
COPY requirements.txt ./
COPY monitor.py ./
COPY src/ ./src/
COPY config/ ./config/
COPY locales/ ./locales/
COPY scripts/ ./scripts/
COPY version.txt ./

# Copy Docker-specific scripts and config
COPY docker/crontab.template /etc/cron.d/template
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
