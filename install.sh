#!/bin/bash

# Mail Agent Automated Installer
# This script sets up the Mail Agent with zero manual configuration

set -e  # Exit on any error

echo "🚀 Mail Agent Automated Installer"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
fi

print_info "Detected OS: $OS"

# Check for required tools
check_requirements() {
    print_info "Checking system requirements..."
    
    # Check for Docker
    if command -v docker &> /dev/null; then
        print_status "Docker found"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not found - will install alternative method"
        DOCKER_AVAILABLE=false
    fi
    
    # Check for Python
    if command -v python3 &> /dev/null; then
        print_status "Python 3 found"
        PYTHON_AVAILABLE=true
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
        if [[ ${PYTHON_VERSION%%.*} -ge 3 ]]; then
            print_status "Python 3 found"
            PYTHON_AVAILABLE=true
        else
            print_warning "Python 2 found, but Python 3 required"
            PYTHON_AVAILABLE=false
        fi
    else
        print_warning "Python not found - will install"
        PYTHON_AVAILABLE=false
    fi
    
    # Check for curl/wget
    if command -v curl &> /dev/null; then
        DOWNLOAD_CMD="curl -fsSL"
        print_status "curl found"
    elif command -v wget &> /dev/null; then
        DOWNLOAD_CMD="wget -qO-"
        print_status "wget found"
    else
        print_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi
}

# Install Docker if not present
install_docker() {
    if [[ $DOCKER_AVAILABLE == false ]]; then
        print_info "Installing Docker..."
        
        case $OS in
            "linux")
                $DOWNLOAD_CMD https://get.docker.com | sh
                sudo usermod -aG docker $USER
                print_warning "Please log out and log back in for Docker permissions to take effect"
                ;;
            "mac")
                print_info "Please install Docker Desktop from: https://docker.com/products/docker-desktop"
                print_warning "Manual installation required for macOS"
                ;;
            "windows")
                print_info "Please install Docker Desktop from: https://docker.com/products/docker-desktop"
                print_warning "Manual installation required for Windows"
                ;;
        esac
    fi
}

# Install Python if not present
install_python() {
    if [[ $PYTHON_AVAILABLE == false ]]; then
        print_info "Installing Python..."
        
        case $OS in
            "linux")
                if command -v apt &> /dev/null; then
                    sudo apt update && sudo apt install -y python3 python3-pip
                elif command -v yum &> /dev/null; then
                    sudo yum install -y python3 python3-pip
                elif command -v dnf &> /dev/null; then
                    sudo dnf install -y python3 python3-pip
                else
                    print_error "Package manager not found. Please install Python 3 manually."
                    exit 1
                fi
                ;;
            "mac")
                if command -v brew &> /dev/null; then
                    brew install python3
                else
                    print_info "Please install Python from: https://python.org/downloads/"
                    print_warning "Manual installation required"
                fi
                ;;
            "windows")
                print_info "Please install Python from: https://python.org/downloads/"
                print_warning "Manual installation required for Windows"
                ;;
        esac
    fi
}

# Install Ollama
install_ollama() {
    print_info "Installing Ollama for AI features..."
    
    if command -v ollama &> /dev/null; then
        print_status "Ollama already installed"
    else
        case $OS in
            "linux"|"mac")
                $DOWNLOAD_CMD https://ollama.ai/install.sh | sh
                ;;
            "windows")
                print_info "Please install Ollama from: https://ollama.ai"
                print_warning "Manual installation required for Windows"
                ;;
        esac
    fi
    
    # Start Ollama and pull model
    print_info "Starting Ollama and downloading AI model..."
    if command -v ollama &> /dev/null; then
        # Start ollama in background
        ollama serve &
        sleep 5
        
        # Pull the model
        ollama pull llama3
        print_status "AI model downloaded"
    fi
}

# Setup Mail Agent
setup_mailagent() {
    print_info "Setting up Mail Agent..."
    
    # Create directory
    INSTALL_DIR="$HOME/MailAgent"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Download/copy files (assuming they're in current directory)
    if [[ -f "../requirements.txt" ]]; then
        cp ../*.py .
        cp ../requirements.txt .
        cp ../Dockerfile .
        cp ../docker-compose.yml .
        print_status "Files copied from source directory"
    else
        print_info "Downloading Mail Agent files..."
        # In a real scenario, you'd download from GitHub releases
        print_warning "Please ensure Mail Agent files are in the current directory"
    fi
    
    # Create configuration
    if [[ ! -f "config.py" ]]; then
        cat > config.py << 'EOL'
# Mail Agent Configuration
# Please update these values with your actual credentials

# For Graph API version (outlook_mail_summarizer)
CLIENT_ID = 'your_client_id_here'
TENANT_ID = 'your_tenant_id_here'
CLIENT_SECRET = 'your_client_secret_here'
SUBJECT_TO_SEARCH = 'your_subject_here'

# For Ollama integration
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3'

# For web version search criteria
SEARCH_QUERY = 'subject:"Letter Of Authorization" from:"Harshit Amar"'
REQUIRED_SENDER_NAME = "Harshit Amar"
REQUIRED_SENDER_EMAIL = "Harshit.Amar@ril.com"
EOL
        print_status "Configuration template created"
        print_warning "Please edit config.py with your actual credentials"
    fi
    
    # Install Python dependencies if Python is available
    if [[ $PYTHON_AVAILABLE == true ]] || command -v python3 &> /dev/null; then
        print_info "Installing Python dependencies..."
        python3 -m pip install -r requirements.txt
        print_status "Dependencies installed"
    fi
    
    # Create startup scripts
    cat > start_mailagent.sh << 'EOL'
#!/bin/bash
echo "🚀 Starting Mail Agent..."

# Check if Docker is available and docker-compose.yml exists
if command -v docker &> /dev/null && [[ -f docker-compose.yml ]]; then
    echo "📦 Starting with Docker..."
    docker-compose up -d
    echo "✓ Mail Agent started with Docker"
    echo "🌐 Access web interface at: http://localhost:8080"
elif command -v python3 &> /dev/null; then
    echo "🐍 Starting with Python..."
    python3 web_interface.py &
    echo "✓ Mail Agent started with Python"
    echo "🌐 Access web interface at: http://localhost:8080"
else
    echo "❌ Neither Docker nor Python 3 found"
    echo "Please install Docker or Python 3"
    exit 1
fi
EOL
    
    chmod +x start_mailagent.sh
    print_status "Startup script created"
    
    # Create desktop shortcut (Linux/Mac)
    create_shortcuts
}

# Create desktop shortcuts
create_shortcuts() {
    case $OS in
        "linux")
            DESKTOP_FILE="$HOME/Desktop/MailAgent.desktop"
            cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Name=Mail Agent
Comment=AI-powered email processing agent
Exec=$INSTALL_DIR/start_mailagent.sh
Icon=mail
Terminal=false
Type=Application
Categories=Office;Email;
EOL
            chmod +x "$DESKTOP_FILE"
            print_status "Desktop shortcut created"
            ;;
        "mac")
            # Create a simple app bundle
            APP_DIR="$HOME/Desktop/MailAgent.app"
            mkdir -p "$APP_DIR/Contents/MacOS"
            
            cat > "$APP_DIR/Contents/MacOS/MailAgent" << EOL
#!/bin/bash
cd "$INSTALL_DIR"
./start_mailagent.sh
EOL
            chmod +x "$APP_DIR/Contents/MacOS/MailAgent"
            
            cat > "$APP_DIR/Contents/Info.plist" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>MailAgent</string>
    <key>CFBundleExecutable</key>
    <string>MailAgent</string>
</dict>
</plist>
EOL
            print_status "Mac app bundle created"
            ;;
    esac
}

# Main installation flow
main() {
    echo
    print_info "Starting automated installation..."
    
    # Check system requirements
    check_requirements
    
    # Ask user which method they prefer
    echo
    echo "Choose installation method:"
    echo "1) Docker (Recommended - fully isolated)"
    echo "2) Python (Direct installation)"
    echo "3) Both (Maximum compatibility)"
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            install_docker
            ;;
        2)
            install_python
            ;;
        3)
            install_docker
            install_python
            ;;
        *)
            print_error "Invalid choice. Defaulting to Docker installation."
            install_docker
            ;;
    esac
    
    # Install Ollama for AI features
    echo
    read -p "Install Ollama for AI email summarization? (y/N): " install_ai
    if [[ $install_ai =~ ^[Yy]$ ]]; then
        install_ollama
    fi
    
    # Setup Mail Agent
    setup_mailagent
    
    # Final instructions
    echo
    echo "🎉 Installation Complete!"
    echo "========================"
    echo
    print_status "Mail Agent installed to: $INSTALL_DIR"
    print_info "Next steps:"
    echo "  1. Edit $INSTALL_DIR/config.py with your email credentials"
    echo "  2. Run: cd $INSTALL_DIR && ./start_mailagent.sh"
    echo "  3. Open browser to: http://localhost:8080"
    echo
    print_info "Quick start:"
    echo "  cd $INSTALL_DIR"
    echo "  ./start_mailagent.sh"
    echo
    print_warning "Don't forget to configure your credentials in config.py!"
}

# Run main function
main "$@" 