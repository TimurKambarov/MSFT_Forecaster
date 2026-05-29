FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY dashboard/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir yfinance

# Copy application code
COPY dashboard/ ./dashboard/
COPY src/       ./src/
COPY setup_db.py .

# Copy models (required for predictions)
COPY models/ ./models/

# Create db directory (populated at runtime by entrypoint)
RUN mkdir -p db

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
