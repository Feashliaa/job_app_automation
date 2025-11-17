#!/bin/bash
# Exits immediately if a command exits with a non-zero status
set -e

# Start Xvfb - Sets display :99, and sets screen size to 1920x1080 with 24-bit color depth
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 &
sleep 1

# Run gunicorn - Set binding to all interfaces on port 5000 with a timeout of 60 seconds
echo "Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:5000 \
  --timeout 60 \
  --keyfile /certs/server.key \
  --certfile /certs/server.crt \
  app:app
