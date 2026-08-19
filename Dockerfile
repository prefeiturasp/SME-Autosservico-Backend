FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --no-create-home app

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

COPY --chown=app:app . .

RUN mkdir -p /app/staticfiles && chown -R app:app /app

USER app

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
