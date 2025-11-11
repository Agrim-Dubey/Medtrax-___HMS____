FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /app/
RUN apt-get update && apt-get install -y netcat-traditional && \
    pip install --upgrade pip && pip install -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN adduser --disabled-password medtraxuser
USER medtraxuser

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "medtrax.asgi:application"]
