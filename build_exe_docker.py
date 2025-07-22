#!/usr/bin/env python3
"""
Build Windows .exe using Docker (works on macOS/Linux)
Alternative to GitHub Actions for immediate .exe creation
"""

import os
import subprocess
import sys
import platform

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker found: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker daemon is running")
                return True
            else:
                print("❌ Docker daemon not running. Please start Docker Desktop.")
                return False
        else:
            print("❌ Docker not found")
            return False
    except FileNotFoundError:
        print("❌ Docker not installed")
        return False

def create_dockerfile():
    """Create Dockerfile for Windows build environment"""
    dockerfile_content = '''# Use Windows Server Core with Python
FROM python:3.11-windowsservercore

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir pyinstaller playwright requests msal

# Install Playwright browsers
RUN python -m playwright install chromium

# Copy source files
COPY . .

# Create hybrid files and build
RUN python -c "import build_windows_exe; build_windows_exe.create_hybrid_files(); build_windows_exe.create_version_info()"

# Build the executable
RUN pyinstaller outlook_hybrid_client_windows.py ^
    --onefile ^
    --windowed ^
    --name=MailAgent_Client ^
    --hidden-import=playwright ^
    --hidden-import=playwright.sync_api ^
    --hidden-import=sqlite3 ^
    --hidden-import=requests ^
    --hidden-import=msal ^
    --hidden-import=tkinter ^
    --hidden-import=webbrowser ^
    --collect-all=playwright ^
    --add-data="outlook_web_summarizer_hybrid.py;." ^
    --clean ^
    --noconfirm

# Create release package
RUN mkdir release_package && ^
    copy dist\\MailAgent_Client.exe release_package\\ && ^
    copy README_USER.txt release_package\\ && ^
    echo 100.0.255.3 > release_package\\host_ip.txt

# Default command
CMD ["cmd"]
'''

    with open('Dockerfile.windows', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Dockerfile.windows created")

def create_docker_compose():
    """Create docker-compose for easier building"""
    compose_content = '''version: '3.8'

services:
  windows-builder:
    build:
      context: .
      dockerfile: Dockerfile.windows
    platform: windows/amd64
    volumes:
      - ./dist:/app/release_package
    command: >
      cmd /c "echo Build completed && 
              dir release_package &&
              echo Ready to copy files"
'''

    with open('docker-compose.windows.yml', 'w') as f:
        f.write(compose_content)
    
    print("✅ docker-compose.windows.yml created")

def build_with_docker():
    """Build using Docker"""
    print("🔨 Building Windows .exe with Docker...")
    
    try:
        # Build the Docker image
        print("📦 Building Docker image...")
        result = subprocess.run([
            'docker', 'build', 
            '-f', 'Dockerfile.windows',
            '-t', 'mailagent-windows-builder',
            '.'
        ], check=True)
        
        print("✅ Docker image built successfully")
        
        # Run the container to build the .exe
        print("🚀 Running build container...")
        os.makedirs('dist', exist_ok=True)
        
        result = subprocess.run([
            'docker', 'run', '--rm',
            '-v', f'{os.getcwd()}/dist:/app/release_package',
            'mailagent-windows-builder',
            'cmd', '/c', 
            'copy release_package\\* C:\\app\\release_package\\ && echo Build completed'
        ], check=True)
        
        print("✅ Build completed")
        
        # Check if files were created
        exe_path = os.path.join('dist', 'MailAgent_Client.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"✅ MailAgent_Client.exe created!")
            print(f"📦 Size: {size_mb:.1f} MB")
            print(f"📁 Location: {exe_path}")
            return True
        else:
            print("❌ .exe file not found in dist/")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
        return False

def build_with_wine():
    """Alternative: Build using Wine (Windows emulator)"""
    print("🍷 Attempting build with Wine...")
    
    # Check if Wine is available
    try:
        result = subprocess.run(['wine', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Wine not installed")
            return False
            
        print(f"✅ Wine found: {result.stdout.strip()}")
        
        # Install Windows Python in Wine
        print("📦 This method requires manual Wine setup...")
        print("💡 Use Docker method instead for automated build")
        return False
        
    except FileNotFoundError:
        print("❌ Wine not available")
        return False

def main():
    """Main build function"""
    print("🚀 Docker Windows .exe Builder")
    print("=" * 50)
    
    # Check platform
    if platform.system() == 'Windows':
        print("✅ Running on Windows - can build directly")
        print("💡 Run: python build_windows_exe.py")
        return
    
    print(f"📱 Running on {platform.system()}")
    print("🔄 Using cross-compilation approach...")
    
    # Method 1: Docker (recommended)
    if check_docker():
        print("\n🐳 Using Docker method...")
        create_dockerfile()
        
        choice = input("\nProceed with Docker build? (y/N): ").strip().lower()
        if choice == 'y':
            success = build_with_docker()
            if success:
                print("\n" + "=" * 50)
                print("✅ BUILD SUCCESSFUL!")
                print("=" * 50)
                print("\n📦 Your files are ready:")
                print("  • dist/MailAgent_Client.exe")
                print("  • dist/README_USER.txt") 
                print("  • dist/host_ip.txt")
                print("\n🎯 Share these files with Windows users!")
                return
        else:
            print("❌ Build cancelled")
    
    # Method 2: GitHub Actions (fallback)
    print("\n🌐 Alternative: GitHub Actions")
    print("💡 Run: python trigger_build.py")
    print("   This will build the .exe in the cloud")
    
    # Method 3: Manual instructions
    print("\n📋 Manual method:")
    print("1. Copy files to a Windows machine")
    print("2. Run: python build_windows_exe.py")
    print("3. Get dist/MailAgent_Client.exe")

if __name__ == "__main__":
    main() 