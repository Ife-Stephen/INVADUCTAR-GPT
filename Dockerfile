# Use a Python base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy everything
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that HF Spaces expects
EXPOSE 7860

# Run your API server
CMD ["python", "api_server.py"]
