FROM python:3.12-slim-bullseye

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create directory for mounted databases
RUN mkdir -p /data/db

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install --no-cache -e .

# Expose port
EXPOSE 80

# Run the application.
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
