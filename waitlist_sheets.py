"""
Google Sheets integration for FinPilot waitlist.

Uses gspread with service account credentials stored in Streamlit secrets.
Falls back to local JSON if Sheets is unavailable.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

# Local fallback file
WAITLIST_FILE = "data/waitlist.json"

# Sheet config
SHEET_HEADERS = ["email", "name", "source", "timestamp", "language"]


def _get_gspread_client():
    """Create gspread client from Streamlit secrets."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        # Streamlit secrets stores the service account JSON under [gsheets]
        creds_dict = dict(st.secrets["gsheets"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        logger.warning(f"Google Sheets bağlantısı kurulamadı: {e}")
        return None


def _get_worksheet():
    """Get the waitlist worksheet. Creates headers if sheet is empty."""
    try:
        client = _get_gspread_client()
        if client is None:
            return None

        spreadsheet_url = st.secrets.get("gsheets", {}).get("spreadsheet_url", "")
        spreadsheet_key = st.secrets.get("gsheets", {}).get("spreadsheet_key", "")

        if spreadsheet_key:
            sh = client.open_by_key(spreadsheet_key)
        elif spreadsheet_url:
            sh = client.open_by_url(spreadsheet_url)
        else:
            # Try opening by name
            sh = client.open("FinPilot Waitlist")

        worksheet = sh.sheet1

        # If sheet is empty, add headers
        if not worksheet.get_all_values():
            worksheet.append_row(SHEET_HEADERS)

        return worksheet
    except Exception as e:
        logger.warning(f"Worksheet alınamadı: {e}")
        return None


# ─── LOCAL JSON FALLBACK ───────────────────────────────────

def _save_local(email, name, source, language):
    """Save to local JSON as fallback."""
    try:
        Path("data").mkdir(exist_ok=True)
        waitlist = []
        if Path(WAITLIST_FILE).exists():
            with open(WAITLIST_FILE, "r") as f:
                waitlist = json.load(f)
        if any(w["email"].lower() == email.lower() for w in waitlist):
            return False
        waitlist.append({
            "email": email.lower(),
            "name": name,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "language": language,
        })
        with open(WAITLIST_FILE, "w") as f:
            json.dump(waitlist, f, indent=2)
        return True
    except Exception:
        return False


def _count_local():
    """Count from local JSON."""
    try:
        if Path(WAITLIST_FILE).exists():
            with open(WAITLIST_FILE, "r") as f:
                return len(json.load(f))
    except Exception:
        pass
    return 0


# ─── PUBLIC API ────────────────────────────────────────────

def save_to_waitlist(email, name="", source="demo"):
    """
    Save email to waitlist.
    Tries Google Sheets first, falls back to local JSON.
    Returns True if new signup, False if duplicate or error.
    """
    language = st.session_state.get("language", "en")

    # Try Google Sheets
    worksheet = _get_worksheet()
    if worksheet is not None:
        try:
            # Check for duplicate
            existing_emails = worksheet.col_values(1)  # Column A = emails
            if email.lower() in [e.lower() for e in existing_emails]:
                return False

            # Append new row
            row = [
                email.lower(),
                name,
                source,
                datetime.now().isoformat(),
                language,
            ]
            worksheet.append_row(row, value_input_option="USER_ENTERED")
            logger.info(f"Waitlist kaydı Google Sheets'e eklendi: {email}")
            return True
        except Exception as e:
            logger.warning(f"Google Sheets yazma hatası: {e}")
            # Fall through to local save

    # Fallback: local JSON
    logger.info("Google Sheets kullanılamıyor, local JSON'a yazılıyor")
    return _save_local(email, name, source, language)


def get_waitlist_count():
    """
    Get current waitlist count.
    Tries Google Sheets first, falls back to local JSON.
    """
    worksheet = _get_worksheet()
    if worksheet is not None:
        try:
            rows = worksheet.get_all_values()
            # Subtract 1 for header row
            count = max(0, len(rows) - 1)
            return count
        except Exception as e:
            logger.warning(f"Google Sheets okuma hatası: {e}")

    return _count_local()


def migrate_json_to_sheets():
    """
    One-time migration: copy existing waitlist.json entries to Google Sheets.
    Runs on app startup. Skips duplicates. Safe to call multiple times.
    """
    if not Path(WAITLIST_FILE).exists():
        return 0

    try:
        with open(WAITLIST_FILE, "r") as f:
            local_data = json.load(f)
    except Exception:
        return 0

    if not local_data:
        return 0

    worksheet = _get_worksheet()
    if worksheet is None:
        logger.warning("Migration: Google Sheets bağlantısı yok, atlaniyor")
        return 0

    try:
        existing_emails = [e.lower() for e in worksheet.col_values(1)]
        migrated = 0

        for entry in local_data:
            email = entry.get("email", "").lower()
            if not email or email in existing_emails:
                continue

            row = [
                email,
                entry.get("name", ""),
                entry.get("source", ""),
                entry.get("timestamp", ""),
                entry.get("language", ""),
            ]
            worksheet.append_row(row, value_input_option="USER_ENTERED")
            existing_emails.append(email)
            migrated += 1

        if migrated > 0:
            logger.info(f"Migration: {migrated} kayıt JSON'dan Sheets'e aktarıldı")
        return migrated
    except Exception as e:
        logger.warning(f"Migration hatası: {e}")
        return 0
