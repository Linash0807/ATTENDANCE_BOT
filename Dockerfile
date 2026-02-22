FROM python:3.13-slim-bullseye

# Install system dependencies for Chromium and the dynamic linker
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libatk-bridge2.0-0 \
    libcups2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libxss1 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libxrandr2 \
    libatk1.0-0 \
    libcairo2 \
    libdrm2 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libvulkan1 \
    xdg-utils \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables for the bot to find the browser
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# Expose the port (though polling doesn't strictly need it, good for Railway)
EXPOSE 8080

# Command to run the bot
CMD ["python", "bot.py"]
