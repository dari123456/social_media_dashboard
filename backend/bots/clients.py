# backend/bots/clients.py
import os
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import storage
import tweepy
from . import config

# --- OpenAI Client ---
def get_openai_client():
    """Initializes and returns the OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in the .env file.")
    return OpenAI(api_key=api_key)

# --- Google Sheets Client ---
def get_gspread_client():
    """Initializes and returns the Google Sheets client."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CREDENTIALS_PATH, scope)
    return gspread.authorize(creds)

# --- Google Cloud Storage Client ---
def get_gcs_client():
    """Initializes and returns the Google Cloud Storage client."""
    return storage.Client.from_service_account_json(config.GOOGLE_CREDENTIALS_PATH)

# --- Twitter API Clients (v1 for media uploads, v2 for posting) ---
def get_tweepy_clients():
    """Initializes and returns both Tweepy v1 and v2 clients."""
    consumer_key = os.getenv("TWITTER_API_KEY")
    consumer_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise ValueError("One or more Twitter API keys are missing from the .env file.")

    # v2 client for creating tweets
    client_v2 = tweepy.Client(
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        access_token=access_token, access_token_secret=access_token_secret
    )
    
    # v1 API for media uploads
    auth = tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret, access_token, access_token_secret
    )
    api_v1 = tweepy.API(auth)
    
    return api_v1, client_v2