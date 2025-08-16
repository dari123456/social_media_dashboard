# backend/bots/clients.py

import os
import json
import gspread
from google.oauth2.service_account import Credentials

try:
    import streamlit as st  # noqa: F401
    _HAS_STREAMLIT = True
except Exception:
    _HAS_STREAMLIT = False

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _client_from_info(info: dict):
    creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    return gspread.authorize(creds)

def _client_from_file(path: str):
    creds = Credentials.from_service_account_file(path, scopes=_SCOPES)
    return gspread.authorize(creds)

def get_gspread_client():
    """Return an authorized gspread client."""
    if _HAS_STREAMLIT:
        try:
            if "gcp_service_account" in st.secrets:
                info = dict(st.secrets["gcp_service_account"])
                return _client_from_info(info)
        except Exception:
            pass

    json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_env:
        info = json.loads(json_env)
        return _client_from_info(info)

    path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if os.path.exists(path):
        return _client_from_file(path)

    raise RuntimeError("Google credentials not found.")

# --- NEW: helper functions used in step1_ingestion ---

import openai
from google.cloud import storage

def get_openai_client():
    """Return an OpenAI client using the API key in secrets/env."""
    api_key = None
    if _HAS_STREAMLIT and "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    elif os.getenv("OPENAI_API_KEY"):
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in secrets or environment.")

    # Configure OpenAI globally
    openai.api_key = api_key
    return openai

def get_gcs_client():
    """Return a Google Cloud Storage client."""
    # For Streamlit secrets
    if _HAS_STREAMLIT and "gcp_service_account" in st.secrets:
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"])
        )
        return storage.Client(credentials=creds, project=creds.project_id)

    # Else fallback to default credentials (if running locally with GOOGLE_APPLICATION_CREDENTIALS)
    return storage.Client()
