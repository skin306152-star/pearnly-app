FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8080

COPY requirements.lock.txt requirements-cloud.lock ./
RUN pip install --no-cache-dir -r requirements.lock.txt -r requirements-cloud.lock \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 pearnly \
    && useradd --uid 10001 --gid 10001 --create-home pearnly \
    && mkdir -p /opt/mrpilot/storage /opt/mrpilot/uploads /opt/mrpilot/var \
    && chown -R 10001:10001 /opt/mrpilot /app \
    && chmod -R a+rX /ms-playwright

COPY --chown=10001:10001 . .
COPY --chown=10001:10001 home.html login.html reset.html ./static/
ARG BUILD_SHA
ENV BUILD_SHA=${BUILD_SHA}
LABEL org.opencontainers.image.revision=${BUILD_SHA}
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "services.cloud_runtime.entrypoint"]
