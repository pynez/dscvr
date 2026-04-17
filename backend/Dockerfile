FROM python:3.12.5 AS builder
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# Create and populate virtualenv with Python deps
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

FROM python:3.12.5-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app

# Copy prebuilt venv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy backend code and runtime assets (data artifacts/seeds are kept via .dockerignore)
COPY src ./src
COPY data ./data

EXPOSE 8080

# Run FastAPI via uvicorn
CMD ["uvicorn", "src.recsys.service.api:app", "--host", "0.0.0.0", "--port", "8080"]
