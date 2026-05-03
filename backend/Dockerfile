FROM python:3.11-slim

# Bring in uv binary from official image — fast resolver/installer
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies via uv — orders of magnitude faster than pip
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/static

# Expose port
EXPOSE 8000

# Run init script and start server
CMD ["sh", "-c", "python scripts/init_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
