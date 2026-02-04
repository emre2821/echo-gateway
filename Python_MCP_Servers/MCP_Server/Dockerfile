FROM python:3.11-slim

WORKDIR /app

# install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8766 8765

CMD ["python", "http_api.py"]
