FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cron goaccess \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000 8001

ENTRYPOINT ["/bin/sh", "./docker/entrypoint.sh"]
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8000", "app:app"]
