#!/usr/bin/env python3
"""
Gmail Bulk Email Deletion - Web UI
Runs a Flask web server with beautiful black/royal blue interface.

Requirements:
    pip install flask google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Run:
    python gmail_ui.py
"""

from flask import Flask, render_template_string, request, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import pickle
import threading

app = Flask(__name__)

SCOPES = ['https://mail.google.com/']

CONFIG = {
    'credentials_file': 'credentials.json',
    'token_file': 'token.pickle',
    'batch_size': 500,
}

FILTERS = {
    'old_2y': {'label': 'Emails older than 2 years', 'query': 'older_than:2y', 'category': 'Time-based'},
    'old_1y': {'label': 'Emails older than 1 year', 'query': 'older_than:1y', 'category': 'Time-based'},
    'old_6m': {'label': 'Emails older than 6 months', 'query': 'older_than:6m', 'category': 'Time-based'},
    'old_3m': {'label': 'Emails older than 3 months', 'query': 'older_than:3m', 'category': 'Time-based'},
    'cat_promotions': {'label': 'Promotions', 'query': 'category:promotions', 'category': 'Categories'},
    'cat_social': {'label': 'Social updates', 'query': 'category:social', 'category': 'Categories'},
    'cat_updates': {'label': 'Updates & notifications', 'query': 'category:updates', 'category': 'Categories'},
    'cat_forums': {'label': 'Forums', 'query': 'category:forums', 'category': 'Categories'},
    'no_star': {'label': 'Unstarred emails', 'query': '-is:starred -label:Important', 'category': 'Star Status'},
    'read_all': {'label': 'All read emails', 'query': 'is:read', 'category': 'Read Status'},
    'read_old': {'label': 'Read emails older than 1 year', 'query': 'is:read older_than:1y', 'category': 'Read Status'},
    'no_attach': {'label': 'Emails without attachments', 'query': '-has:attachment', 'category': 'Attachments'},
    'no_attach_old': {'label': 'Read, no attachments, older than 1 year', 'query': 'is:read -has:attachment older_than:1y', 'category': 'Attachments'},
    'trash': {'label': 'Already in Trash', 'query': 'in:trash', 'category': 'Labels'},
    'spam': {'label': 'Spam folder', 'query': 'in:spam', 'category': 'Labels'},
    'clean_up': {'label': 'Promotions + Social older than 6m', 'query': '(category:promotions OR category:social) older_than:6m', 'category': 'Combined'},
    'aggressive': {'label': 'Read, no attachments, older than 1 year', 'query': 'is:read -has:attachment older_than:1y -is:starred -label:Important', 'category': 'Combined'},
}

deletion_in_progress = False
deletion_progress = {'current': 0, 'total': 0, 'status': 'idle'}

def get_gmail_service():
    creds = None
    if os.path.exists(CONFIG['token_file']):
        with open(CONFIG['token_file'], 'rb') as token_file:
            creds = pickle.load(token_file)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CONFIG['credentials_file']):
                raise FileNotFoundError(f"{CONFIG['credentials_file']} not found!")
            flow = InstalledAppFlow.from_client_secrets_file(CONFIG['credentials_file'], SCOPES)
            creds = flow.run_local_server(port=0)
        with open(CONFIG['token_file'], 'wb') as token_file:
            pickle.dump(creds, token_file)
    return build('gmail', 'v1', credentials=creds)

def count_emails(service, query):
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        return results.get('resultSizeEstimate', 0)
    except HttpError:
        return -1

def delete_emails_by_query(service, query):
    global deletion_progress
    total_deleted = 0
    page_token = None
    deletion_progress['status'] = 'deleting'
    
    try:
        while True:
            results = service.users().messages().list(userId='me', q=query, maxResults=CONFIG['batch_size'], pageToken=page_token).execute()
            messages = results.get('messages', [])
            if not messages:
                break
            message_ids = [msg['id'] for msg in messages]
            service.users().messages().batchDelete(userId='me', body={'ids': message_ids}).execute()
            total_deleted += len(message_ids)
            deletion_progress['current'] = total_deleted
            page_token = results.get('nextPageToken')
            if not page_token:
                break
    except HttpError:
        deletion_progress['status'] = 'error'
        return -1
    
    deletion_progress['status'] = 'complete'
    return total_deleted

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/filters')
def get_filters():
    categories = {}
    for key, info in FILTERS.items():
        cat = info['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({'key': key, 'label': info['label'], 'query': info['query']})
    return jsonify(categories)

@app.route('/api/count', methods=['POST'])
def count():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query'}), 400
    try:
        service = get_gmail_service()
        cnt = count_emails(service, query)
        return jsonify({'count': cnt})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete():
    global deletion_in_progress, deletion_progress
    if deletion_in_progress:
        return jsonify({'error': 'Deletion in progress'}), 400
    
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query'}), 400
    
    def do_deletion():
        global deletion_in_progress, deletion_progress
        try:
            deletion_in_progress = True
            service = get_gmail_service()
            cnt = count_emails(service, query)
            deletion_progress['total'] = cnt
            deletion_progress['current'] = 0
            deleted = delete_emails_by_query(service, query)
            deletion_in_progress = False
        except Exception as e:
            deletion_progress['status'] = 'error'
            deletion_progress['error'] = str(e)
            deletion_in_progress = False
    
    thread = threading.Thread(target=do_deletion, daemon=True)
    thread.start()
    return jsonify({'status': 'deleting'})

@app.route('/api/progress')
def progress():
    return jsonify(deletion_progress)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gmail Bulk Cleanup</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Audiowide&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Space Mono', monospace;
            background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f1629 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #e0e0e0;
        }
        .container {
            width: 100%;
            max-width: 900px;
            background: #16213e;
            border: 3px solid #4a90e2;
            box-shadow: 0 0 40px rgba(74, 144, 226, 0.4);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(90deg, #0a2463 0%, #1a5490 50%, #0a2463 100%);
            padding: 60px 30px;
            text-align: center;
            border-bottom: 4px solid #4a90e2;
        }
        .header h1 {
            font-family: 'Audiowide', cursive;
            font-size: 56px;
            color: #fff;
            margin-bottom: 10px;
            letter-spacing: 3px;
            text-shadow: 0 0 30px rgba(74, 144, 226, 0.8);
            text-transform: uppercase;
        }
        .header p {
            color: #b0c4de;
            font-size: 13px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .content { padding: 40px 30px; }
        .section { margin-bottom: 35px; }
        .section-title {
            font-size: 13px;
            font-weight: 700;
            color: #4a90e2;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 2px solid rgba(74, 144, 226, 0.3);
            padding-bottom: 8px;
        }
        .filters-container {
            display: grid;
            gap: 8px;
            max-height: 600px;
            overflow-y: auto;
            padding-right: 10px;
        }
        .filters-container::-webkit-scrollbar { width: 8px; }
        .filters-container::-webkit-scrollbar-track { background: rgba(74, 144, 226, 0.1); }
        .filters-container::-webkit-scrollbar-thumb { background: #4a90e2; }
        .category { margin-bottom: 20px; }
        .category-label {
            font-size: 11px;
            font-weight: 700;
            color: #7a9fd1;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 8px;
            padding-left: 10px;
            border-left: 3px solid #4a90e2;
        }
        .filter-option { position: relative; }
        .filter-option input[type="radio"] { display: none; }
        .filter-option label {
            display: block;
            padding: 11px 14px;
            background: rgba(74, 144, 226, 0.1);
            border: 2px solid rgba(74, 144, 226, 0.3);
            cursor: pointer;
            transition: all 0.2s ease;
            color: #e0e0e0;
            font-size: 13px;
        }
        .filter-option input[type="radio"]:checked + label {
            background: rgba(74, 144, 226, 0.3);
            border-color: #4a90e2;
            box-shadow: 0 0 15px rgba(74, 144, 226, 0.6);
            color: #fff;
        }
        .filter-option label:hover { border-color: #4a90e2; background: rgba(74, 144, 226, 0.15); }
        .custom-query { margin-top: 15px; }
        .custom-query input {
            width: 100%;
            padding: 12px 15px;
            background: rgba(74, 144, 226, 0.1);
            border: 2px solid rgba(74, 144, 226, 0.3);
            color: #e0e0e0;
            font-size: 13px;
            font-family: 'Space Mono', monospace;
        }
        .custom-query input:focus {
            outline: none;
            border-color: #4a90e2;
            background: rgba(74, 144, 226, 0.15);
            box-shadow: 0 0 15px rgba(74, 144, 226, 0.5);
        }
        .info-box {
            background: rgba(74, 144, 226, 0.1);
            border-left: 4px solid #4a90e2;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 13px;
        }
        .info-box.warning { background: rgba(255, 180, 0, 0.1); border-left-color: #ffb400; color: #ffd700; }
        .info-box.success { background: rgba(76, 175, 80, 0.1); border-left-color: #4caf50; color: #90ee90; }
        .info-box.error { background: rgba(244, 67, 54, 0.1); border-left-color: #f44336; color: #ff6b6b; }
        .count-display {
            font-size: 40px;
            font-weight: 700;
            color: #4a90e2;
            margin: 15px 0;
            font-family: 'Audiowide', cursive;
        }
        .buttons { display: flex; gap: 10px; margin-top: 20px; }
        button {
            flex: 1;
            padding: 13px 20px;
            border: 2px solid #4a90e2;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-family: 'Space Mono', monospace;
            background: rgba(74, 144, 226, 0.15);
            color: #4a90e2;
        }
        .btn-check:hover:not(:disabled) { background: rgba(74, 144, 226, 0.3); box-shadow: 0 0 20px rgba(74, 144, 226, 0.6); transform: translateY(-2px); }
        .btn-delete { background: rgba(231, 76, 60, 0.15); color: #ff6b6b; border-color: #e74c3c; }
        .btn-delete:hover:not(:disabled) { background: rgba(231, 76, 60, 0.3); box-shadow: 0 0 20px rgba(231, 76, 60, 0.6); transform: translateY(-2px); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .progress-bar { width: 100%; height: 8px; background: rgba(74, 144, 226, 0.15); border: 1px solid rgba(74, 144, 226, 0.3); overflow: hidden; margin-top: 10px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #4a90e2 0%, #6ba3f5 100%); width: 0%; transition: width 0.3s ease; }
        .progress-text { font-size: 12px; color: #888; margin-top: 5px; }
        .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(74, 144, 226, 0.3); border-top-color: #4a90e2; animation: spin 0.8s linear infinite; margin-right: 8px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .footer { background: rgba(0, 0, 0, 0.3); padding: 15px 30px; text-align: center; border-top: 2px solid rgba(74, 144, 226, 0.2); font-size: 11px; color: #666; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Gmail Bulk Cleanup</h1>
            <p>Modern Email Management</p>
        </div>
        <div class="content">
            <div class="section">
                <div class="section-title">Select Filter</div>
                <div class="filters-container" id="filtersContainer">Loading filters...</div>
                <div class="custom-query">
                    <input type="text" id="customQuery" placeholder="Or enter custom Gmail query...">
                </div>
            </div>
            <div class="section">
                <div class="section-title">Preview</div>
                <div id="countInfo" class="info-box" style="display: none;">
                    <div>Matching Emails:</div>
                    <div class="count-display" id="emailCount">0</div>
                    <button class="btn-delete" id="deleteBtn" style="width: 100%; margin-top: 10px;">⚡ DELETE</button>
                </div>
                <div id="noCount" class="info-box info-box.warning">⚠️ Click "CHECK COUNT" to preview</div>
            </div>
            <div class="section">
                <div class="buttons">
                    <button class="btn-check" id="checkBtn">▶ CHECK COUNT</button>
                </div>
            </div>
            <div id="statusMsg"></div>
            <div id="progressContainer" style="display: none;">
                <div class="info-box info-box.warning">
                    <div style="display: flex; align-items: center;">
                        <div class="spinner"></div>
                        <span id="progressText">DELETING...</span>
                    </div>
                    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                    <div class="progress-text" id="progressDetails"></div>
                </div>
            </div>
        </div>
        <div class="footer">► GMAIL BULK CLEANUP • V1.0 ◄</div>
    </div>

    <script>
        let selectedFilter = null;
        let emailCount = 0;

        document.addEventListener('DOMContentLoaded', () => {
            loadFilters();
            document.getElementById('checkBtn').addEventListener('click', checkCount);
            document.getElementById('deleteBtn').addEventListener('click', deleteEmails);
            document.getElementById('customQuery').addEventListener('input', clearSelection);
        });

        function loadFilters() {
            fetch('/api/filters')
                .then(r => r.json())
                .then(categories => {
                    const container = document.getElementById('filtersContainer');
                    container.innerHTML = '';

                    const sortedKeys = Object.keys(categories).sort();
                    sortedKeys.forEach(category => {
                        const categoryDiv = document.createElement('div');
                        categoryDiv.className = 'category';

                        const label = document.createElement('div');
                        label.className = 'category-label';
                        label.textContent = category;
                        categoryDiv.appendChild(label);

                        categories[category].forEach(filter => {
                            const optionDiv = document.createElement('div');
                            optionDiv.className = 'filter-option';

                            const input = document.createElement('input');
                            input.type = 'radio';
                            input.id = filter.key;
                            input.name = 'filter';
                            input.value = filter.query;
                            input.addEventListener('change', () => {
                                selectedFilter = filter.query;
                                document.getElementById('customQuery').value = '';
                            });

                            const lbl = document.createElement('label');
                            lbl.htmlFor = filter.key;
                            lbl.textContent = filter.label;

                            optionDiv.appendChild(input);
                            optionDiv.appendChild(lbl);
                            categoryDiv.appendChild(optionDiv);
                        });

                        container.appendChild(categoryDiv);
                    });
                })
                .catch(e => {
                    document.getElementById('filtersContainer').innerHTML = '<div class="info-box error">Error loading filters: ' + e + '</div>';
                });
        }

        function clearSelection() {
            document.querySelectorAll('input[name="filter"]').forEach(i => i.checked = false);
            selectedFilter = null;
        }

        function checkCount() {
            const query = document.getElementById('customQuery').value.trim() || selectedFilter;
            if (!query) {
                showStatus('Please select a filter', 'error');
                return;
            }

            document.getElementById('checkBtn').disabled = true;
            document.getElementById('checkBtn').textContent = '⟳ CHECKING...';

            fetch('/api/count', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) })
                .then(r => r.json())
                .then(data => {
                    emailCount = data.count || 0;
                    if (emailCount === 0) {
                        showStatus('No emails found', 'warning');
                        document.getElementById('countInfo').style.display = 'none';
                    } else {
                        document.getElementById('emailCount').textContent = emailCount.toLocaleString();
                        document.getElementById('countInfo').style.display = 'block';
                        document.getElementById('noCount').style.display = 'none';
                    }
                })
                .catch(e => showStatus('Error: ' + e, 'error'))
                .finally(() => {
                    document.getElementById('checkBtn').disabled = false;
                    document.getElementById('checkBtn').textContent = '▶ CHECK COUNT';
                });
        }

        function deleteEmails() {
            const query = document.getElementById('customQuery').value.trim() || selectedFilter;
            if (!query || emailCount === 0) {
                showStatus('No emails to delete', 'error');
                return;
            }

            if (!confirm(`⚠️ DELETE ${emailCount.toLocaleString()} EMAILS?\n\nThis CANNOT be undone!`)) return;
            if (!confirm('🔴 FINAL CONFIRMATION - Ready to delete?')) return;

            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('countInfo').style.display = 'none';

            fetch('/api/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) })
                .then(() => trackProgress())
                .catch(e => showStatus('Error: ' + e, 'error'));
        }

        function trackProgress() {
            const interval = setInterval(() => {
                fetch('/api/progress')
                    .then(r => r.json())
                    .then(p => {
                        const pct = p.total > 0 ? (p.current / p.total * 100) : 0;
                        document.getElementById('progressFill').style.width = pct + '%';
                        document.getElementById('progressDetails').textContent = `${p.current.toLocaleString()} / ${p.total.toLocaleString()}`;
                        
                        if (p.status === 'complete') {
                            clearInterval(interval);
                            showStatus(`✅ Deleted ${p.current.toLocaleString()} emails!`, 'success');
                            document.getElementById('progressContainer').style.display = 'none';
                        } else if (p.status === 'error') {
                            clearInterval(interval);
                            showStatus('Error: ' + (p.error || 'Unknown'), 'error');
                            document.getElementById('progressContainer').style.display = 'none';
                        }
                    });
            }, 500);
        }

        function showStatus(msg, type) {
            const box = document.createElement('div');
            box.className = `info-box info-box.${type}`;
            box.textContent = msg;
            document.getElementById('statusMsg').innerHTML = '';
            document.getElementById('statusMsg').appendChild(box);
        }
    </script>
</body>
</html>'''

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("📧 Gmail Bulk Cleanup")
    print("=" * 70)
    print("\n✓ Starting server...")
    print("✓ Opening http://localhost:5000\n")
    import webbrowser
    webbrowser.open('http://localhost:5000')
    app.run(debug=False, port=5000)
