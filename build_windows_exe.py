#!/usr/bin/env python3
"""
Windows-specific build script for creating MailAgent_Client.exe
Run this script on a Windows machine to create the executable.
"""

import os
import sys
import subprocess
import platform

def check_windows():
    """Ensure this is running on Windows"""
    if platform.system() != 'Windows':
        print("❌ This script must be run on Windows to create .exe files")
        print("💡 Use build_executable.py on other platforms")
        sys.exit(1)

def install_dependencies():
    """Install required dependencies for building"""
    print("📦 Installing build dependencies...")
    
    dependencies = [
        'pyinstaller',
        'playwright',
        'requests',
        'msal'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} already installed")
        except ImportError:
            print(f"📥 Installing {dep}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("🌐 Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install'])
        print("✅ Playwright browsers installed")
    except subprocess.CalledProcessError:
        print("⚠️  Playwright browser installation failed. Manual installation may be required.")

def create_hybrid_files():
    """Create the hybrid client files"""
    print("📝 Creating hybrid client files...")
    
    # Hybrid client main file
    client_code = '''#!/usr/bin/env python3
"""
Mail Agent Hybrid Client for Windows
Connects to remote Mail Agent host for database and LLM services
"""

import sys
import os
import requests
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess

# Configuration
DEFAULT_HOST = "192.168.1.100"  # User will change this
DEFAULT_PORT = "8080"

class MailAgentClient:
    def __init__(self):
        self.host = None
        self.port = None
        self.base_url = None
        
    def setup_connection(self):
        """Setup connection to host machine"""
        root = tk.Tk()
        root.title("Mail Agent Client Setup")
        root.geometry("400x200")
        root.eval('tk::PlaceWindow . center')
        
        # Create UI
        tk.Label(root, text="Mail Agent Client Setup", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Host input
        tk.Label(root, text="Host IP Address:").pack()
        host_entry = tk.Entry(root, width=30)
        host_entry.insert(0, DEFAULT_HOST)
        host_entry.pack(pady=5)
        
        # Port input
        tk.Label(root, text="Port:").pack()
        port_entry = tk.Entry(root, width=30)
        port_entry.insert(0, DEFAULT_PORT)
        port_entry.pack(pady=5)
        
        # Connection result
        result = {'success': False}
        
        def test_connection():
            self.host = host_entry.get().strip()
            self.port = port_entry.get().strip()
            
            if not self.host:
                messagebox.showerror("Error", "Host IP is required!")
                return
                
            if not self.port:
                self.port = DEFAULT_PORT
                
            self.base_url = f"http://{self.host}:{self.port}"
            
            # Test connection
            try:
                response = requests.get(f"{self.base_url}/api/status", timeout=5)
                if response.status_code == 200:
                    result['success'] = True
                    messagebox.showinfo("Success", f"✅ Connected to Mail Agent host!\\n{self.base_url}")
                    root.destroy()
                else:
                    messagebox.showerror("Connection Error", f"Invalid response from {self.base_url}")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Cannot connect to {self.base_url}\\n\\nError: {str(e)}\\n\\nMake sure the host is running:\\npython web_interface.py --host 0.0.0.0")
        
        tk.Button(root, text="Connect", command=test_connection, bg='#007AFF', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
        
        root.mainloop()
        
        if not result['success']:
            sys.exit(1)
    
    def run_email_processing(self):
        """Run the email processing with remote services"""
        try:
            # Show processing dialog
            processing_window = tk.Tk()
            processing_window.title("Processing Emails")
            processing_window.geometry("400x150")
            processing_window.eval('tk::PlaceWindow . center')
            
            tk.Label(processing_window, text="Processing your emails...", font=('Arial', 12)).pack(pady=20)
            tk.Label(processing_window, text="This may take a few minutes.", font=('Arial', 10)).pack()
            
            progress_label = tk.Label(processing_window, text="Starting...", font=('Arial', 10))
            progress_label.pack(pady=10)
            
            processing_window.update()
            
            # Import and run the email processing
            progress_label.config(text="Connecting to Outlook...")
            processing_window.update()
            
            from outlook_web_summarizer_hybrid import main as process_emails
            
            progress_label.config(text="Processing emails...")
            processing_window.update()
            
            # Process emails and send results to host
            results = process_emails(self.base_url)
            
            processing_window.destroy()
            
            # Show results
            result_window = tk.Tk()
            result_window.title("Processing Complete")
            result_window.geometry("450x200")
            result_window.eval('tk::PlaceWindow . center')
            
            tk.Label(result_window, text="✅ Email Processing Complete!", font=('Arial', 14, 'bold'), fg='green').pack(pady=10)
            tk.Label(result_window, text=f"Processed {results.get('count', 0)} emails", font=('Arial', 12)).pack()
            tk.Label(result_window, text=f"View results at: {self.base_url}", font=('Arial', 10)).pack(pady=5)
            
            def open_browser():
                import webbrowser
                webbrowser.open(self.base_url)
                result_window.destroy()
            
            tk.Button(result_window, text="Open Dashboard", command=open_browser, bg='#007AFF', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
            tk.Button(result_window, text="Close", command=result_window.destroy, font=('Arial', 10)).pack()
            
            result_window.mainloop()
            
        except Exception as e:
            # Show error dialog
            error_window = tk.Tk()
            error_window.title("Error")
            error_window.geometry("450x200")
            error_window.eval('tk::PlaceWindow . center')
            
            tk.Label(error_window, text="❌ Processing Failed", font=('Arial', 14, 'bold'), fg='red').pack(pady=10)
            tk.Label(error_window, text=str(e)[:100] + "..." if len(str(e)) > 100 else str(e), font=('Arial', 10)).pack(pady=5)
            tk.Button(error_window, text="Close", command=error_window.destroy, font=('Arial', 10)).pack(pady=10)
            
            error_window.mainloop()

def main():
    """Main application entry point"""
    print("🚀 Mail Agent Client Starting...")
    
    client = MailAgentClient()
    client.setup_connection()
    client.run_email_processing()
    
    print("✅ Mail Agent Client finished")

if __name__ == "__main__":
    main()
'''
    
    with open('outlook_hybrid_client_windows.py', 'w') as f:
        f.write(client_code)
    
    print("✅ Hybrid client files created")

def build_exe():
    """Build the Windows executable"""
    print("🔨 Building Windows executable...")
    
    import PyInstaller.__main__
    
    # Build arguments
    build_args = [
        'outlook_hybrid_client_windows.py',
        '--onefile',
        '--windowed',
        '--name=MailAgent_Client',
        '--hidden-import=playwright',
        '--hidden-import=playwright.sync_api',
        '--hidden-import=sqlite3',
        '--hidden-import=requests',
        '--hidden-import=msal',
        '--hidden-import=tkinter',
        '--hidden-import=webbrowser',
        '--collect-all=playwright',
        '--add-data=outlook_web_summarizer_hybrid.py;.',
        '--clean',
        '--noconfirm'
    ]
    
    # Add icon if available
    if os.path.exists('mail_icon.ico'):
        build_args.append('--icon=mail_icon.ico')
    
    # Add version info if available
    if os.path.exists('version_info.txt'):
        build_args.append('--version-file=version_info.txt')
    
    try:
        PyInstaller.__main__.run(build_args)
        print("✅ Windows executable built successfully!")
        print("📦 Location: dist\\MailAgent_Client.exe")
        print("📋 File size:", os.path.getsize('dist/MailAgent_Client.exe') // (1024*1024), "MB")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False
    
    return True

def create_version_info():
    """Create version info for the executable"""
    version_info = '''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
# filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
# Set not needed items to zero 0.
filevers=(1,0,0,0),
prodvers=(1,0,0,0),
# Contains a bitmask that specifies the valid bits 'flags'r
mask=0x3f,
# Contains a bitmask that specifies the Boolean attributes of the file.
flags=0x0,
# The operating system for which this file was designed.
# 0x4 - NT and there is no need to change it.
OS=0x4,
# The general type of file.
# 0x1 - the file is an application.
fileType=0x1,
# The function of the file.
# 0x0 - the function is not defined for this fileType
subtype=0x0,
# Creation date and time stamp.
date=(0, 0)
),
  kids=[
StringFileInfo(
  [
  StringTable(
    u'040904B0',
    [StringStruct(u'CompanyName', u'Mail Agent'),
    StringStruct(u'FileDescription', u'Mail Agent Hybrid Client'),
    StringStruct(u'FileVersion', u'1.0.0.0'),
    StringStruct(u'InternalName', u'MailAgent_Client'),
    StringStruct(u'LegalCopyright', u'Copyright (c) 2025'),
    StringStruct(u'OriginalFilename', u'MailAgent_Client.exe'),
    StringStruct(u'ProductName', u'Mail Agent Hybrid Client'),
    StringStruct(u'ProductVersion', u'1.0.0.0')])
  ]), 
VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''
    
    with open('version_info.txt', 'w') as f:
        f.write(version_info)

def main():
    """Main build process"""
    print("🚀 Mail Agent Windows .exe Builder")
    print("=" * 50)
    
    try:
        # Check if running on Windows
        check_windows()
        
        # Install dependencies
        install_dependencies()
        
        # Install Playwright browsers
        install_playwright_browsers()
        
        # Create version info
        create_version_info()
        
        # Create hybrid client files
        create_hybrid_files()
        
        # Build the executable
        success = build_exe()
        
        if success:
            print("\\n" + "=" * 50)
            print("✅ BUILD SUCCESSFUL!")
            print("📦 Your .exe file is ready: dist\\MailAgent_Client.exe")
            print("\\n📋 Next steps:")
            print("1. Test the .exe on your Windows machine")
            print("2. Share with other Windows users")
            print("3. Provide them your host IP address")
            print("\\n🔧 Host setup reminder:")
            print("Run on your host machine: python web_interface.py --host 0.0.0.0")
        else:
            print("\\n❌ Build failed. Check the error messages above.")
            
    except KeyboardInterrupt:
        print("\\n❌ Build cancelled by user")
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 