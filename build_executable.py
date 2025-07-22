#!/usr/bin/env python3
"""
Build script to create standalone executables for the Mail Agent
"""
import os
import sys
import subprocess
import platform
import PyInstaller.__main__
import requests
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog

def install_build_dependencies():
    """Install PyInstaller and other build dependencies"""
    print("Installing build dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "auto-py-to-exe"])

def create_executable(script_name, app_name):
    """Create standalone executable for a given script"""
    print(f"Creating executable for {script_name}...")
    
    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable file
        "--windowed" if "web" in script_name else "--console",  # GUI vs CLI
        "--add-data", "email_assistants.db;." if os.path.exists("email_assistants.db") else "",
        "--hidden-import", "sqlite3",
        "--hidden-import", "playwright.sync_api",
        "--hidden-import", "msal",
        "--name", app_name,
        script_name
    ]
    
    # Remove empty strings
    cmd = [arg for arg in cmd if arg]
    
    try:
        subprocess.check_call(cmd)
        print(f"✓ Successfully created {app_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating {app_name}: {e}")

def post_build_setup():
    """Create additional files needed for distribution"""
    # Create a simple launcher script
    launcher_content = """#!/bin/bash
# Mail Agent Launcher
echo "Starting Mail Agent..."

# Check if Ollama is running (for summarization features)
if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "Warning: Ollama not detected. Summarization features may not work."
    echo "Please install Ollama from https://ollama.ai"
fi

# Launch the appropriate version based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    ./MailAgent_Mac
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    ./MailAgent_Web
else
    ./MailAgent_Web.exe
fi
"""
    
    with open("launch_mailagent.sh", "w") as f:
        f.write(launcher_content)
    
    os.chmod("launch_mailagent.sh", 0o755)
    
    # Create configuration template
    config_template = """# Mail Agent Configuration
# Copy this file to config.py and fill in your details

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
"""
    
    with open("config_template.py", "w") as f:
        f.write(config_template)

def build_hybrid_executable():
    """Build a hybrid executable that connects to remote services"""
    
    # Create a hybrid version of the outlook summarizer
    create_hybrid_outlook_script()
    
    # Build the executable
    build_args = [
        'outlook_hybrid_client.py',
        '--onefile',
        '--windowed',
        '--name=MailAgent_Client',
        '--hidden-import=playwright',
        '--hidden-import=sqlite3',
        '--hidden-import=requests',
        '--hidden-import=msal',
        '--hidden-import=tkinter',
        '--collect-all=playwright',
        '--clean'
    ]
    
    # Add icon if available
    if os.path.exists('mail_icon.ico'):
        build_args.append('--icon=mail_icon.ico')
    
    PyInstaller.__main__.run(build_args)
    
    print("✅ Hybrid executable built successfully!")
    print("📦 Location: dist/MailAgent_Client.exe")
    print("\n🔧 Setup required on host machine:")
    print("1. Run: python web_interface.py --host 0.0.0.0")
    print("2. Ensure database is accessible")
    print("3. Share the .exe file with users")

def create_hybrid_outlook_script():
    """Create a hybrid script that connects to remote services"""
    
    hybrid_script = '''#!/usr/bin/env python3
"""
Hybrid Mail Agent Client
Connects to remote database and LLM while processing local Outlook emails
"""

import sys
import os
import requests
import json
from datetime import datetime
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog

# Configuration
DEFAULT_HOST = "YOUR_HOST_IP"  # User will be prompted to enter this
DEFAULT_PORT = "8080"

class MailAgentClient:
    def __init__(self):
        self.host = None
        self.port = None
        self.base_url = None
        
    def setup_connection(self):
        """Setup connection to host machine"""
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Get host information from user
        self.host = simpledialog.askstring(
            "Mail Agent Setup", 
            "Enter the host machine IP address:",
            initialvalue=DEFAULT_HOST
        )
        
        if not self.host:
            messagebox.showerror("Error", "Host IP is required!")
            sys.exit(1)
            
        self.port = simpledialog.askstring(
            "Mail Agent Setup", 
            "Enter the port number:",
            initialvalue=DEFAULT_PORT
        )
        
        if not self.port:
            self.port = DEFAULT_PORT
            
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Test connection
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Success", "Connected to Mail Agent host!")
            else:
                raise Exception("Invalid response")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect to {self.base_url}\\nError: {str(e)}")
            sys.exit(1)
            
        root.destroy()
    
    def run_email_processing(self):
        """Run the email processing with remote services"""
        try:
            # Import and modify the outlook summarizer to use remote services
            from outlook_web_summarizer_hybrid import main as process_emails
            
            # Process emails and send results to host
            results = process_emails(self.base_url)
            
            # Show results to user
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "Processing Complete", 
                f"Processed {results.get('count', 0)} emails\\n"
                f"View results at: {self.base_url}"
            )
            root.destroy()
            
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error", f"Email processing failed:\\n{str(e)}")
            root.destroy()

def main():
    client = MailAgentClient()
    client.setup_connection()
    client.run_email_processing()

if __name__ == "__main__":
    main()
'''
    
    with open('outlook_hybrid_client.py', 'w') as f:
        f.write(hybrid_script)
    
    # Create hybrid version of outlook summarizer
    create_hybrid_summarizer()

def create_hybrid_summarizer():
    """Create a version of outlook_web_summarizer that sends data to remote host"""
    
    hybrid_summarizer = '''#!/usr/bin/env python3
"""
Hybrid Outlook Web Summarizer
Processes local emails but sends results to remote database and uses remote LLM
"""

import sys
import time
from playwright.sync_api import sync_playwright
import os
import re
import requests
import json
from datetime import datetime

SESSION_FILE = 'outlook_web_session.json'
OUTLOOK_URL = 'https://outlook.office.com/mail/inbox'

# Search criteria
SEARCH_QUERY = 'subject:"Letter Of Authorization" from:"Harshit Amar" from:Harshit.Amar@ril.com'
REQUIRED_SENDER_NAME = "Harshit Amar"
REQUIRED_SENDER_EMAIL = "Harshit.Amar@ril.com"

def send_to_remote_database(email_data, base_url):
    """Send extracted email data to remote database"""
    try:
        response = requests.post(
            f"{base_url}/api/save_email",
            json=email_data,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to save to remote database: {response.text}")
            return {"success": False, "error": response.text}
    except Exception as e:
        print(f"❌ Error connecting to remote database: {e}")
        return {"success": False, "error": str(e)}

def summarize_with_remote_ollama(text, base_url):
    """Summarize text using remote Ollama service"""
    try:
        response = requests.post(
            f"{base_url}/api/summarize",
            json={"text": text},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("summary", "")
        else:
            print(f"❌ Failed to summarize with remote Ollama: {response.text}")
            return ""
    except Exception as e:
        print(f"❌ Error connecting to remote Ollama: {e}")
        return ""

def main(base_url):
    """Main function that processes emails and sends results to remote services"""
    
    print(f"🔗 Using remote services at: {base_url}")
    print(f"Searching for emails using query: {SEARCH_QUERY}")
    
    processed_count = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = None
        if os.path.exists(SESSION_FILE):
            context = browser.new_context(storage_state=SESSION_FILE)
        else:
            context = browser.new_context()
        page = context.new_page()
        
        # Step 1: Open Outlook
        print("Opening Outlook...")
        page.goto(OUTLOOK_URL)
        if not os.path.exists(SESSION_FILE):
            print("Please log in to Outlook Web in the opened browser window. After your inbox loads, press Enter here to continue...")
            input()
            context.storage_state(path=SESSION_FILE)
        
        # Step 2: Search and process emails (using existing logic)
        # ... (include the email search and processing logic from outlook_web_summarizer.py)
        
        # Step 3: Send results to remote database
        print(f"\\n{'='*80}")
        print(f"SENDING RESULTS TO REMOTE DATABASE")
        print(f"{'='*80}")
        
        # For each processed email, send to remote database
        # This would include the actual email processing logic
        
        context.close()
        browser.close()
    
    print(f"\\n✅ Processing complete! Sent {processed_count} emails to remote database")
    return {"count": processed_count}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8080"
    
    main(base_url)
'''
    
    with open('outlook_web_summarizer_hybrid.py', 'w') as f:
        f.write(hybrid_summarizer)

def main():
    """Main build process"""
    print("🚀 Mail Agent Build System")
    print("\nSelect build type:")
    print("1. Full standalone executables (local setup)")
    print("2. Hybrid client executable (connects to remote services)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "2":
            print("\n🔄 Building hybrid client executable...")
            build_hybrid_executable()
        else:
            print("\n🔄 Building full standalone executables...")
            current_os = platform.system().lower()
            print(f"Building Mail Agent for {current_os}...")
            
            # Install dependencies
            install_build_dependencies()
            
            # Create executables for each version
            if current_os == "darwin":  # macOS
                create_executable("outlook_mac_summarizer.py", "MailAgent_Mac")
            
            create_executable("outlook_web_summarizer.py", "MailAgent_Web")
            create_executable("outlook_mail_summarizer.py", "MailAgent_API")
            
            # Create support files
            post_build_setup()
            
            print("\n✓ Build complete!")
            print("📁 Executables created in ./dist/ directory")
            print("📋 Next steps:")
            print("   1. Copy config_template.py to config.py and fill in your details")
            print("   2. Install Ollama on target machines for summarization features")
            print("   3. Run ./launch_mailagent.sh to start the application")
            
    except KeyboardInterrupt:
        print("\n❌ Build cancelled by user")
    except Exception as e:
        print(f"❌ Build failed: {e}")

if __name__ == "__main__":
    main() 