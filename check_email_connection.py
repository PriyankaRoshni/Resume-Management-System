#!/usr/bin/env python3
"""
Script to check which email accounts are connected in the system.
"""

import os
import pickle
from pathlib import Path

print("=" * 60)
print("EMAIL CONNECTION CHECKER")
print("=" * 60)
print()

# Check Gmail connection
print("1. GMAIL CONNECTION")
print("-" * 60)
token_file = Path("token.pickle")
credentials_file = Path("credentials.json")

if token_file.exists():
    print(f"✓ Token file found: {token_file.absolute()}")
    try:
        with open(token_file, 'rb') as f:
            creds = pickle.load(f)
            print(f"  - Token file size: {token_file.stat().st_size} bytes")
            print(f"  - Token valid: {creds.valid if hasattr(creds, 'valid') else 'Unknown'}")
            print(f"  - Token expired: {creds.expired if hasattr(creds, 'expired') else 'Unknown'}")
            
            # Try to get email from token
            try:
                from googleapiclient.discovery import build
                from google.auth.transport.requests import Request
                
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                
                service = build('gmail', 'v1', credentials=creds)
                profile = service.users().getProfile(userId='me').execute()
                email_address = profile.get('emailAddress', 'Unknown')
                print(f"  - Connected Gmail account: {email_address}")
            except Exception as e:
                print(f"  - Could not retrieve email address: {e}")
                print(f"  - Note: Account is authenticated but email not retrieved")
    except Exception as e:
        print(f"  ✗ Error reading token file: {e}")
else:
    print(f"✗ Token file NOT FOUND at: {token_file.absolute()}")

if credentials_file.exists():
    print(f"✓ Credentials file found: {credentials_file.absolute()}")
else:
    print(f"✗ Credentials file NOT FOUND at: {credentials_file.absolute()}")
    # Check nested path
    nested_path = Path("mini project/credentials.json")
    if nested_path.exists():
        print(f"  → Found at nested path: {nested_path.absolute()}")

print()

# Check Outlook SMTP connection
print("2. OUTLOOK SMTP CONNECTION (for sending OTP emails)")
print("-" * 60)
smtp_username = os.getenv("SMTP_USERNAME")
smtp_password = os.getenv("SMTP_PASSWORD")
smtp_host = os.getenv("SMTP_HOST", "smtp.office365.com")
smtp_port = os.getenv("SMTP_PORT", "587")

if smtp_username:
    print(f"✓ SMTP Username: {smtp_username}")
else:
    print("✗ SMTP_USERNAME not set in environment")

if smtp_password:
    print(f"✓ SMTP Password: {'*' * len(smtp_password)} (set)")
else:
    print("✗ SMTP_PASSWORD not set in environment")

print(f"  - SMTP Host: {smtp_host}")
print(f"  - SMTP Port: {smtp_port}")

print()

# Check Outlook Graph API connection
print("3. OUTLOOK/MICROSOFT GRAPH CONNECTION (for fetching emails)")
print("-" * 60)
outlook_client_id = os.getenv("OUTLOOK_CLIENT_ID")
outlook_tenant_id = os.getenv("OUTLOOK_TENANT_ID")

if outlook_client_id:
    print(f"✓ Outlook Client ID: {outlook_client_id[:20]}... (set)")
else:
    print("✗ OUTLOOK_CLIENT_ID not set in environment")

if outlook_tenant_id:
    print(f"✓ Outlook Tenant ID: {outlook_tenant_id}")
else:
    print("✗ OUTLOOK_TENANT_ID not set in environment")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print()
print("Gmail: Used for fetching emails and attachments")
print("  → Configured in: system/fetch_emails.py")
print("  → Token stored in: token.pickle")
print()
print("Outlook SMTP: Used for sending OTP emails")
print("  → Configured in: backend/app/config.py")
print("  → Uses environment variables: SMTP_USERNAME, SMTP_PASSWORD")
print()
print("Outlook Graph: Used for fetching emails via Microsoft Graph API")
print("  → Configured in: system/fetch_emails.py")
print("  → Uses environment variables: OUTLOOK_CLIENT_ID, OUTLOOK_TENANT_ID")
print()

