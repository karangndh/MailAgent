# Mail Agent - Plug and Play Deployment Guide

This guide provides multiple ways to deploy the Mail Agent as a plug-and-play service that can run on computers without Python or dependencies pre-installed.

## 🚀 Deployment Options

### 1. **Standalone Executables** (Easiest for Desktop Users)

Create self-contained executables that include Python and all dependencies.

#### Build Process:
```bash
# Run the build script
python build_executable.py
```

#### What you get:
- `MailAgent_Web.exe` (Windows) / `MailAgent_Web` (Mac/Linux) - Web-based interface
- `MailAgent_API.exe` (Windows) / `MailAgent_API` (Mac/Linux) - Graph API version
- `MailAgent_Mac` (macOS only) - AppleScript version for Mac Outlook
- `launch_mailagent.sh` - Simple launcher script
- `config_template.py` - Configuration template

#### Distribution:
1. Copy the `dist/` folder to target computer
2. Copy `config_template.py` to `config.py` and fill in credentials
3. Install Ollama on target machine (optional, for summarization)
4. Run `./launch_mailagent.sh` or execute the specific version directly

---

### 2. **Docker Containerization** (Best for Servers)

Run everything in isolated containers with zero host dependencies.

#### Quick Start:
```bash
# Clone the repository
git clone <your-repo-url>
cd MailAgent

# Copy and configure
cp config_template.py config.py
# Edit config.py with your credentials

# Start with Docker Compose (includes Ollama)
docker-compose up -d

# Access web interface
open http://localhost:8080
```

#### What's included:
- ✅ Python environment
- ✅ All dependencies pre-installed
- ✅ Ollama LLM server (automatic model download)
- ✅ Web interface accessible via browser
- ✅ Persistent data storage
- ✅ Automatic restarts

#### Manual Docker Commands:
```bash
# Build the image
docker build -t mailagent .

# Run with volume mounts
docker run -d \
  --name mailagent \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config.py:/app/config.py \
  mailagent
```

---

### 3. **Web Service Interface** (Browser-Based)

Access via web browser - no installation needed on client machines.

#### Features:
- 📊 **Dashboard**: View email processing status and results
- ⚙️ **Configuration**: Edit settings via web interface
- 🔍 **Web Search**: Trigger email searches with one click
- 📧 **Email Management**: View processed emails in table format
- 🤖 **AI Integration**: Built-in Ollama status monitoring

#### Access:
- Main Dashboard: `http://localhost:8080`
- Configuration: `http://localhost:8080/config`

#### API Endpoints:
- `GET /api/status` - System status
- `GET /api/emails` - List processed emails
- `POST /api/run_web_search` - Trigger email search
- `POST /api/summarize` - Summarize text with AI

---

### 4. **Cloud Deployment** (AWS/GCP/Azure)

#### Option A: Container-based Cloud Deployment
```bash
# Push to container registry
docker tag mailagent your-registry/mailagent:latest
docker push your-registry/mailagent:latest

# Deploy to cloud (example: AWS ECS, Google Cloud Run, Azure Container Instances)
```

#### Option B: Serverless Functions
- Convert core functions to AWS Lambda/Azure Functions
- Use managed databases (RDS/Cloud SQL)
- Trigger via API Gateway/HTTP triggers

---

## 🔧 Configuration

### Environment Setup

#### For Graph API (outlook_mail_summarizer.py):
```python
CLIENT_ID = 'your_azure_app_client_id'
TENANT_ID = 'your_azure_tenant_id'
CLIENT_SECRET = 'your_azure_app_secret'
SUBJECT_TO_SEARCH = 'subject_to_search_for'
```

#### For Web Version (outlook_web_summarizer.py):
```python
SEARCH_QUERY = 'subject:"Letter Of Authorization" from:"Harshit Amar"'
REQUIRED_SENDER_NAME = "Harshit Amar"
REQUIRED_SENDER_EMAIL = "Harshit.Amar@ril.com"
```

#### For Ollama Integration:
```python
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3'
```

---

## 📋 Prerequisites for Target Machines

### Minimal Requirements:
- **Executables**: None (completely self-contained)
- **Docker**: Docker installed (or Docker Desktop)
- **Web Service**: Any modern web browser

### Optional Components:
- **Ollama**: For AI-powered email summarization
  - Download: https://ollama.ai
  - Models: `ollama pull llama3`

---

## 🎯 Quick Start Guide for End Users

### Method 1: One-Click Docker (Recommended)
```bash
# Download and start (everything included)
curl -O https://raw.githubusercontent.com/your-repo/docker-compose.yml
docker-compose up -d

# Open browser
open http://localhost:8080
```

### Method 2: Download Executable
1. Download `MailAgent-v1.0.zip` from releases
2. Extract to any folder
3. Edit `config.py` with your email credentials
4. Double-click `MailAgent_Web.exe` (Windows) or `./MailAgent_Web` (Mac/Linux)
5. Open browser to `http://localhost:8080`

### Method 3: Cloud Access
Simply navigate to your deployed cloud URL - no installation required.

---

## 🔒 Security Considerations

### Credentials Management:
- Store sensitive credentials in environment variables
- Use Azure Key Vault / AWS Secrets Manager for production
- Never commit credentials to version control

### Network Security:
- Use HTTPS in production deployments
- Implement authentication for web interface
- Configure firewall rules appropriately

### Data Privacy:
- Email data stored locally in SQLite database
- No data transmitted to external services (except Ollama for summarization)
- Regular database backups recommended

---

## 🐛 Troubleshooting

### Common Issues:

#### "Ollama not detected"
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull required model
ollama pull llama3
```

#### "Database not found"
- Web interface automatically creates database
- For manual setup: `python outlook_web_summarizer.py` (creates database)

#### "Playwright browser not found"
```bash
# Install browsers
playwright install chromium
```

#### "Authentication failed"
- Verify Azure app registration
- Check tenant ID and client credentials
- Ensure correct permissions granted

### Log Files:
- Docker: `docker logs mailagent`
- Executable: Check console output
- Web interface: Browser developer tools

---

## 📊 Monitoring and Maintenance

### Health Checks:
- Database status: `http://localhost:8080/api/status`
- Ollama status: `curl http://localhost:11434/api/version`
- Email processing: Check `/api/emails` endpoint

### Backup Strategy:
```bash
# Backup database
cp data/email_assistants.db backups/email_assistants_$(date +%Y%m%d).db

# Backup configuration
cp config.py backups/config_$(date +%Y%m%d).py
```

### Updates:
- Executables: Download new release and replace files
- Docker: `docker-compose pull && docker-compose up -d`
- Source: `git pull && docker-compose build`

---

## 🚀 Advanced Deployment

### Load Balancer Setup:
```nginx
# nginx.conf
upstream mailagent {
    server localhost:8080;
    server localhost:8081;  # Scale horizontally
}

server {
    listen 80;
    location / {
        proxy_pass http://mailagent;
    }
}
```

### Environment Variables:
```bash
# .env file for docker-compose
MAILAGENT_CLIENT_ID=your_client_id
MAILAGENT_TENANT_ID=your_tenant_id
MAILAGENT_CLIENT_SECRET=your_secret
OLLAMA_MODEL=llama3
DATABASE_PATH=/app/data/email_assistants.db
```

### Scaling:
- Horizontal: Run multiple container instances
- Vertical: Increase container resources
- Database: Use external PostgreSQL/MySQL for multi-instance deployments

---

## 📞 Support

### Documentation:
- API Documentation: `/api/docs` (if Swagger enabled)
- Configuration Guide: This README
- Troubleshooting: See above section

### Community:
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: [your-support-email]

---

*This deployment guide ensures your Mail Agent can run on any computer without requiring Python installation or complex dependency management.* 