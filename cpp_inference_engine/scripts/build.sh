#!/bin/bash
set -e

echo "Building Docker image for API..."
docker build -f Dockerfile -t email-api .

echo "Starting FastAPI container on port 8000..."
docker run -d --rm -p 8000:8000 --name email-api email-api

# Wait for the API to be live
echo "Waiting for API to become ready..."
until curl -s http://localhost:8000 > /dev/null; do
    sleep 1
done

echo "FastAPI server is running at http://localhost:8000"
