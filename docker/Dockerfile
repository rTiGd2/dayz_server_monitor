FROM python:3.11-slim

WORKDIR /app

# Install system dependencies, including git and gettext
RUN apt-get update && apt-get install -y wget gettext git

# Install supercronic
RUN wget -O /usr/local/bin/supercronic https://github.com/aptible/supercronic/releases/latest/download/supercronic-linux-amd64 \
    && chmod +x /usr/local/bin/supercronic

# Copy project files
COPY requirements.txt ./
COPY monitor.py ./
COPY src/ ./src/
COPY config/ ./config/
COPY locales/ ./locales/
COPY scripts/ ./scripts/
COPY version.txt ./

# Copy Docker-specific scripts and config
COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/crontab.template /tmp/crontab.template
RUN chmod +x /entrypoint.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
