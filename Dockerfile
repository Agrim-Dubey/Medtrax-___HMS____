FROM python:3.12-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/apps

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    jpeg-dev \
    zlib-dev \
    libpng-dev \
    netcat-openbsd

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create static and media directories
RUN mkdir -p /app/static /app/media && \
    chmod -R 755 /app/static /app/media

# Expose port
EXPOSE 8000

# Default command
CMD python manage.py migrate && python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 config.asgi:application
