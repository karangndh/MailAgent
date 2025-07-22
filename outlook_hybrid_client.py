#!/usr/bin/env python3
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
            messagebox.showerror("Connection Error", f"Cannot connect to {self.base_url}\nError: {str(e)}")
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
                f"Processed {results.get('count', 0)} emails\n"
                f"View results at: {self.base_url}"
            )
            root.destroy()
            
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error", f"Email processing failed:\n{str(e)}")
            root.destroy()

def main():
    client = MailAgentClient()
    client.setup_connection()
    client.run_email_processing()

if __name__ == "__main__":
    main()
