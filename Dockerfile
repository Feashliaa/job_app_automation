FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ make pkg-config \
    default-libmysqlclient-dev \
    curl wget unzip xvfb libxi6 gnupg \
    libnss3 libxss1 libatk-bridge2.0-0 libgtk-3-0 \
    fonts-liberation libasound2 \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

EXPOSE 5000

COPY certs/server.crt /certs/server.crt
COPY certs/server.key /certs/server.key
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--keyfile", "/certs/server.key", "--certfile", "/certs/server.crt", "app:app"]
