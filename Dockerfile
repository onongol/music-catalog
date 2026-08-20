# Stage 1: build the frontend with Vite. Node lives only here, so the runtime
FROM node:24-slim AS assets

# Install build dependencies
WORKDIR /build

# Copy package files for better caching
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source files and build
COPY vite.config.js ./
COPY assets ./assets

# Copy templates for Vite to process, so that it can resolve the paths in them
COPY catalog/templates ./catalog/templates

RUN npm run build


# Stage 2: the application itself.
FROM python:3.13-slim AS app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip && pip install -r requirements-dev.txt

COPY . .
COPY --from=assets /build/static ./static

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/staticfiles \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
