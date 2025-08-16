# backend/bots/clients.py
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# Optional: Streamlit may not exist in local scripts
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
    """
    Returns an authorized gspread client.

    Resolution order:
      1) Streamlit Secrets: st.secrets["gcp_service_account"]  (Streamlit Cloud)
      2) Env var JSON:      GOOGLE_CREDENTIALS_JSON            (stringified JSON)
      3) File path:         GOOGLE_CREDENTIALS_PATH or 'credentials.json'
    """
    # 1) Streamlit Secrets (best for Streamlit Cloud)
    if _HAS_STREAMLIT:
        try:
            if "gcp_service_account" in st.secrets:
                info = dict(st.secrets["gcp_service_account"])
                return _client_from_info(info)
        except Exception:
            # fall through to other methods
            pass

    # 2) JSON from environment variable (useful in containers/CI)
    json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_env:
        info = json.loads(json_env)
        return _client_from_info(info)

    # 3) Credentials file path (useful for local dev)
    path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if os.path.exists(path):
        return _client_from_file(path)

    raise RuntimeError(
        "Google credentials not found. Provide one of: "
        "st.secrets['gcp_service_account'] (Streamlit), "
        "GOOGLE_CREDENTIALS_JSON (env), or GOOGLE_CREDENTIALS_PATH/credentials.json (file)."
    )
