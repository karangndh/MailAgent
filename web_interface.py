from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import json
import os
import subprocess
import threading
import time
from datetime import datetime
import sys
import signal

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    try:
        print(f"🔍 Checking for processes on port {port}...")
        
        # Find processes using the port
        try:
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                print(f"🗑️  Found {len(pids)} process(es) on port {port}")
                
                for pid in pids:
                    if pid.strip():
                        try:
                            print(f"   Killing PID {pid.strip()}...")
                            subprocess.run(['kill', '-9', pid.strip()], 
                                         capture_output=True, timeout=3)
                        except:
                            pass
                
                # Wait a moment for processes to die
                time.sleep(2)
                print(f"✅ Port {port} cleared")
            else:
                print(f"✅ Port {port} is already free")
                
        except subprocess.TimeoutExpired:
            print(f"⚠️  Timeout checking port {port}")
        except FileNotFoundError:
            # lsof not available, try alternative method
            print(f"⚠️  lsof not found, trying alternative method...")
            try:
                # Alternative: use netstat (if available)
                result = subprocess.run(['netstat', '-tulpn'], 
                                      capture_output=True, text=True, timeout=5)
                if f':{port}' in result.stdout:
                    print(f"⚠️  Port {port} appears to be in use but couldn't kill process")
                else:
                    print(f"✅ Port {port} appears to be free")
            except:
                print(f"⚠️  Could not check port {port} status")
                
    except Exception as e:
        print(f"⚠️  Error clearing port {port}: {e}")

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

DATABASE_FILE = 'email_assistants.db'

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Check system status"""
    status = {
        'database': os.path.exists(DATABASE_FILE),
        'ollama': check_ollama_status(),
        'config': os.path.exists('config.py')
    }
    return jsonify(status)

@app.route('/api/emails')
def api_emails():
    """Get all emails from database"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT assistant_id, assistant_name, account, authorization, 
                   email_subject, processed_date 
            FROM email_assistants 
            ORDER BY processed_date DESC
        ''')
        records = cursor.fetchall()
        conn.close()
        
        emails = []
        for record in records:
            emails.append({
                'assistant_id': record[0],
                'assistant_name': record[1],
                'account': record[2],
                'authorization': record[3],
                'email_subject': record[4],
                'processed_date': record[5]
            })
        
        return jsonify({'success': True, 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/summary')
def api_summary():
    """Get summary statistics for LOAs"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM email_assistants')
        total_count = cursor.fetchone()[0]
        
        # Get approved count (Authorization = 'Done')
        cursor.execute('SELECT COUNT(*) FROM email_assistants WHERE authorization = ?', ('Done',))
        approved_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True, 
            'total_count': total_count,
            'approved_count': approved_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_email', methods=['POST'])
def api_save_email():
    """Save email data from remote clients"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['assistant_id', 'assistant_name', 'account', 'authorization', 'email_subject']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'})
        
        # Save to database
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO email_assistants 
                (assistant_id, assistant_name, account, authorization, email_subject, processed_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['assistant_id'],
                data['assistant_name'], 
                data['account'],
                data['authorization'],
                data['email_subject'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return jsonify({
                'success': True, 
                'message': f'Email saved: Assistant ID={data["assistant_id"]}, Account={data["account"]}'
            })
            
        except sqlite3.IntegrityError:
            return jsonify({
                'success': False, 
                'message': f'Duplicate entry: Assistant ID={data["assistant_id"]}, Account={data["account"]}'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/run_web_search', methods=['POST'])
def api_run_web_search():
    """Run the web summarizer"""
    try:
        # Run in background thread to avoid blocking
        def run_search():
            subprocess.run([sys.executable, 'outlook_web_summarizer.py'], 
                         capture_output=True, text=True)
        
        thread = threading.Thread(target=run_search)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': 'Web search started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    """Summarize text using Ollama"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        
        # Import and use the summarization function
        from outlook_mail_summarizer import summarize_with_ollama
        summary = summarize_with_ollama(text)
        
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clear_database', methods=['POST'])
def api_clear_database():
    """Clear all records from the database"""
    try:
        import sqlite3
        
        # Connect to database and clear all records
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute('SELECT COUNT(*) FROM email_assistants')
        count_before = cursor.fetchone()[0]
        
        # Delete all records
        cursor.execute('DELETE FROM email_assistants')
        conn.commit()
        
        # Get count after deletion
        cursor.execute('SELECT COUNT(*) FROM email_assistants')
        count_after = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Database cleared successfully. Deleted {count_before} records.',
            'records_deleted': count_before
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/config')
def config_page():
    """Configuration page"""
    return render_template('config.html')

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Get or update configuration"""
    config_file = 'config.py'
    
    if request.method == 'GET':
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                return jsonify({'success': True, 'config': content})
            else:
                return jsonify({'success': False, 'error': 'Config file not found'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            config_content = data.get('config', '')
            
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            return jsonify({'success': True, 'message': 'Configuration saved'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/version', timeout=2)
        return response.status_code == 200
    except:
        return False

def create_templates():
    """Create HTML templates"""
    os.makedirs('templates', exist_ok=True)
    
    # Main index template
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mail Agent Dashboard</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f7;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { 
            background: white; border-radius: 12px; padding: 24px; 
            margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
        .status-item { 
            padding: 16px; border-radius: 8px; text-align: center;
            font-weight: 600;
        }
        .status-ok { background: #d4edda; color: #155724; }
        .status-error { background: #f8d7da; color: #721c24; }
        .btn { 
            background: #007AFF; color: white; border: none; 
            padding: 12px 24px; border-radius: 8px; cursor: pointer;
            font-size: 16px; margin: 8px;
        }
        .btn:hover { background: #0056CC; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #545b62; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .status-badge { 
            padding: 4px 12px; border-radius: 12px; font-size: 12px; 
            font-weight: 600; text-transform: uppercase;
        }
        .status-done { background: #d4edda; color: #155724; }
        .status-awaiting { background: #fff3cd; color: #856404; }
        .summary-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
        }
        .summary-card { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 24px; 
            border-radius: 12px; 
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .summary-card.approved { 
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .summary-card h3 { 
            margin: 0 0 8px 0; 
            font-size: 14px; 
            opacity: 0.9; 
            font-weight: 500;
        }
        .summary-card .count { 
            font-size: 36px; 
            font-weight: 700; 
            margin: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 Mail Agent Dashboard</h1>
        
        <div class="card">
            <h2>System Status</h2>
            <div class="status-grid" id="status-grid">
                <div class="status-item">Loading...</div>
            </div>
        </div>

        <div class="card">
            <h2>Actions</h2>
            <button class="btn" onclick="runWebSearch()">🔍 Run Web Search</button>
            <button class="btn btn-secondary" onclick="refreshEmails()">🔄 Refresh Emails</button>
            <button class="btn btn-secondary" onclick="window.location.href='/config'">⚙️ Configuration</button>
            <button class="btn btn-danger" onclick="clearDatabase()">🗑️ Clear Database</button>
        </div>

        <div class="card">
            <h2>📊 Summary</h2>
            <div class="summary-grid" id="summary-grid">
                <div class="summary-card">
                    <h3>Total Count of LOAs</h3>
                    <div class="count" id="total-count">-</div>
                </div>
                <div class="summary-card approved">
                    <h3>Approved</h3>
                    <div class="count" id="approved-count">-</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Recent Emails</h2>
            <div id="emails-container">
                <div class="loading">Loading emails...</div>
            </div>
        </div>
    </div>

    <script>
        // Load system status
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusGrid = document.getElementById('status-grid');
                statusGrid.innerHTML = `
                    <div class="status-item ${data.database ? 'status-ok' : 'status-error'}">
                        📁 Database: ${data.database ? 'OK' : 'Missing'}
                    </div>
                    <div class="status-item ${data.ollama ? 'status-ok' : 'status-error'}">
                        🤖 Ollama: ${data.ollama ? 'Running' : 'Offline'}
                    </div>
                    <div class="status-item ${data.config ? 'status-ok' : 'status-error'}">
                        ⚙️ Config: ${data.config ? 'Configured' : 'Missing'}
                    </div>
                `;
            } catch (error) {
                console.error('Error loading status:', error);
            }
        }

        // Load summary statistics
        async function loadSummary() {
            try {
                const response = await fetch('/api/summary');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('total-count').textContent = data.total_count;
                    document.getElementById('approved-count').textContent = data.approved_count;
                } else {
                    console.error('Error loading summary:', data.error);
                    document.getElementById('total-count').textContent = '?';
                    document.getElementById('approved-count').textContent = '?';
                }
            } catch (error) {
                console.error('Error loading summary:', error);
                document.getElementById('total-count').textContent = '?';
                document.getElementById('approved-count').textContent = '?';
            }
        }

        // Load emails
        async function loadEmails() {
            try {
                const response = await fetch('/api/emails');
                const data = await response.json();
                
                const container = document.getElementById('emails-container');
                
                if (data.success && data.emails.length > 0) {
                    container.innerHTML = `
                        <table>
                            <thead>
                                <tr>
                                    <th>Assistant ID</th>
                                    <th>Name</th>
                                    <th>Account</th>
                                    <th>Authorization</th>
                                    <th>Subject</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.emails.map(email => `
                                    <tr>
                                        <td>${email.assistant_id}</td>
                                        <td>${email.assistant_name}</td>
                                        <td>${email.account}</td>
                                        <td><span class="status-badge status-${email.authorization.toLowerCase()}">${email.authorization}</span></td>
                                        <td>${email.email_subject}</td>
                                        <td>${new Date(email.processed_date).toLocaleDateString()}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                } else {
                    container.innerHTML = '<p>No emails found. Run a web search to populate the database.</p>';
                }
            } catch (error) {
                console.error('Error loading emails:', error);
                document.getElementById('emails-container').innerHTML = '<p>Error loading emails.</p>';
            }
        }

        // Run web search
        async function runWebSearch() {
            try {
                const response = await fetch('/api/run_web_search', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    alert('Web search started! Check back in a few minutes for results.');
                    setTimeout(refreshEmails, 5000); // Refresh emails and summary after 5 seconds
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error starting web search: ' + error);
            }
        }

        // Refresh emails
        function refreshEmails() {
            document.getElementById('emails-container').innerHTML = '<div class="loading">Loading emails...</div>';
            loadEmails();
            loadSummary();
        }

        // Clear database with confirmation
        async function clearDatabase() {
            if (confirm('Are you sure you want to delete all email records from the database? This action cannot be undone.')) {
                try {
                    const response = await fetch('/api/clear_database', { method: 'POST' });
                    const data = await response.json();
                    
                    if (data.success) {
                        alert(data.message);
                        refreshEmails(); // Refresh the email list and summary immediately
                    } else {
                        alert('Error: ' + data.error);
                    }
                } catch (error) {
                    alert('Error clearing database: ' + error);
                }
            }
        }

        // Initialize page
        loadStatus();
        loadEmails();
        loadSummary();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            loadStatus();
            loadEmails();
            loadSummary();
        }, 30000);
    </script>
</body>
</html>'''

    with open('templates/index.html', 'w') as f:
        f.write(index_html)

    # Config template
    config_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mail Agent Configuration</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f7;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .card { 
            background: white; border-radius: 12px; padding: 24px; 
            margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        textarea { 
            width: 100%; height: 400px; font-family: monospace; 
            border: 1px solid #ddd; border-radius: 8px; padding: 12px;
            font-size: 14px;
        }
        .btn { 
            background: #007AFF; color: white; border: none; 
            padding: 12px 24px; border-radius: 8px; cursor: pointer;
            font-size: 16px; margin: 8px 0;
        }
        .btn:hover { background: #0056CC; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #545b62; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ Mail Agent Configuration</h1>
        
        <div class="card">
            <h2>Configuration File (config.py)</h2>
            <textarea id="config-content" placeholder="Loading configuration..."></textarea>
            <br>
            <button class="btn" onclick="saveConfig()">💾 Save Configuration</button>
            <button class="btn btn-secondary" onclick="window.location.href='/'">🏠 Back to Dashboard</button>
        </div>
    </div>

    <script>
        // Load configuration
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('config-content').value = data.config;
                } else {
                    document.getElementById('config-content').value = '# Configuration file not found\\n# Please create your configuration here';
                }
            } catch (error) {
                console.error('Error loading config:', error);
            }
        }

        // Save configuration
        async function saveConfig() {
            try {
                const content = document.getElementById('config-content').value;
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ config: content })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('Configuration saved successfully!');
                } else {
                    alert('Error saving configuration: ' + data.error);
                }
            } catch (error) {
                alert('Error saving configuration: ' + error);
            }
        }

        // Initialize
        loadConfig();
    </script>
</body>
</html>'''

    with open('templates/config.html', 'w') as f:
        f.write(config_html)

def initialize_app():
    """Initialize the application"""
    # Create templates
    create_templates()
    
    # Database will be in current directory
    # os.makedirs('data', exist_ok=True)
    
    # Initialize database if needed
    if not os.path.exists(DATABASE_FILE):
        try:
            # Import and call the database creation function
            from outlook_web_summarizer import create_database
            create_database()
        except ImportError:
            # Create simple database if import fails
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
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

if __name__ == '__main__':
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Mail Agent Web Interface')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (use 0.0.0.0 for external access)')
    parser.add_argument('--port', default=8080, type=int, help='Port to bind to')
    args = parser.parse_args()
    
    initialize_app()
    
    # Add Flask dependency to requirements
    try:
        import flask
    except ImportError:
        print("Installing Flask...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    
    # Kill any existing process on the specified port
    kill_process_on_port(args.port)
    
    print("🚀 Starting Mail Agent Web Interface...")
    if args.host == '0.0.0.0':
        print("🌐 External access enabled!")
        print(f"📱 Local access: http://localhost:{args.port}")
        print(f"📱 External access: http://YOUR_IP_ADDRESS:{args.port}")
        print("⚠️  Make sure your firewall allows connections on this port")
    else:
        print(f"📱 Access at: http://localhost:{args.port}")
    print(f"🔧 Configuration: http://localhost:{args.port}/config")
    
    app.run(host=args.host, port=args.port, debug=False) 