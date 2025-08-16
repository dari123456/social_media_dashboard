# backend/bots/config.py
import os


# Load variables from your .env file
PROMPT_FILES_DIR = os.path.join(os.path.dirname(__file__), '..', 'prompt_files')

# --- File Paths ---
PROMPT_FILES_DIR = os.path.join(os.path.dirname(__file__), '..', 'prompt_files')
GOOGLE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')

# --- Google Cloud Storage ---
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

# --- Platform-Specific Settings ---
class PlatformConfig:
    def __init__(self, sheet_name, steps):
        self.sheet_name = sheet_name
        self.steps = {f"step{i+1}": name for i, name in enumerate(steps)}

PLATFORMS = {
    "facebook": PlatformConfig(
        sheet_name="Facebook_Workflow",
        steps=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"]
    ),
    "instagram": PlatformConfig(
        sheet_name="Instagram_Workflow",
        steps=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"]
    ),
    "twitter": PlatformConfig(
        sheet_name="Google_Workflow",
        steps=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"]
    )
}

# --- Prompt File Names ---
PROMPT_SUMMARIZE = os.path.join(PROMPT_FILES_DIR, "summarize_and_extract_conclusions_prompt.txt")
PROMPT_IS_CHART = os.path.join(PROMPT_FILES_DIR, "is_the_image_a_chart_prompt.txt")
PROMPT_IMAGE_MATCHING = os.path.join(PROMPT_FILES_DIR, "image_matching_prompt.txt")
PROMPT_INSTAGRAM_CAPTION = os.path.join(PROMPT_FILES_DIR, "instagram_prompt.txt")
PROMPT_FACEBOOK_POST = os.path.join(PROMPT_FILES_DIR, "facebook_prompt.txt")
PROMPT_TWITTER_TWEET = os.path.join(PROMPT_FILES_DIR, "prompt_that_creates_tweet_text.txt")

# --- Scheduling ---
TIMEZONE = "Europe/Berlin"