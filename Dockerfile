FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ make pkg-config \
    default-libmysqlclient-dev \
    curl wget unzip xvfb libxi6 gnupg \
    libnss3 libxss1 libatk-bridge2.0-0 libgtk-3-0 \
    fonts-liberation libasound2 \
    chromium \
    chromium-driver \
    libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

EXPOSE 5000

# copy certs for https
COPY certs/server.crt /certs/server.crt
COPY certs/server.key /certs/server.key

# use entrypoint script to start Xvfb and gunicorn
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
