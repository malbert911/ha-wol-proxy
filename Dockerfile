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

# Make run script executable
RUN chmod +x run.py

# Expose default ports (will be overridden by config)
EXPOSE 8080-8090

CMD ["python", "run.py"]
