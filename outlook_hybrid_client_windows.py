#!/usr/bin/env python3
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
                    messagebox.showinfo("Success", f"✅ Connected to Mail Agent host!\n{self.base_url}")
                    root.destroy()
                else:
                    messagebox.showerror("Connection Error", f"Invalid response from {self.base_url}")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Cannot connect to {self.base_url}\n\nError: {str(e)}\n\nMake sure the host is running:\npython web_interface.py --host 0.0.0.0")
        
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
