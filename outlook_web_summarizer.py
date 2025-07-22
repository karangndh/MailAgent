import sys
import time
from playwright.sync_api import sync_playwright
import os
import re
import sqlite3
from datetime import datetime

SESSION_FILE = 'outlook_web_session.json'
OUTLOOK_URL = 'https://outlook.office.com/mail/inbox'
DATABASE_FILE = 'email_assistants.db'

# Search criteria
SEARCH_QUERY = 'subject:"Letter Of Authorization" from:"Harshit Amar" from:Harshit.Amar@ril.com'
REQUIRED_SENDER_NAME = "Harshit Amar"
REQUIRED_SENDER_EMAIL = "Harshit.Amar@ril.com"

def create_database():
    """Create the database and table if they don't exist"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create table with the required columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_assistants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assistant_id TEXT,
            assistant_name TEXT,
            account TEXT,
            authorization TEXT,
            email_subject TEXT,
            processed_date TEXT,
            UNIQUE(assistant_id, account)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database and table created/verified")

def extract_email_data(email_body, email_subject):
    """Extract Assistant ID, Assistant name, and Account from email body"""
    data = {
        'assistant_id': '',
        'assistant_name': '',
        'account': '',
        'authorization': '',  # Keep blank as requested
        'email_subject': email_subject
    }
    
    print(f"    🔍 Extracting data from email body ({len(email_body)} chars)")
    print(f"    📄 Email Subject: '{email_subject}'")
    
    # Show first 500 chars for debugging
    debug_content = email_body[:500].replace('\n', ' ').replace('\r', ' ')
    print(f"    📝 Content preview: {debug_content}...")
    
    # Extract Assistant ID with multiple patterns
    assistant_id_patterns = [
        r'Assistant ID:\s*([^\n\r]+)',  # Standard format
        r'Assistant\s+ID:\s*([^\n\r]+)',  # With space
        r'AssistantID:\s*([^\n\r]+)',  # No space
        r'ID:\s*([^\n\r]+)',  # Just ID
        r'assistant\s*id\s*[:\-=]\s*([^\n\r\s]+)',  # Flexible ID pattern
    ]
    
    for pattern in assistant_id_patterns:
        assistant_id_match = re.search(pattern, email_body, re.IGNORECASE)
        if assistant_id_match:
            data['assistant_id'] = assistant_id_match.group(1).strip()
            print(f"    ✓ Found Assistant ID: '{data['assistant_id']}'")
            break
    
    if not data['assistant_id']:
        print(f"    ⚠️  No Assistant ID found")
    
    # Extract Assistant name with multiple patterns
    assistant_name_patterns = [
        r'Assistant name:\s*([^\n\r]+)',  # Standard format
        r'Assistant\s+name:\s*([^\n\r]+)',  # With space
        r'AssistantName:\s*([^\n\r]+)',  # No space
        r'Name:\s*([^\n\r]+)',  # Just Name
        r'assistant\s*name\s*[:\-=]\s*([^\n\r]+)',  # Flexible name pattern
        r"([^'\n\r]*)'s\s+Assistant",  # [Name]'s Assistant format
    ]
    
    for pattern in assistant_name_patterns:
        assistant_name_match = re.search(pattern, email_body, re.IGNORECASE)
        if assistant_name_match:
            data['assistant_name'] = assistant_name_match.group(1).strip()
            print(f"    ✓ Found Assistant Name: '{data['assistant_name']}'")
            break
    
    if not data['assistant_name']:
        print(f"    ⚠️  No Assistant Name found")
    
    # Extract Account (organization name before "has registered")
    account_patterns = [
        r"([^.\n\r]+?)\s+has\s+registered",  # [Organization] has registered
        r"([^.\n\r]+?)\s+has\s+already\s+registered",  # [Organization] has already registered
        r"([^.\n\r]+?)\s+is\s+registered",  # [Organization] is registered
        r"([^.\n\r]+?)\s+registered",  # [Organization] registered
        r"Organization:\s*([^\n\r]+)",  # Organization: [Name]
        r"Company:\s*([^\n\r]+)",  # Company: [Name]
    ]
    
    for pattern in account_patterns:
        account_match = re.search(pattern, email_body, re.IGNORECASE)
        if account_match:
            # Clean up the organization name
            org_name = account_match.group(1).strip()
            # Remove common prefixes if present
            org_name = re.sub(r'^(Hi\s+[^,]+,?\s*)', '', org_name, flags=re.IGNORECASE).strip()
            data['account'] = org_name
            print(f"    ✓ Found Account: '{data['account']}'")
            break
    
    if not data['account']:
        print(f"    ⚠️  No Account found using 'has registered' pattern")
        # Fallback to old Hi pattern if new pattern fails
        hi_patterns = [
            r'Hi\s+([^,\n\r]+)',  # Hi [Name],
            r'Hello\s+([^,\n\r]+)',  # Hello [Name],
            r'Dear\s+([^,\n\r]+)',  # Dear [Name],
        ]
        
        for pattern in hi_patterns:
            hi_match = re.search(pattern, email_body, re.IGNORECASE)
            if hi_match:
                data['account'] = hi_match.group(1).strip()
                print(f"    ✓ Found Account (fallback): '{data['account']}'")
                break
    
    if not data['account']:
        print(f"    ⚠️  No Account found using any pattern")
        # Show first few lines for debugging
        lines = email_body.split('\n')[:10]
        print(f"    Debug - First 10 lines: {lines}")
    
    # Enhanced debugging for missing data
    if not data['assistant_id'] and not data['assistant_name']:
        print(f"    🚨 WARNING: No Assistant ID or Name found - this email will be SKIPPED!")
        print(f"    📊 Debug Summary:")
        print(f"      - Assistant ID: '{data['assistant_id']}'")
        print(f"      - Assistant Name: '{data['assistant_name']}'") 
        print(f"      - Account: '{data['account']}'")
        print(f"      - Email will be skipped because both ID and Name are empty")
    
    return data

def save_to_database(email_data):
    """Save extracted email data to database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        # Try to insert the data (will fail if duplicate assistant_id + account combination)
        cursor.execute('''
            INSERT INTO email_assistants 
            (assistant_id, assistant_name, account, authorization, email_subject, processed_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            email_data['assistant_id'],
            email_data['assistant_name'], 
            email_data['account'],
            email_data['authorization'],
            email_data['email_subject'],
            datetime.now().isoformat()
        ))
        
        conn.commit()
        print(f"✓ Saved to database: Assistant ID={email_data['assistant_id']}, Account={email_data['account']}")
        return True
        
    except sqlite3.IntegrityError:
        print(f"⚠️  Duplicate entry skipped: Assistant ID={email_data['assistant_id']}, Account={email_data['account']}")
        return False
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        return False
    finally:
        conn.close()

def view_database():
    """Display all records in the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT assistant_id, assistant_name, account, authorization, email_subject, processed_date FROM email_assistants ORDER BY processed_date DESC')
    records = cursor.fetchall()
    
    if records:
        print(f"\n{'='*100}")
        print("DATABASE RECORDS:")
        print(f"{'='*100}")
        print(f"{'Assistant ID':<20} {'Assistant Name':<25} {'Account':<20} {'Authorization':<15} {'Email Subject':<30}")
        print(f"{'-'*100}")
        
        for record in records:
            assistant_id, assistant_name, account, authorization, email_subject, processed_date = record
            print(f"{assistant_id:<20} {assistant_name:<25} {account:<20} {authorization:<15} {email_subject[:28]:<30}")
        
        print(f"{'-'*100}")
        print(f"Total records: {len(records)}")
    else:
        print("\n📭 No records found in database")
    
    conn.close()





def update_authorization_status(assistant_id, account, authorization_status):
    """Update the authorization status in the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE email_assistants 
            SET authorization = ?
            WHERE assistant_id = ? AND account = ?
        ''', (authorization_status, assistant_id, account))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✓ Updated authorization status to '{authorization_status}' for Assistant ID: {assistant_id}, Account: {account}")
            return True
        else:
            print(f"⚠️  No record found to update for Assistant ID: {assistant_id}, Account: {account}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating authorization status: {e}")
        return False
    finally:
        conn.close()

def check_for_reply_in_thread(page, account_name):
    """Check if there's a reply from the account person in the currently opened email thread"""
    try:
        print(f"  💬 Checking for reply from '{account_name}' in email thread...")
        
        # Look for conversation items in the email view (after expansion)
        conversation_selectors = [
            'div[role="article"]',  # Individual messages in thread
            'div[aria-label="Message body"]',  # Message bodies
            '.fui-Stack:has(.fui-Stack)',  # Message containers
            '[data-convid]',  # Conversation items
            '.customScrollBar > div',  # Message divs
        ]
        
        conversation_items = []
        for selector in conversation_selectors:
            try:
                items = page.query_selector_all(selector)
                if items:
                    conversation_items = items
                    print(f"    Found {len(conversation_items)} conversation items using selector: {selector}")
                    break
            except:
                continue
        
        if not conversation_items:
            print(f"    No conversation thread found - checking main content")
            # Fallback to checking main content area
            try:
                main_content = page.query_selector('div[role="main"]')
                if main_content:
                    main_text = main_content.inner_text()
                    if account_name.lower() in main_text.lower():
                        # Look for the account name in context that suggests a reply
                        lines = main_text.split('\n')
                        for i, line in enumerate(lines):
                            if account_name.lower() in line.lower():
                                # Check surrounding lines for reply indicators
                                context = lines[max(0, i-2):i+3]
                                context_text = ' '.join(context).lower()
                                if any(indicator in context_text for indicator in ['from:', 'to:', 'sent:', 'reply', 'response']):
                                    print(f"    ✓ Found reply from '{account_name}' in main content")
                                    return True
            except:
                pass
            return False
        
        # Check each conversation item for sender information
        print(f"    Analyzing {len(conversation_items)} conversation items...")
        
        for idx, item in enumerate(conversation_items):
            try:
                # Get the full text of this conversation item
                item_text = item.inner_text() if hasattr(item, 'inner_text') else ""
                
                if not item_text:
                    continue
                
                # Look for sender name in this conversation item using multiple approaches
                sender_selectors = [
                    'span[title*="@"]',  # Sender with email in title
                    'button[aria-label*="@"]',  # Button with email
                    'span[aria-label*="@"]',  # Span with email
                    f'span:has-text("{account_name}")',  # Span containing account name
                    f'[title*="{account_name}"]',  # Any element with account name in title
                    'span.fui-Text',  # General text spans
                ]
                
                # Check structured sender elements
                for sender_selector in sender_selectors:
                    try:
                        sender_elements = item.query_selector_all(sender_selector)
                        for sender_el in sender_elements:
                            sender_text = sender_el.inner_text().strip() if hasattr(sender_el, 'inner_text') else ""
                            title_attr = sender_el.get_attribute('title') or ""
                            aria_label = sender_el.get_attribute('aria-label') or ""
                            
                            # Check if this matches our account name
                            if (account_name.lower() in sender_text.lower() or 
                                account_name.lower() in title_attr.lower() or
                                account_name.lower() in aria_label.lower()):
                                print(f"    ✓ Found reply from '{account_name}' in conversation item {idx+1} (structured)")
                                return True
                    except:
                        continue
                
                # Check raw text content for the account name in sender context
                if account_name.lower() in item_text.lower():
                    lines = item_text.split('\n')
                    for i, line in enumerate(lines):
                        if account_name.lower() in line.lower():
                            # Check if this line and surrounding context suggest it's a sender
                            # Look for patterns like "From: Name", "Name <email>", or short lines with names
                            line_clean = line.strip()
                            
                            # Check if it's a sender line (usually short and at the top)
                            if (len(line_clean) < 100 and i < 10 and  # Short line near the top
                                (any(indicator in line_clean.lower() for indicator in ['from:', 'to:', '@']) or
                                 len(line_clean.split()) <= 3)):  # Very short line (likely a name)
                                print(f"    ✓ Found reply from '{account_name}' in conversation item {idx+1} (text pattern)")
                                print(f"      Matching line: '{line_clean}'")
                                return True
                            
                            # Also check if previous/next lines give context
                            context_lines = lines[max(0, i-2):i+3]
                            context_text = ' '.join(context_lines).lower()
                            if any(indicator in context_text for indicator in ['from:', 'sent:', 'reply', 'response']):
                                print(f"    ✓ Found reply from '{account_name}' in conversation item {idx+1} (context)")
                                print(f"      Context: {' '.join(context_lines)[:100]}")
                                return True
                            
            except Exception as e:
                print(f"    Error checking conversation item {idx+1}: {e}")
                continue
        
        print(f"    ✗ No reply found from '{account_name}' in conversation thread")
        return False
        
    except Exception as e:
        print(f"    Error checking for replies in thread: {e}")
        return False



def main():
    print(f"Searching for emails using query: {SEARCH_QUERY}")
    
    # Create database and table
    create_database()
    
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
        
        def perform_search():
            """Perform the search and return email results"""
            print(f"Searching for emails using: {SEARCH_QUERY}")
        
            # Find the search box
            search_selectors = [
                'input[aria-label="Search for email, meetings, files and more."]',
                'input[placeholder*="Search"]',
                'input[type="search"]',
                'input[aria-label*="Search"]'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    search_box = page.locator(selector)
                    break
                except:
                    continue
            
            if not search_box:
                print("❌ Could not find search box!")
                return []
            
            # Enter the search query
            search_box.click()
            search_box.press('Control+a')
            search_box.press('Delete')
            page.wait_for_timeout(500)
            
            search_box.type(SEARCH_QUERY, delay=50)
            page.wait_for_timeout(500)
            
            # Press Enter to search
            search_box.press('Enter')
            page.wait_for_timeout(3000)
            
            # Get search results
            try:
                page.wait_for_selector('div[role="option"]', timeout=15000)
                email_results = page.query_selector_all('div[role="option"]')
                print(f"Found {len(email_results)} results in search page")
                return email_results
            except:
                print("No emails found in search results")
                return []
        
        # Step 2: Initial search to get email list
        email_results = perform_search()
        if not email_results:
            context.close()
            browser.close()
            return
        
        # Step 3: Extract email info from search results and store DOM elements
        emails_to_process = []
        processed_subjects = set()
        
        print(f"\n{'='*80}")
        print("ANALYZING SEARCH RESULTS")
        print(f"{'='*80}")
        
        for idx, email_item in enumerate(email_results):
            try:
                # Extract subject
                subj_el = email_item.query_selector('span.TtcXM')
                if not subj_el:
                    subj_el = email_item.query_selector('[role="heading"]') or email_item.query_selector('span[title]')
                
                extracted_subject = ""
                if subj_el:
                    extracted_subject = subj_el.inner_text().strip()
                    if not extracted_subject:
                        markjs_spans = email_item.query_selector_all('span[data-markjs="true"]')
                        if markjs_spans:
                            extracted_subject = ' '.join([span.inner_text().strip() for span in markjs_spans if span.inner_text().strip()])
                
                # Extract sender information
                sender_name = ""
                sender_email = ""
                
                sender_selectors = [
                    'span[title*="@"]',
                    'span.bJN9t',
                    'span.tLnr8',
                    '[data-convid] span:first-child',
                ]
                
                for selector in sender_selectors:
                    try:
                        sender_el = email_item.query_selector(selector)
                        if sender_el:
                            sender_text = sender_el.inner_text().strip()
                            title_attr = sender_el.get_attribute('title')
                            
                            if title_attr and '@' in title_attr:
                                if '<' in title_attr and '>' in title_attr:
                                    parts = title_attr.split('<')
                                    sender_name = parts[0].strip()
                                    sender_email = parts[1].replace('>', '').strip()
                                else:
                                    sender_email = title_attr.strip()
                                    sender_name = sender_text
                                break
                            elif sender_text:
                                sender_name = sender_text
                    except:
                        continue
                
                # Extract timestamp
                ts_el = email_item.query_selector('span.qq2gS')
                if not ts_el:
                    ts_el = email_item.query_selector('span[title*="AM"]') or email_item.query_selector('span[title*="PM"]')
                extracted_timestamp = ts_el.inner_text().strip() if ts_el else ""
                
                # Check if this email matches our criteria
                subject_match = "letter of authorization" in extracted_subject.lower()
                sender_name_match = sender_name.lower() == REQUIRED_SENDER_NAME.lower()
                sender_email_match = sender_email.lower() == REQUIRED_SENDER_EMAIL.lower()
                already_processed = extracted_subject in processed_subjects
                
                print(f"Email {idx+1}: '{extracted_subject}' from {sender_name} ({extracted_timestamp})")
                print(f"  Subject match: {subject_match}, Sender name match: {sender_name_match}, Sender email match: {sender_email_match}")
                
                if subject_match and sender_name_match and sender_email_match and extracted_timestamp and not already_processed:
                    # Check for expand button in this email item
                    has_expand_button = False
                    expand_selectors = [
                        'button[aria-label="Expand conversation"]',
                        'button[aria-label*="Expand"]',
                        'button[title*="Expand"]',
                        'button[data-testid*="expand"]'
                    ]
                    
                    for selector in expand_selectors:
                        try:
                            expand_btn = email_item.query_selector(selector)
                            if expand_btn and expand_btn.is_visible():
                                has_expand_button = True
                                break
                        except:
                            continue
                    
                    emails_to_process.append({
                        'element': email_item,  # Store the actual DOM element
                        'subject': extracted_subject,
                        'sender_name': sender_name,
                        'sender_email': sender_email,
                        'timestamp': extracted_timestamp,
                        'has_expand_button': has_expand_button,
                        'index': idx
                    })
                    processed_subjects.add(extracted_subject)
                    expand_status = "📁 Conversation" if has_expand_button else "📄 Single Email"
                    print(f"  ✅ QUEUED: {expand_status}")
                else:
                    if already_processed:
                        print(f"  ⏭️  SKIPPED: Already processed")
                    else:
                        print(f"  ❌ SKIPPED: Criteria not met")
                
            except Exception as e:
                print(f"  ❌ Error extracting email info {idx+1}: {e}")
                continue
        
        print(f"\nFound {len(emails_to_process)} unique emails to process")
        
        # Step 4: Process each email individually from the original search results
        print(f"\n{'='*80}")
        print("PROCESSING EMAILS INDIVIDUALLY")
        print(f"{'='*80}")
        
        database_entries = 0

        for email_idx, email_info in enumerate(emails_to_process):
            print(f"\n{'-'*60}")
            print(f"Processing Email #{email_idx + 1}/{len(emails_to_process)}")
            print(f"Subject: '{email_info['subject']}'")
            print(f"Timestamp: {email_info['timestamp']}")
            
            try:
                # For each email after the first, perform a fresh search to ensure clean state
                if email_idx > 0:
                    print("  🔄 Performing fresh search for clean state...")
                    page.reload()
                    page.wait_for_timeout(3000)  # Wait for page to fully load
                    
                    # Perform fresh search
                    email_results = perform_search()
                    if not email_results:
                        print("  ✗ Could not get search results after refresh")
                        continue
                else:
                    # For first email, use existing search results
                    try:
                        email_results = page.query_selector_all('div[role="option"]')
                        if not email_results:
                            print("  ✗ No search results found on current page")
                            continue
                    except Exception as e:
                        print(f"  ⚠️  Error getting current search results: {e}")
                        continue
                
                # Find the email that matches our stored subject and timestamp
                target_email_item = None
                has_expand_button = email_info['has_expand_button']
                
                for email_item in email_results:
                    try:
                        # Extract subject from current email item
                        subj_el = email_item.query_selector('span.TtcXM')
                        if not subj_el:
                            subj_el = email_item.query_selector('[role="heading"]') or email_item.query_selector('span[title]')
                        
                        current_subject = ""
                        if subj_el:
                            current_subject = subj_el.inner_text().strip()
                            if not current_subject:
                                markjs_spans = email_item.query_selector_all('span[data-markjs="true"]')
                                if markjs_spans:
                                    current_subject = ' '.join([span.inner_text().strip() for span in markjs_spans if span.inner_text().strip()])
                        
                        # Extract timestamp from current email item
                        ts_el = email_item.query_selector('span.qq2gS')
                        if not ts_el:
                            ts_el = email_item.query_selector('span[title*="AM"]') or email_item.query_selector('span[title*="PM"]')
                        current_timestamp = ts_el.inner_text().strip() if ts_el else ""
                        
                        # Check if this matches our target email
                        if (current_subject == email_info['subject'] and 
                            current_timestamp == email_info['timestamp']):
                            target_email_item = email_item
                            print(f"  ✅ Found target email: '{current_subject}' ({current_timestamp})")
                            break
                            
                    except Exception as e:
                        continue
                
                if not target_email_item:
                    print(f"  ✗ Could not find email: '{email_info['subject']}' ({email_info['timestamp']})")
                    continue
                
                print(f"  📧 Processing stored email element (index {email_info['index']})")
                expand_status = "📁 Conversation" if has_expand_button else "📄 Single Email"
                print(f"  🔍 Email type: {expand_status}")
                
                try:
                    # Check if we need to expand conversation
                    if has_expand_button:
                        print(f"  🔄 Looking for expand button...")
                        expand_selectors = [
                            'button[aria-label="Expand conversation"]',
                            'button[aria-label*="Expand"]',
                            'button[title*="Expand"]',
                            'button[data-testid*="expand"]'
                        ]
                        
                        expand_button = None
                        for selector in expand_selectors:
                            try:
                                expand_btn = target_email_item.query_selector(selector)
                                if expand_btn and expand_btn.is_visible():
                                    expand_button = expand_btn
                                    break
                            except:
                                continue
                        
                        if expand_button:
                            print(f"  ✅ Clicking expand button...")
                            expand_button.click()
                            page.wait_for_timeout(3000)
                            print(f"  ✅ Conversation expanded")
                        else:
                            print(f"  ⚠️  Expand button not found (may already be expanded)")
                    
                    # Click on the email to view content
                    print(f"  📧 Clicking on email to view content...")
                    target_email_item.click()
                    page.wait_for_timeout(3000)
                    
                except Exception as e:
                    print(f"  ⚠️  Error interacting with email element: {e}")
                    continue
                
                # Process email based on stored information
                try:
                    print("  🔍 Processing email content...")
                    
                    # Wait for email to fully load
                    page.wait_for_timeout(2000)
                    
                    # Use the determination we made during initial analysis
                    is_single_email = not has_expand_button
                    
                    if is_single_email:
                        print(f"  🎯 DECISION: Single email (no expand button found in search results)")
                    else:
                        print(f"  🎯 DECISION: Conversation thread (expand button was clicked in search results)")
                    
                    # Extract email body based on decision
                    body_text = ""
                    has_responses_from_others = False  # Initialize for each email processing
                    
                    if is_single_email:
                        # Single email - read directly
                        print("  📧 Single email: Reading content directly...")
                        has_responses_from_others = False  # Single email = no responses from others
                        
                        message_body = page.query_selector('div[aria-label="Message body"]')
                        if message_body:
                            body_text = message_body.inner_text()
                            print(f"    ✓ Extracted single email content ({len(body_text)} characters)")
                        else:
                            print(f"    ✗ Could not find message body for single email")
                    
                    else:
                        # Conversation thread - find Harshit's email (already expanded in search results)
                        print("  📧 Conversation thread: Finding Harshit's original email...")
                        
                        try:
                            # Conversation was already expanded in search results, no need to click expand again
                            print(f"    ✓ Conversation already expanded in search results")
                            
                            # Now find Harshit's original email in the expanded conversation
                            individual_emails = page.query_selector_all('div[role="treeitem"][aria-setsize][aria-posinset]')
                            
                            print(f"    Found {len(individual_emails)} individual emails in conversation")
                            
                            # If that didn't work, try alternative selectors
                            if len(individual_emails) == 0 or len(individual_emails) > 10:
                                print(f"    Trying alternative selectors for conversation emails...")
                                alternative_selectors = [
                                    'div[draggable="true"][role="treeitem"]',
                                    'div[aria-label*="AM"], div[aria-label*="PM"]',
                                    'div[class*="CB0t_"]',
                                    'div[id*="AAkALgAAAAAAHYQDEapmEc2byACqAC"]'
                                ]
                                
                                for selector in alternative_selectors:
                                    try:
                                        alt_emails = page.query_selector_all(selector)
                                        if 2 <= len(alt_emails) <= 10:  # Reasonable number of emails
                                            individual_emails = alt_emails
                                            print(f"    ✓ Using alternative selector '{selector}' - found {len(individual_emails)} emails")
                                            break
                                        else:
                                            print(f"    Selector '{selector}' found {len(alt_emails)} items - not using")
                                    except:
                                        continue
                            
                            # Find Harshit's email (bottommost)
                            harshit_emails = []
                            
                            for idx, email_item in enumerate(individual_emails):
                                try:
                                    email_text = email_item.inner_text()
                                    aria_label = email_item.get_attribute('aria-label') or ""
                                    
                                    # DEBUG: Show what each email contains
                                    email_snippet = email_text[:150].replace('\n', ' ') if email_text else "[empty]"
                                    print(f"      DEBUG Email {idx+1}: {email_snippet}...")
                                    
                                    # More precise check for Harshit's emails
                                    is_from_harshit = False
                                    sender_name = "Unknown"
                                    
                                    # Look for sender name in aria-label first (most reliable)
                                    if 'harshit amar' in aria_label.lower():
                                        is_from_harshit = True
                                        sender_name = "Harshit Amar"
                                    elif 'karan gandhi' in aria_label.lower():
                                        sender_name = "Karan Gandhi"
                                    else:
                                        # Check email text for sender indicators
                                        email_lines = email_text.split('\n')[:10]  # Check first 10 lines
                                        for line in email_lines:
                                            line_lower = line.strip().lower()
                                            if 'harshit amar' in line_lower and len(line.strip()) < 100:
                                                is_from_harshit = True
                                                sender_name = "Harshit Amar"
                                                break
                                            elif 'karan gandhi' in line_lower and len(line.strip()) < 100:
                                                sender_name = "Karan Gandhi"
                                                break
                                    
                                    print(f"      Email {idx+1}: From {sender_name}")
                                    
                                    if is_from_harshit:
                                        # Check if it has Assistant-related content
                                        has_assistant_content = ('jio business messaging' in email_text.lower() or 
                                                               'jbm assistant' in email_text.lower() or
                                                               'organization has registered' in email_text.lower() or
                                                               'assistant id:' in email_text.lower())
                                        
                                        if has_assistant_content:
                                            harshit_emails.append({
                                                'element': email_item,
                                                'index': idx,
                                                'text': email_text,
                                                'aria_label': aria_label,
                                                'sender': sender_name
                                            })
                                            print(f"      ✓ Email {idx+1}: Found Harshit email with Assistant content")
                                        else:
                                            print(f"      Email {idx+1}: From Harshit but no Assistant content")
                                        
                                except Exception as e:
                                    print(f"      Error checking email {idx+1}: {e}")
                                    continue
                            
                            # Click on Harshit's email to get full content
                            if harshit_emails:
                                # Instead of hardcoded patterns, find email that best matches original preview
                                target_email = None
                                
                                print(f"    ✓ Found {len(harshit_emails)} Harshit email(s), finding the one that matches original preview")
                                
                                # Get the original preview content we saw before expanding
                                original_preview = ""
                                try:
                                    # Try to get the content that was visible before expansion
                                    preview_body = page.query_selector('div[aria-label="Message body"]')
                                    if preview_body:
                                        original_preview = preview_body.inner_text().strip()
                                        print(f"    📄 Original preview: {original_preview[:200]}...")
                                except:
                                    pass
                                
                                # Strategy: Find the email with content most similar to original preview
                                best_match_score = 0
                                best_match_email = None
                                
                                for idx, harshit_email in enumerate(harshit_emails):
                                    email_text = harshit_email['text'].strip()
                                    
                                    # Calculate similarity score
                                    similarity_score = 0
                                    
                                    # Method 1: Check if email contains portions of original preview
                                    if original_preview and len(original_preview) > 50:
                                        # Take first 100 chars of preview (usually the most distinctive)
                                        preview_start = original_preview[:100].lower()
                                        if preview_start in email_text.lower():
                                            similarity_score += 1000  # High score for preview match
                                            print(f"      Email {harshit_email['index']+1}: PREVIEW MATCH (+1000)")
                                    
                                    # Method 2: Check for Assistant-related content uniqueness
                                    if 'assistant id:' in email_text.lower():
                                        similarity_score += 500  # Bonus for having Assistant ID
                                        print(f"      Email {harshit_email['index']+1}: HAS ASSISTANT ID (+500)")
                                    
                                    # Method 3: Content length similarity (if we have preview length)
                                    if original_preview:
                                        length_diff = abs(len(email_text) - len(original_preview))
                                        if length_diff < 200:  # Similar length
                                            similarity_score += 100
                                            print(f"      Email {harshit_email['index']+1}: SIMILAR LENGTH (+100)")
                                    
                                    # Method 4: If no preview, prefer more substantial content
                                    if not original_preview and len(email_text) > 500:
                                        similarity_score += len(email_text) // 10  # Length-based score
                                        print(f"      Email {harshit_email['index']+1}: SUBSTANTIAL CONTENT (+{len(email_text) // 10})")
                                    
                                    print(f"      Email {harshit_email['index']+1}: Total score = {similarity_score}")
                                    
                                    if similarity_score > best_match_score:
                                        best_match_score = similarity_score
                                        best_match_email = harshit_email
                                        print(f"      ⭐ NEW BEST MATCH with score {similarity_score}")
                                
                                # Use the best match, or fallback to first email with Assistant content
                                if best_match_email:
                                    target_email = best_match_email
                                    print(f"    ✅ Selected email {target_email['index']+1} as best match (score: {best_match_score})")
                                else:
                                    # Fallback: first email with Assistant content
                                    for harshit_email in harshit_emails:
                                        if 'assistant id:' in harshit_email['text'].lower():
                                            target_email = harshit_email
                                            print(f"    ⚠️ Fallback: Using first email with Assistant content (index {target_email['index']+1})")
                                            break
                                    
                                    # Final fallback: first email
                                    if not target_email:
                                        target_email = harshit_emails[0]
                                        print(f"    ⚠️ Final fallback: Using first email (index {target_email['index']+1})")
                                
                                try:
                                    # Click on the identified target email
                                    print(f"    ✓ Clicking on target email (index {target_email['index']})...")
                                    target_email['element'].click()
                                    page.wait_for_timeout(3000)  # Wait longer for content to load
                                    
                                    # Debug: Check what's currently visible
                                    current_bodies = page.query_selector_all('div[aria-label="Message body"]')
                                    print(f"    DEBUG: Found {len(current_bodies)} message bodies after clicking")
                                    
                                    # Try multiple approaches to get the email content
                                    full_body_text = ""
                                    
                                    # Approach 1: When multiple message bodies exist, find the best one
                                    if len(current_bodies) > 1:
                                        print(f"    ✓ Multiple message bodies found - analyzing each one...")
                                        best_body = None
                                        best_score = 0
                                        has_responses_from_others = False
                                        
                                        for idx, body in enumerate(current_bodies):
                                            try:
                                                body_text = body.inner_text()
                                                body_len = len(body_text)
                                                
                                                # Enhanced content analysis to find Harshit's email specifically
                                                is_from_harshit = False
                                                is_from_other = False
                                                
                                                # Check if this body contains Harshit's original content
                                                harshit_indicators = [
                                                    'hi karan gandhi' in body_text.lower(),
                                                    'hi karan' in body_text.lower(),
                                                    'letter of authorization' in body_text.lower(),
                                                    ('organization has registered' in body_text.lower() and 'jio business messaging' in body_text.lower()),
                                                    ('jbm assistant' in body_text.lower() and 'assistant id:' in body_text.lower())
                                                ]
                                                
                                                # Check if this body contains responses from others
                                                other_indicators = [
                                                    ('thank' in body_text.lower() and len(body_text) < 500),
                                                    ('received' in body_text.lower() and len(body_text) < 500),
                                                    ('acknowledged' in body_text.lower() and len(body_text) < 500),
                                                    ('regards' in body_text.lower() and 'karan' in body_text.lower()),
                                                    ('from:' in body_text.lower() and 'harshit' not in body_text.lower())
                                                ]
                                                
                                                is_from_harshit = any(harshit_indicators)
                                                is_from_other = any(other_indicators) and not is_from_harshit
                                                
                                                # Track responses from others for authorization status
                                                if is_from_other:
                                                    has_responses_from_others = True
                                                
                                                # ENHANCED DEBUGGING: Check for specific content patterns
                                                has_24723 = '24723' in body_text
                                                has_qwerty = 'qwerty' in body_text
                                                has_shashank = 'shashank' in body_text.lower()
                                                has_assistant_id = 'assistant id:' in body_text.lower()
                                                
                                                print(f"      Body {idx+1}: {body_len} chars")
                                                print(f"        From Harshit: {is_from_harshit}")
                                                print(f"        From Other: {is_from_other}")
                                                print(f"        Has Assistant ID: {has_assistant_id}")
                                                print(f"        Contains 24723: {has_24723}")
                                                print(f"        Contains qwerty: {has_qwerty}")
                                                print(f"        Contains Shashank: {has_shashank}")
                                                
                                                if body_len > 100:  # Show snippet for substantial content
                                                    snippet = body_text[:150].replace('\n', ' ')
                                                    print(f"        Snippet: {snippet}...")
                                                
                                                # Priority selection: Harshit's emails with Assistant content
                                                if is_from_harshit and has_assistant_id:
                                                    score = 10000  # Highest priority
                                                    print(f"        ⭐ PRIORITY: Harshit's email with Assistant ID")
                                                elif is_from_harshit:
                                                    score = 5000   # High priority for Harshit
                                                    print(f"        ✅ Harshit's email")
                                                elif has_assistant_id:
                                                    score = 1000   # Medium priority for Assistant content
                                                    print(f"        📋 Has Assistant ID")
                                                else:
                                                    score = body_len  # Fallback to length
                                                    print(f"        �� Using length score")
                                                
                                                if score > best_score:
                                                    best_score = score
                                                    best_body = body
                                                    print(f"        🎯 NEW BEST with score {score}")
                                                                    
                                            except Exception as e:
                                                print(f"      Error analyzing body {idx+1}: {e}")
                                                continue
                                        
                                        if best_body:
                                            full_body_text = best_body.inner_text()
                                            print(f"    ✓ Selected best message body with score {best_score} ({len(full_body_text)} chars)")
                                            print(f"    🔍 Detected responses from others: {has_responses_from_others}")
                                            # Show what Assistant ID we're about to extract
                                            if '24723' in full_body_text:
                                                print(f"    ✅ Selected body contains 24723 - this looks correct for PQR")
                                            elif 'qwerty' in full_body_text:
                                                print(f"    ❌ WARNING: Selected body contains qwerty - this might be wrong for PQR")
                                    
                                    # Approach 2: Single message body
                                    elif len(current_bodies) == 1:
                                        full_body_element = current_bodies[0]
                                        full_body_text = full_body_element.inner_text()
                                        has_responses_from_others = False  # Single message = no responses from others
                                        print(f"    ✓ Using single message body ({len(full_body_text)} chars)")
                                    
                                    # Approach 3: No message bodies found, try alternative approach
                                    else:
                                        has_responses_from_others = False  # No message bodies = no responses from others
                                        print(f"    ⚠️  No message bodies found, trying alternative approach...")
                                        # Try to find content within the clicked email element
                                        try:
                                            email_content = target_email['element'].query_selector('div[aria-label="Message body"]')
                                            if not email_content:
                                                # Look for any content div within the email
                                                content_divs = target_email['element'].query_selector_all('div')
                                                for div in content_divs:
                                                    div_text = div.inner_text()
                                                    if len(div_text) > 200 and 'assistant' in div_text.lower():
                                                        full_body_text = div_text
                                                        print(f"    ✓ Found Assistant content in email element ({len(full_body_text)} chars)")
                                                        break
                                            else:
                                                full_body_text = email_content.inner_text()
                                                print(f"    ✓ Found message body within email element ({len(full_body_text)} chars)")
                                        except Exception as e:
                                            print(f"    ⚠️  Error accessing email element content: {e}")
                                    
                                    # Final verification
                                    if full_body_text:
                                        # Check if this is the right content
                                        if 'assistant id' in full_body_text.lower():
                                            print(f"    ✓ Found Assistant ID in selected content")
                                        else:
                                            print(f"    ⚠️  Selected content doesn't contain Assistant ID - showing what we have")
                                    
                                    if full_body_text:
                                        body_text = full_body_text
                                        print(f"    ✓ Successfully extracted Harshit's original email with complete Assistant data")
                                    else:
                                        print(f"    ✗ Could not find any message body content after clicking")
                                        
                                except Exception as e:
                                    print(f"    ✗ Error clicking on Harshit's email: {e}")
                            else:
                                print(f"    ✗ No emails from Harshit with Assistant content found in conversation")
                            
                        except Exception as e:
                            print(f"    ✗ Error processing expanded conversation: {e}")
                            body_text = ""
                    
                    if body_text:
                        print(f"  ✓ Email body extracted successfully ({len(body_text)} characters)")
                        # Show a snippet for debugging
                        snippet = body_text[:200].replace('\n', ' ')
                        print(f"    Snippet: {snippet}...")
                    else:
                        print(f"  ✗ Could not find email body")
                        continue
                        
                except Exception as e:
                    print(f"  ✗ Error extracting email body: {e}")
                    continue
                
                # Extract data for database
                extracted_data = extract_email_data(body_text, email_info['subject'])
                
                print(f"  Extracted Data:")
                print(f"    Assistant ID: '{extracted_data['assistant_id']}'")
                print(f"    Assistant Name: '{extracted_data['assistant_name']}'")
                print(f"    Account: '{extracted_data['account']}'")
                
                # Save to database if we have required data
                if not (extracted_data['assistant_id'] or extracted_data['assistant_name']):
                    print(f"  ⚠️  No Assistant ID or Assistant Name found - skipping")
                    continue
                
                # Prepare data for database saving
                db_data = {
                    'assistant_id': extracted_data['assistant_id'],
                    'assistant_name': extracted_data['assistant_name'],
                    'account': extracted_data['account'],
                    'authorization': 'Awaiting',  # Default status - will be updated below
                    'email_subject': email_info['subject']
                }
                
                # Determine authorization status using enhanced logic
                if is_single_email:
                    # Single email (no expand button) = no responses = Awaiting
                    authorization_status = "Awaiting"
                    print(f"  🟡 Single email (no expand button) → Authorization: 'Awaiting'")
                else:
                    # Conversation thread - use the enhanced detection
                    if has_responses_from_others:
                        authorization_status = "Done"
                        print(f"  ✅ Conversation thread with responses detected → Authorization: 'Done'")
                    else:
                        authorization_status = "Awaiting"
                        print(f"  ⏳ Conversation thread with no responses detected → Authorization: 'Awaiting'")
                
                # Update the database entry with the determined authorization status
                db_data['authorization'] = authorization_status
                
                saved = save_to_database(db_data)
                if saved:
                    database_entries += 1
                    
                    # Update database with authorization status
                    account_name = extracted_data['account']
                    if account_name and extracted_data['assistant_id']:
                        update_authorization_status(extracted_data['assistant_id'], account_name, authorization_status)
                    else:
                        print(f"  ⚠️  Cannot update authorization - missing account or assistant ID")
                
            except Exception as e:
                print(f"  ✗ Error processing email: {e}")
                continue
        
        context.close()
        browser.close()
    
    # Display final database contents
    print(f"\n{'='*80}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"🗃️  Processed {database_entries} emails and added to database")
    view_database()

if __name__ == '__main__':
    main() 