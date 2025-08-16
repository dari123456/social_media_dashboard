# backend/bots/step5_publishing.py
import os
import requests
import time
import tempfile
from .clients import get_tweepy_clients

# --- Platform-Specific Publishing Functions ---

def _post_to_facebook(page_id, access_token, image_url, caption):
    """Posts an image and caption to a Facebook Page."""
    post_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    payload = {'url': image_url, 'caption': caption, 'access_token': access_token}
    try:
        response = requests.post(post_url, data=payload)
        response.raise_for_status()
        res_json = response.json()
        post_id = res_json.get('post_id')
        permalink = f"https://www.facebook.com/{post_id}" if post_id else "Link not available"
        return True, permalink
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Facebook post failed. Response: {e.response.text if e.response else e}")
        return False, str(e)

def _post_to_instagram(account_id, access_token, image_url, caption):
    """Posts an image and caption to an Instagram Business Account."""
    base_url = "https://graph.facebook.com/v19.0"
    try:
        # Step 1: Create media container
        container_url = f"{base_url}/{account_id}/media"
        container_payload = {'image_url': image_url, 'caption': caption, 'access_token': access_token}
        container_res = requests.post(container_url, data=container_payload)
        container_res.raise_for_status()
        container_id = container_res.json()['id']
        
        # Step 2: Poll for container readiness
        for _ in range(10): # Poll for ~50 seconds
            status_res = requests.get(f"{base_url}/{container_id}?fields=status_code&access_token={access_token}")
            if status_res.json().get('status_code') == 'FINISHED':
                break
            time.sleep(5)
        else:
            return False, "Instagram media container did not finish processing in time."
            
        # Step 3: Publish the container
        publish_url = f"{base_url}/{account_id}/media_publish"
        publish_payload = {'creation_id': container_id, 'access_token': access_token}
        publish_res = requests.post(publish_url, data=publish_payload)
        publish_res.raise_for_status()
        
        permalink_id = publish_res.json().get('id')
        permalink_res = requests.get(f"{base_url}/{permalink_id}?fields=permalink&access_token={access_token}")
        permalink = permalink_res.json().get('permalink', 'Link not available')
        return True, permalink
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Instagram post failed. Response: {e.response.text if e.response else e}")
        return False, str(e)

def _post_to_twitter(image_url, text):
    """Posts a text and optional image to Twitter."""
    api_v1, client_v2 = get_tweepy_clients()
    media_id = None
    
    # Twitter requires downloading the image locally before uploading
    if image_url:
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(response.content)
                temp_path = tmp_file.name
            
            media = api_v1.media_upload(filename=temp_path)
            media_id = media.media_id_string
            os.remove(temp_path) # Clean up the temp file
        except Exception as e:
            print(f"WARNING: Twitter image upload failed. Posting as text-only. Error: {e}")

    try:
        media_ids = [media_id] if media_id else None
        tweet_response = client_v2.create_tweet(text=text, media_ids=media_ids)
        tweet_id = tweet_response.data['id']
        permalink = f"https://twitter.com/anyuser/status/{tweet_id}"
        return True, permalink
    except Exception as e:
        print(f"ERROR: Twitter post failed. Error: {e}")
        return False, str(e)

# --- Main Dispatcher Function ---

def publish_post(platform_name: str, post_data: dict) -> tuple[bool, str]:
    """
    Publishes content to the specified platform by dispatching to the correct function.

    Args:
        platform_name: 'facebook', 'instagram', or 'twitter'.
        post_data: A dictionary-like object (e.g., a Pandas Series)
                   containing all necessary data for the post.

    Returns:
        A tuple of (success_boolean, result_string), where the string is
        either the permalink on success or an error message on failure.
    """
    print(f"--- Starting Step 5: Publishing to {platform_name.capitalize()} ---")
    
    # Construct the full post content
    text = post_data.get('Facebook_Post_Text') or post_data.get('Instagram_Caption') or post_data.get('Tweet')
    hashtags = post_data.get('Facebook_Hashtags') or post_data.get('Instagram_Hashtags', '')
    article_url = post_data.get('article_url', '')
    image_url = post_data.get('Matched_Image_Path', '')
    
    # Format the caption with hashtags and a link (if applicable)
    full_caption = f"{text}\n\n{hashtags}"
    if platform_name == 'facebook':
        full_caption += f"\n\nRead the full article here:\n{article_url}"

    try:
        if platform_name == 'facebook':
            return _post_to_facebook(
                page_id=os.getenv("FB_PAGE_ID"),
                access_token=os.getenv("FB_ACCESS_TOKEN"),
                image_url=image_url,
                caption=full_caption
            )
        elif platform_name == 'instagram':
            return _post_to_instagram(
                account_id=os.getenv("IG_ACCOUNT_ID"),
                access_token=os.getenv("IG_ACCESS_TOKEN"),
                image_url=image_url,
                caption=full_caption
            )
        elif platform_name == 'twitter':
            return _post_to_twitter(
                image_url=image_url,
                text=text # Twitter has a character limit, so we don't add hashtags/URL here by default
            )
        else:
            return False, "Invalid platform name provided."
    except Exception as e:
        return False, f"An unexpected error occurred in the dispatcher: {e}"