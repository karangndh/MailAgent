#!/usr/bin/env python3
"""
Trigger Windows .exe build and provide download instructions
"""

import os
import subprocess
import sys
import webbrowser
from datetime import datetime

def check_git_setup():
    """Check if we're in a git repository and have GitHub setup"""
    try:
        # Check if we're in a git repo
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Not in a Git repository")
            return False
            
        # Check if we have a GitHub remote
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if 'github.com' not in result.stdout:
            print("❌ No GitHub remote found")
            return False
            
        print("✅ Git and GitHub setup detected")
        return True
        
    except FileNotFoundError:
        print("❌ Git not installed")
        return False

def get_github_repo():
    """Get the GitHub repository URL"""
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip()
            # Convert SSH to HTTPS for browser opening
            if url.startswith('git@github.com:'):
                url = url.replace('git@github.com:', 'https://github.com/')
            if url.endswith('.git'):
                url = url[:-4]
            return url
    except:
        pass
    return None

def commit_and_push():
    """Commit changes and push to trigger the build"""
    try:
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit with timestamp
        commit_msg = f"Build Windows executable - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # Push to trigger build
        subprocess.run(['git', 'push'], check=True)
        
        print("✅ Changes committed and pushed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False

def main():
    """Main function to trigger build"""
    print("🚀 Windows .exe Build Trigger")
    print("=" * 50)
    
    # Check prerequisites
    if not check_git_setup():
        print("\n📋 Setup required:")
        print("1. Initialize git: git init")
        print("2. Add GitHub remote: git remote add origin <your-repo-url>")
        print("3. Push code to GitHub")
        print("4. Run this script again")
        return
    
    # Get repository info
    repo_url = get_github_repo()
    if not repo_url:
        print("❌ Could not determine GitHub repository URL")
        return
    
    print(f"📁 Repository: {repo_url}")
    
    # Check if workflow file exists
    workflow_path = ".github/workflows/build-windows.yml"
    if not os.path.exists(workflow_path):
        print(f"❌ Workflow file missing: {workflow_path}")
        return
    
    print("✅ GitHub Actions workflow found")
    
    # Commit and push changes
    print("\n🔄 Committing and pushing changes...")
    if not commit_and_push():
        return
    
    # Provide instructions
    print("\n" + "=" * 50)
    print("✅ BUILD TRIGGERED!")
    print("=" * 50)
    
    actions_url = f"{repo_url}/actions"
    
    print(f"\n📋 Next steps:")
    print(f"1. Visit: {actions_url}")
    print(f"2. Look for 'Build Windows Executable' workflow")
    print(f"3. Wait for build completion (~5-10 minutes)")
    print(f"4. Download the 'MailAgent_Client_Windows' artifact")
    print(f"5. Extract and share MailAgent_Client.exe")
    
    print(f"\n🌐 Opening GitHub Actions in browser...")
    webbrowser.open(actions_url)
    
    print(f"\n📦 What you'll get:")
    print(f"  • MailAgent_Client.exe (~60MB)")
    print(f"  • README_USER.txt (instructions)")
    print(f"  • host_ip.txt (your IP address)")
    
    print(f"\n🎯 Ready to share with Windows users!")

if __name__ == "__main__":
    main() 