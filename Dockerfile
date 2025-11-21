FROM python:3.11-slim

# ==========================================================
# 1. Install system dependencies
# ==========================================================
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip xvfb \
    gcc g++ make pkg-config \
    default-libmysqlclient-dev \
    libnss3 libxss1 libatk-bridge2.0-0 libgtk-3-0 \
    fonts-liberation libasound2 libu2f-udev \
    libgbm1 libxshmfence1 libglu1-mesa mesa-va-drivers mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# ==========================================================
# 2. Install Google Chrome Stable (Debian 12 compatible)
# ==========================================================
RUN wget -q -O /usr/share/keyrings/google-linux-signing-key.gpg \
        https://dl.google.com/linux/linux_signing_key.pub && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-key.gpg] \
        http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# ==========================================================
# 3. Python environment setup
# ==========================================================
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================================
# 4. Copy application files
# ==========================================================
COPY . .
ENV PYTHONUNBUFFERED=1

# ==========================================================
# 5. Xvfb display for non-headless Chrome
# ==========================================================
ENV DISPLAY=:99

# ==========================================================
# 6. HTTPS certs
# ==========================================================
COPY certs/server.crt /certs/server.crt
COPY certs/server.key /certs/server.key

# ==========================================================
# 7. Entrypoint (starts Xvfb + gunicorn)
# ==========================================================
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
