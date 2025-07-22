#!/usr/bin/env python3

import sqlite3
import os

DATABASE_FILE = 'email_assistants.db'

def view_database():
    """Display all records in the database"""
    if not os.path.exists(DATABASE_FILE):
        print(f"❌ Database file '{DATABASE_FILE}' not found!")
        print("Run the main script first to create the database.")
        return
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT assistant_id, assistant_name, account, authorization, email_subject, processed_date FROM email_assistants ORDER BY processed_date DESC')
    records = cursor.fetchall()
    
    if records:
        print(f"\n{'='*120}")
        print("EMAIL ASSISTANTS DATABASE RECORDS:")
        print(f"{'='*120}")
        print(f"{'Assistant ID':<20} {'Assistant Name':<25} {'Account':<20} {'Authorization':<15} {'Email Subject':<35} {'Date'}")
        print(f"{'-'*120}")
        
        for record in records:
            assistant_id, assistant_name, account, authorization, email_subject, processed_date = record
            # Format date for better display
            date_str = processed_date[:10] if processed_date else ""
            print(f"{assistant_id:<20} {assistant_name:<25} {account:<20} {authorization:<15} {email_subject[:33]:<35} {date_str}")
        
        print(f"{'-'*120}")
        print(f"Total records: {len(records)}")
        print(f"{'='*120}")
    else:
        print("\n📭 No records found in database")
    
    conn.close()

if __name__ == "__main__":
    view_database() 