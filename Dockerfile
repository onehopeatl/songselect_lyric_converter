FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY app/requirements-pip.txt app/requirements.txt ./
RUN apk upgrade --no-cache \
    && python -m pip install --upgrade --require-hashes -r requirements-pip.txt \
    && python -m pip --version \
    && python -m pip install --require-hashes -r requirements.txt \
    && addgroup -S converter \
    && adduser -S -G converter converter

COPY app/ /app/
ARG APP_VERSION=docker-dev-build
RUN printf '%s\n' "$APP_VERSION" > sslc_app_version

USER converter
EXPOSE 8080
CMD ["gunicorn", "--config", "gunicorn_config.py", "webapp:app"]
