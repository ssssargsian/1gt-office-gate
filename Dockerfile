FROM python:3.9-slim as base

WORKDIR /app
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

FROM base

COPY . .
ENV PYTHONPATH=/app

EXPOSE 5000
CMD ["python", "app.py"]