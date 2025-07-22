import subprocess
import sys
import requests

OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3'  # Or your preferred model

def get_email_body(subject):
    applescript = f'''
    tell application "Microsoft Outlook"
        set theMessages to messages of inbox whose subject is "{subject}"
        if (count of theMessages) > 0 then
            set theBody to content of item 1 of theMessages
            return theBody
        else
            return "NO_EMAIL_FOUND"
        end if
    end tell
    '''
    process = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
    result = process.stdout.strip()
    if result == "NO_EMAIL_FOUND":
        print("No email found with the specified subject.")
        sys.exit(0)
    return result

def summarize_with_ollama(text):
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': f"Summarize the following email:\n{text}",
        'stream': False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    if response.status_code == 200:
        return response.json().get('response', '').strip()
    else:
        print('Error from Ollama:', response.text)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python outlook_mac_summarizer.py 'Email Subject'")
        sys.exit(1)
    subject = sys.argv[1]
    body = get_email_body(subject)
    print(f"\nOriginal Email Body:\n{'-'*40}\n{body}\n{'-'*40}")
    summary = summarize_with_ollama(body)
    print(f"\nSummary:\n{'='*20}\n{summary}\n{'='*20}")

if __name__ == '__main__':
    main() 