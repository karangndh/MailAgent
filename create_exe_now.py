#!/usr/bin/env python3
"""
Create Windows .exe file NOW - tries multiple methods
This is the main script to run for immediate .exe creation
"""

import os
import sys
import platform
import subprocess
import shutil
from datetime import datetime

def print_header():
    """Print header"""
    print("🚀 CREATE WINDOWS .EXE NOW")
    print("=" * 50)
    print(f"📱 Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📁 Directory: {os.getcwd()}")
    print("=" * 50)

def check_dependencies():
    """Check and install required dependencies"""
    print("📦 Checking dependencies...")
    
    required = ['pyinstaller', 'requests']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print(f"\n📥 Installing missing packages: {', '.join(missing)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            print("✅ Dependencies installed")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    
    return True

def create_hybrid_files():
    """Create the hybrid client files"""
    print("📝 Creating hybrid client files...")
    
    try:
        import build_windows_exe
        build_windows_exe.create_hybrid_files()
        build_windows_exe.create_version_info()
        print("✅ Hybrid files created")
        return True
    except Exception as e:
        print(f"❌ Failed to create hybrid files: {e}")
        return False

def method_1_direct_pyinstaller():
    """Method 1: Direct PyInstaller (may work with cross-compilation)"""
    print("\n🔨 Method 1: Direct PyInstaller Build")
    print("-" * 30)
    
    if not os.path.exists('outlook_hybrid_client_windows.py'):
        print("❌ Hybrid client file missing")
        return False
    
    try:
        # Import PyInstaller
        import PyInstaller.__main__
        
        print("🔧 Building with PyInstaller...")
        
        # Build arguments - attempt cross-compilation
        build_args = [
            'outlook_hybrid_client_windows.py',
            '--onefile',
            '--windowed',
            '--name=MailAgent_Client',
            '--hidden-import=requests',
            '--hidden-import=tkinter',
            '--hidden-import=webbrowser',
            '--add-data=outlook_web_summarizer_hybrid.py:.',
            '--clean',
            '--noconfirm',
            '--distpath=dist',
            '--workpath=build'
        ]
        
        # Add icon if available
        if os.path.exists('mail_icon.ico'):
            build_args.append('--icon=mail_icon.ico')
        
        # Run PyInstaller
        PyInstaller.__main__.run(build_args)
        
        # Check results
        if platform.system() == 'Windows':
            exe_path = 'dist/MailAgent_Client.exe'
        else:
            exe_path = 'dist/MailAgent_Client'  # Unix executable
        
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"✅ Executable created: {exe_path}")
            print(f"📦 Size: {size_mb:.1f} MB")
            
            if platform.system() != 'Windows':
                print("⚠️  Created Unix executable (not Windows .exe)")
                print("💡 Use GitHub Actions or Docker for Windows .exe")
                return False
            
            return True
        else:
            print("❌ Executable not found")
            return False
            
    except Exception as e:
        print(f"❌ PyInstaller build failed: {e}")
        return False

def method_2_github_actions():
    """Method 2: GitHub Actions (cloud build)"""
    print("\n🌐 Method 2: GitHub Actions Cloud Build")
    print("-" * 30)
    
    if not os.path.exists('.github/workflows/build-windows.yml'):
        print("❌ GitHub Actions workflow missing")
        print("💡 Run: python trigger_build.py")
        return False
    
    print("✅ GitHub Actions workflow available")
    print("💡 Run: python trigger_build.py")
    print("   This will build the .exe in the cloud")
    return False

def method_3_package_for_transfer():
    """Method 3: Create package for Windows machine"""
    print("\n📦 Method 3: Package for Windows Transfer")
    print("-" * 30)
    
    try:
        # Create transfer package
        package_dir = "windows_build_package"
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        
        os.makedirs(package_dir)
        
        # Copy necessary files
        files_to_copy = [
            'build_windows_exe.py',
            'outlook_web_summarizer_hybrid.py',
            'README_USER.txt',
            'requirements.txt'
        ]
        
        for file in files_to_copy:
            if os.path.exists(file):
                shutil.copy2(file, package_dir)
        
        # Create build instruction
        instructions = '''# BUILD INSTRUCTIONS FOR WINDOWS

## Quick Setup:
1. Install Python 3.8+ from python.org
2. Open Command Prompt as Administrator
3. Navigate to this folder
4. Run: python build_windows_exe.py

## What you'll get:
- dist/MailAgent_Client.exe (ready to share)
- Complete package with user instructions

## Files in this package:
- build_windows_exe.py (build script)
- outlook_web_summarizer_hybrid.py (client logic)
- README_USER.txt (user instructions)
- requirements.txt (dependencies)

## Support:
If build fails, check Python version and internet connection.
'''
        
        with open(f"{package_dir}/BUILD_ON_WINDOWS.md", 'w') as f:
            f.write(instructions)
        
        # Create ZIP if possible
        try:
            shutil.make_archive(package_dir, 'zip', package_dir)
            print(f"✅ Package created: {package_dir}.zip")
            print(f"📁 Transfer this to Windows machine and unzip")
            print(f"🔧 Run: python build_windows_exe.py")
            return True
        except:
            print(f"✅ Package created: {package_dir}/")
            print(f"📁 Transfer this folder to Windows machine")
            print(f"🔧 Run: python build_windows_exe.py")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create package: {e}")
        return False

def main():
    """Main function - try all methods"""
    print_header()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Cannot proceed without dependencies")
        return
    
    # Create hybrid files
    if not create_hybrid_files():
        print("❌ Cannot proceed without hybrid files")
        return
    
    # Try methods in order
    methods = [
        ("Direct PyInstaller", method_1_direct_pyinstaller),
        ("GitHub Actions", method_2_github_actions),
        ("Package for Transfer", method_3_package_for_transfer)
    ]
    
    success = False
    for name, method in methods:
        try:
            if method():
                success = True
                break
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            continue
    
    if success:
        print("\n" + "=" * 50)
        print("✅ SUCCESS!")
        print("=" * 50)
        
        if os.path.exists('dist/MailAgent_Client.exe'):
            print("🎯 Windows .exe ready to share!")
            print("📁 Location: dist/MailAgent_Client.exe")
            print("📋 Also share: README_USER.txt")
            print("🌐 Your host IP: 100.0.255.3:8080")
        elif os.path.exists('windows_build_package.zip'):
            print("📦 Transfer package ready!")
            print("📁 Send windows_build_package.zip to Windows user")
            print("🔧 They run: python build_windows_exe.py")
        
    else:
        print("\n" + "=" * 50)
        print("❌ ALL METHODS FAILED")
        print("=" * 50)
        print("💡 Try these alternatives:")
        print("1. python trigger_build.py (GitHub Actions)")
        print("2. Copy files to Windows machine manually")
        print("3. Use Docker: python build_exe_docker.py")

if __name__ == "__main__":
    main() 