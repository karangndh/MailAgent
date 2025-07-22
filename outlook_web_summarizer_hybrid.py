#!/usr/bin/env python3
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
        print(f"\n{'='*80}")
        print(f"SENDING RESULTS TO REMOTE DATABASE")
        print(f"{'='*80}")
        
        # For each processed email, send to remote database
        # This would include the actual email processing logic
        
        context.close()
        browser.close()
    
    print(f"\n✅ Processing complete! Sent {processed_count} emails to remote database")
    return {"count": processed_count}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8080"
    
    main(base_url)
