import requests
import msal
import sys
import json

# CONFIGURATION - FILL THESE IN
CLIENT_ID = 'YOUR_CLIENT_ID'
TENANT_ID = 'YOUR_TENANT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'  # Or use device code flow for personal use
SUBJECT_TO_SEARCH = 'YOUR_SUBJECT'  # Or pass as argument
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3'  # Or your preferred model

# Microsoft Graph API endpoints
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPE = ['https://graph.microsoft.com/.default']
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0/me/messages'


def get_access_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if 'access_token' in result:
        return result['access_token']
    else:
        print('Error obtaining access token:', result.get('error_description'))
        sys.exit(1)


def search_email(access_token, subject):
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        '$search': f"\"subject:{subject}\"",
        '$top': 1  # Get the most recent
    }
    response = requests.get(GRAPH_API_ENDPOINT, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'value' in data and data['value']:
            return data['value'][0]  # Return the first matching email
        else:
            print('No email found with the specified subject.')
            sys.exit(0)
    else:
        print('Error searching email:', response.text)
        sys.exit(1)


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
    subject = SUBJECT_TO_SEARCH
    if len(sys.argv) > 1:
        subject = sys.argv[1]
    access_token = get_access_token()
    email = search_email(access_token, subject)
    body = email.get('body', {}).get('content', '')
    print(f"\nOriginal Email Body:\n{'-'*40}\n{body}\n{'-'*40}")
    summary = summarize_with_ollama(body)
    print(f"\nSummary:\n{'='*20}\n{summary}\n{'='*20}")


if __name__ == '__main__':
    main() 