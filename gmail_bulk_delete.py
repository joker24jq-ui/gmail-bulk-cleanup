#!/usr/bin/env python3
"""
Gmail Bulk Email Deletion Script - Enhanced Edition
Safely delete emails in bulk with multiple filter options.

Requirements:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Setup:
    1. Enable Gmail API in Google Cloud Console
    2. Create OAuth 2.0 credentials (Desktop app)
    3. Download credentials.json to same directory as this script
    4. Run: python gmail_bulk_delete.py
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import pickle
import sys

# Gmail API scope - allows full read/write access to Gmail
SCOPES = ['https://mail.google.com/']

# Configuration
CONFIG = {
    'credentials_file': 'credentials.json',
    'token_file': 'token.pickle',
    'batch_size': 500,  # Gmail API max is 500
}

# ============================================================================
# FILTER DEFINITIONS
# ============================================================================
# Define all available deletion filters with descriptions and queries
FILTERS = {
    # Time-based filters
    'old_2y': {
        'label': 'Emails older than 2 years',
        'query': 'older_than:2y',
        'category': 'Time-based'
    },
    'old_1y': {
        'label': 'Emails older than 1 year',
        'query': 'older_than:1y',
        'category': 'Time-based'
    },
    'old_6m': {
        'label': 'Emails older than 6 months',
        'query': 'older_than:6m',
        'category': 'Time-based'
    },
    'old_3m': {
        'label': 'Emails older than 3 months',
        'query': 'older_than:3m',
        'category': 'Time-based'
    },
    
    # Category-based filters (Gmail auto-categorized)
    'cat_promotions': {
        'label': 'Promotions',
        'query': 'category:promotions',
        'category': 'Categories'
    },
    'cat_social': {
        'label': 'Social updates',
        'query': 'category:social',
        'category': 'Categories'
    },
    'cat_updates': {
        'label': 'Updates & notifications',
        'query': 'category:updates',
        'category': 'Categories'
    },
    'cat_forums': {
        'label': 'Forums',
        'query': 'category:forums',
        'category': 'Categories'
    },
    
    # Sender-based filters
    'no_star': {
        'label': 'Unstarred emails (excluding important)',
        'query': '-is:starred -label:Important',
        'category': 'Star Status'
    },
    
    # Read status filters
    'read_all': {
        'label': 'All read emails',
        'query': 'is:read',
        'category': 'Read Status'
    },
    'read_old': {
        'label': 'Read emails older than 1 year',
        'query': 'is:read older_than:1y',
        'category': 'Read Status'
    },
    
    # Attachment status filters
    'no_attach': {
        'label': 'Emails without attachments',
        'query': '-has:attachment',
        'category': 'Attachments'
    },
    'no_attach_old': {
        'label': 'Read emails without attachments older than 1 year',
        'query': 'is:read -has:attachment older_than:1y',
        'category': 'Attachments'
    },
    
    # Label-based filters (excluding important labels)
    'trash': {
        'label': 'Already in Trash',
        'query': 'in:trash',
        'category': 'Labels'
    },
    'spam': {
        'label': 'Spam folder',
        'query': 'in:spam',
        'category': 'Labels'
    },
    
    # Combined filters
    'clean_up': {
        'label': 'Promotions + Social older than 6 months',
        'query': '(category:promotions OR category:social) older_than:6m',
        'category': 'Combined'
    },
    'aggressive': {
        'label': 'Read, no attachments, older than 1 year',
        'query': 'is:read -has:attachment older_than:1y -is:starred -label:Important',
        'category': 'Combined'
    },
}


# ============================================================================
# AUTHENTICATION
# ============================================================================

def get_gmail_service():
    """
    Authenticate with Gmail API using OAuth 2.0.
    
    Returns:
        Gmail API service object
        
    Raises:
        FileNotFoundError: If credentials.json not found
        Exception: If authentication fails
    """
    creds = None
    
    # Load saved token if it exists
    if os.path.exists(CONFIG['token_file']):
        with open(CONFIG['token_file'], 'rb') as token_file:
            creds = pickle.load(token_file)
    
    # If credentials don't exist or are invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired credentials
            creds.refresh(Request())
        else:
            # Perform fresh OAuth flow
            if not os.path.exists(CONFIG['credentials_file']):
                raise FileNotFoundError(
                    f"\n❌ {CONFIG['credentials_file']} not found!\n"
                    "Please download OAuth credentials from Google Cloud Console:\n"
                    "https://console.cloud.google.com/apis/credentials\n"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CONFIG['credentials_file'], SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future runs
        with open(CONFIG['token_file'], 'wb') as token_file:
            pickle.dump(creds, token_file)
    
    return build('gmail', 'v1', credentials=creds)


# ============================================================================
# EMAIL OPERATIONS
# ============================================================================

def count_emails(service, query):
    """
    Count how many emails match a query without deleting.
    
    Args:
        service: Gmail API service object
        query: Gmail search query string
        
    Returns:
        Integer count of matching emails
    """
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=1  # We only need the count
        ).execute()
        
        return results.get('resultSizeEstimate', 0)
    except HttpError as e:
        print(f"❌ Error counting emails: {e}")
        return 0


def delete_emails_by_query(service, query, batch_size=CONFIG['batch_size']):
    """
    Delete all emails matching a query in batches.
    
    Args:
        service: Gmail API service object
        query: Gmail search query string
        batch_size: Number of emails to delete per batch (max 500)
        
    Returns:
        Integer count of emails deleted
        
    Raises:
        HttpError: If API call fails
    """
    if batch_size > 500:
        batch_size = 500  # Gmail API limit
    
    total_deleted = 0
    page_token = None
    
    try:
        while True:
            # Fetch batch of emails
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=batch_size,
                pageToken=page_token
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                break
            
            # Extract message IDs
            message_ids = [msg['id'] for msg in messages]
            
            # Batch delete
            service.users().messages().batchDelete(
                userId='me',
                body={'ids': message_ids}
            ).execute()
            
            total_deleted += len(message_ids)
            print(f"   ✓ Deleted batch of {len(message_ids)} | Total: {total_deleted}")
            
            # Check for more pages
            page_token = results.get('nextPageToken')
            if not page_token:
                break
    
    except HttpError as e:
        print(f"❌ Error during deletion: {e}")
        return total_deleted
    
    return total_deleted


# ============================================================================
# USER INTERFACE
# ============================================================================

def display_filters():
    """Display all available filters grouped by category."""
    print("\n" + "=" * 70)
    print("AVAILABLE FILTERS")
    print("=" * 70)
    
    categories = {}
    
    # Group filters by category
    for key, filter_info in FILTERS.items():
        category = filter_info['category']
        if category not in categories:
            categories[category] = []
        categories[category].append((key, filter_info))
    
    # Display grouped
    filter_num = 1
    filter_map = {}
    
    for category in sorted(categories.keys()):
        print(f"\n📁 {category}:")
        print("-" * 70)
        
        for key, filter_info in categories[category]:
            print(f"  [{filter_num}] {filter_info['label']}")
            print(f"      Query: {filter_info['query']}")
            filter_map[str(filter_num)] = key
            filter_num += 1
    
    print(f"\n  [{filter_num}] Custom query")
    filter_map[str(filter_num)] = 'custom'
    
    print("\n" + "=" * 70)
    
    return filter_map


def get_user_filter_choice(filter_map):
    """
    Get filter selection from user.
    
    Args:
        filter_map: Dictionary mapping choice numbers to filter keys
        
    Returns:
        Tuple of (query, label) or None if cancelled
    """
    while True:
        choice = input(f"\nEnter filter number (1-{len(filter_map)}): ").strip()
        
        if choice not in filter_map:
            print("❌ Invalid choice. Please try again.")
            continue
        
        if filter_map[choice] == 'custom':
            query = input("\nEnter custom Gmail search query: ").strip()
            if not query:
                print("❌ Query cannot be empty.")
                continue
            return query, "Custom query"
        else:
            filter_key = filter_map[choice]
            filter_info = FILTERS[filter_key]
            return filter_info['query'], filter_info['label']


def confirm_deletion(query, count):
    """
    Get user confirmation before deletion.
    
    Args:
        query: Gmail search query
        count: Number of emails to delete
        
    Returns:
        Boolean - True if user confirms, False otherwise
    """
    print("\n" + "=" * 70)
    print("⚠️  DELETION CONFIRMATION")
    print("=" * 70)
    print(f"Query:              {query}")
    print(f"Emails to delete:   {count:,}")
    print("\n⚠️  WARNING: This action is PERMANENT and cannot be undone!")
    print("=" * 70)
    
    # Double confirmation for large deletions
    if count > 1000:
        print(f"\n🔴 Large deletion ({count:,} emails). This is a significant action.")
        confirm1 = input("Do you understand this will delete ALL matching emails? (yes/no): ").lower()
        if confirm1 != 'yes':
            return False
    
    confirm2 = input("\nType 'DELETE' to confirm permanent deletion: ").strip()
    return confirm2 == 'DELETE'


def main():
    """Main application flow."""
    print("\n" + "=" * 70)
    print("📧 GMAIL BULK EMAIL DELETION TOOL")
    print("=" * 70)
    print("\nThis tool helps you safely delete large numbers of emails.")
    print("Features:")
    print("  • Preview count before deletion")
    print("  • Multiple pre-built filters")
    print("  • Custom Gmail queries supported")
    print("  • Safe double-confirmation")
    
    try:
        # Step 1: Authenticate
        print("\n\n[1/4] Authenticating with Gmail...")
        service = get_gmail_service()
        print("✓ Authentication successful!")
        
        # Step 2: Choose filter
        print("\n[2/4] Selecting filter...")
        filter_map = display_filters()
        query, label = get_user_filter_choice(filter_map)
        
        # Step 3: Preview count
        print(f"\n[3/4] Counting emails matching: {label}...")
        count = count_emails(service, query)
        print(f"✓ Found {count:,} matching emails")
        
        if count == 0:
            print("\nNo emails found matching this filter. Exiting.")
            return
        
        # Step 4: Confirm and delete
        print(f"\n[4/4] Preparing deletion...")
        if not confirm_deletion(query, count):
            print("\n❌ Deletion cancelled by user.")
            return
        
        print("\n🗑️  Deleting emails...")
        deleted = delete_emails_by_query(service, query)
        
        print("\n" + "=" * 70)
        print(f"✅ SUCCESS! Deleted {deleted:,} emails")
        print("=" * 70 + "\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    except HttpError as e:
        print(f"\n❌ Gmail API error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
