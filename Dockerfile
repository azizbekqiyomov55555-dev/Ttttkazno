FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Tizim paketlari (tzdata pytz uchun foydali)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Bot ma'lumotlari saqlanadigan papka (volume bilan ulanadi)
RUN mkdir -p /app/bot_data

CMD ["python", "obmen_bot.py"]
