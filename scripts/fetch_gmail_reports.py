#!/usr/bin/env python3
"""
Fetch CSV report attachments from Gmail via IMAP.
Saves to data/live/ for the dashboard.

Setup:
  1. Enable 2-Step Verification: https://myaccount.google.com/security
  2. Create App Password: https://myaccount.google.com/apppasswords
     - Select app: "Mail" → generate → copy the 16-char password
  3. Add to .env:
     GMAIL_USER=perezofir@gmail.com
     GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

Usage:
  python3 scripts/fetch_gmail_reports.py
"""

import imaplib
import email
import os
import csv
import io
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Load .env
ENV_PATH = Path(__file__).parent.parent / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

GMAIL_USER = os.environ.get("GMAIL_USER", "perezofir@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
DATA_DIR = Path(__file__).parent.parent / "data" / "live"

# Map email subjects → output filename
SUBJECT_MAP = {
    "Google Ads Daily Report": "google_ads.csv",
    "GA4 Daily Report": "ga4.csv",
}


def fetch_reports():
    if not GMAIL_APP_PASSWORD:
        print("ERROR: Set GMAIL_APP_PASSWORD in .env")
        print("  1. Go to https://myaccount.google.com/apppasswords")
        print("  2. Create an App Password for 'Mail'")
        print("  3. Add to .env: GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to Gmail as {GMAIL_USER}...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select("inbox")

    for subject_key, filename in SUBJECT_MAP.items():
        print(f"\nSearching for: {subject_key}")
        status, data = mail.search(None, f'(SUBJECT "{subject_key}")')
        if status != "OK" or not data[0]:
            print(f"  No emails found")
            continue

        # Get the most recent email (last ID)
        email_ids = data[0].split()
        latest_id = email_ids[-1]
        print(f"  Found {len(email_ids)} emails, using latest")

        status, msg_data = mail.fetch(latest_id, "(RFC822)")
        if status != "OK":
            print(f"  Failed to fetch email")
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        msg_date = msg.get("Date", "unknown")
        print(f"  Date: {msg_date}")

        # Extract CSV attachment
        found = False
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                att_filename = part.get_filename()
                if att_filename and att_filename.endswith(".csv"):
                    csv_data = part.get_payload(decode=True)
                    out_path = DATA_DIR / filename
                    out_path.write_bytes(csv_data)
                    lines = csv_data.decode("utf-8").strip().count("\n")
                    print(f"  Saved: {out_path} ({lines} rows)")
                    found = True
                    break
        if not found:
            print(f"  No CSV attachment found")

    mail.logout()
    print("\nDone!")


if __name__ == "__main__":
    fetch_reports()
