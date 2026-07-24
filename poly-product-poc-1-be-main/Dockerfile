FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies for PDF parsing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install poetry or requirements? 
# Assuming requirements.txt for now. Tell me if you're using poetry
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . /app/

# Expose port
EXPOSE 8001

# Launch
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
