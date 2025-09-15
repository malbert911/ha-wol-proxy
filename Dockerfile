FROM python:3.11-alpine

# Install required packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY run.py .
COPY wol_proxy/ ./wol_proxy/

# Home Assistant add-ons need to run as root to access /data/options.json
# But we can still improve security by setting proper file permissions
RUN chmod 755 /app && \
    chmod 644 /app/*.py && \
    chmod -R 644 /app/wol_proxy/

# Expose default ports (will be overridden by config)
EXPOSE 8080-8090

CMD ["python", "run.py"]
