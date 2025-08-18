# backend/bots/clients.py

import os
import json
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import storage
from google.oauth2 import service_account

try:
    import streamlit as st  # noqa: F401
    _HAS_STREAMLIT = True
except Exception:
    _HAS_STREAMLIT = False


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ----------------------------
# Google Sheets / gspread
# ----------------------------
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
        except Exception as e:
            print(f"WARNING: could not init gspread from st.secrets: {e}")

    json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_env:
        info = json.loads(json_env)
        return _client_from_info(info)

    path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if os.path.exists(path):
        return _client_from_file(path)

    raise RuntimeError("Google credentials not found for gspread client.")


# ----------------------------
# OpenAI
# ----------------------------
import openai

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


# ----------------------------
# Google Cloud Storage
# ----------------------------
def get_gcs_client():
    """Return a Google Cloud Storage client using secrets/env."""
    creds = None
    project = None

    # Prefer Streamlit secrets
    if _HAS_STREAMLIT and "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        project = creds.project_id

    # Fallback: GOOGLE_APPLICATION_CREDENTIALS file (local dev)
    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        creds = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )
        project = creds.project_id

    # Default (tries ADC, may fail on Streamlit Cloud)
    if creds:
        return storage.Client(credentials=creds, project=project)
    else:
        return storage.Client()
    
    # ----------------------------
# Twitter (Tweepy)
# ----------------------------
def get_tweepy_clients():
    """
    Returns (api_v1, client_v2) using credentials from Streamlit secrets or env.
    Requires:
      TWITTER_API_KEY
      TWITTER_API_SECRET
      TWITTER_ACCESS_TOKEN
      TWITTER_ACCESS_TOKEN_SECRET
    """
    import tweepy
    # Read from secrets first, then env
    def _get(name):
        if _HAS_STREAMLIT and name in st.secrets:
            return st.secrets[name]
        v = os.getenv(name)
        if v:
            return v
        raise RuntimeError(f"{name} not found in secrets or environment.")

    api_key = _get("TWITTER_API_KEY")
    api_secret = _get("TWITTER_API_SECRET")
    access_token = _get("TWITTER_ACCESS_TOKEN")
    access_secret = _get("TWITTER_ACCESS_TOKEN_SECRET")

    # v1.1 (for media upload / classic posting)
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api_v1 = tweepy.API(auth)

    # v2 (some endpoints require Client)
    client_v2 = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
        wait_on_rate_limit=True,
    )

    return api_v1, client_v2

