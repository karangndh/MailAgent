#!/usr/bin/env python3

import sqlite3
import os

DATABASE_FILE = 'email_assistants.db'

def clear_database():
    """Clear all records from the email_assistants database"""
    if not os.path.exists(DATABASE_FILE):
        print(f"❌ Database file '{DATABASE_FILE}' not found!")
        return
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get count of records before clearing
        cursor.execute('SELECT COUNT(*) FROM email_assistants')
        record_count = cursor.fetchone()[0]
        
        if record_count == 0:
            print("📭 Database is already empty!")
            conn.close()
            return
        
        print(f"Found {record_count} records in database")
        
        # Confirm before clearing
        confirm = input(f"Are you sure you want to delete all {record_count} records? (y/N): ")
        
        if confirm.lower() in ['y', 'yes']:
            # Clear all records
            cursor.execute('DELETE FROM email_assistants')
            conn.commit()
            
            print(f"✅ Successfully cleared {record_count} records from database")
            print("🗑️  Database is now empty")
        else:
            print("❌ Operation cancelled")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")

def clear_database_force():
    """Clear all records without confirmation - for automated testing"""
    if not os.path.exists(DATABASE_FILE):
        print(f"❌ Database file '{DATABASE_FILE}' not found!")
        return
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get count of records before clearing
        cursor.execute('SELECT COUNT(*) FROM email_assistants')
        record_count = cursor.fetchone()[0]
        
        if record_count == 0:
            print("📭 Database is already empty!")
            conn.close()
            return
        
        # Clear all records without confirmation
        cursor.execute('DELETE FROM email_assistants')
        conn.commit()
        
        print(f"✅ Force cleared {record_count} records from database")
        print("🗑️  Database is now empty")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")

if __name__ == "__main__":
    import sys
    
    # Check for force flag
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        clear_database_force()
    else:
        clear_database() 