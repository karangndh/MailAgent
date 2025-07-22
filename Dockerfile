FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application files
COPY . .

# Create data directory for database
RUN mkdir -p /app/data

# Expose port for web interface (if we add one)
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting Mail Agent Container..."\n\
echo "📧 Available endpoints:"\n\
echo "  - Web Summarizer: python outlook_web_summarizer.py"\n\
echo "  - API Summarizer: python outlook_mail_summarizer.py"\n\
echo "  - Mac Summarizer: python outlook_mac_summarizer.py"\n\
echo ""\n\
echo "💡 To run a specific service:"\n\
echo "  docker exec -it <container_name> python outlook_web_summarizer.py"\n\
echo ""\n\
echo "🔧 Configuration:"\n\
echo "  - Edit config.py with your credentials"\n\
echo "  - Database will be stored in /app/data/"\n\
echo ""\n\
# Keep container running\n\
tail -f /dev/null\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"] 