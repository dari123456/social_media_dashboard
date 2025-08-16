# backend/bots/step3_generation.py
import re
import json
from .clients import get_openai_client
from . import config

# Initialize the OpenAI client once for this module
openai_client = get_openai_client()

def _load_prompt(file_path):
    """Helper function to load a prompt from the configured directory."""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"ERROR: Prompt file not found at {file_path}")
        raise

def generate_post_for_platform(conclusion_text: str, summary_text: str, platform_name: str) -> dict:
    """
    Generates platform-specific social media content (post text and hashtags).

    Args:
        conclusion_text: The specific conclusion to focus on.
        summary_text: The full summary for context.
        platform_name: The target platform ('facebook', 'instagram', or 'twitter').

    Returns:
        A dictionary containing the 'text' and 'hashtags' for the post.
    """
    print(f"--- Starting Step 3a: Generating content for {platform_name.capitalize()} ---")
    
    prompt_templates = {
        'facebook': config.PROMPT_FACEBOOK_POST,
        'instagram': config.PROMPT_INSTAGRAM_CAPTION,
        'twitter': config.PROMPT_TWITTER_TWEET,
    }

    if platform_name not in prompt_templates:
        raise ValueError(f"Invalid platform name: {platform_name}")

    # Load the correct prompt template
    system_prompt = _load_prompt(prompt_templates[platform_name])
    
    # Format the user prompt with the specific context
    user_prompt = f"CONTEXTUAL SUMMARY:\n{summary_text}\n\nCONCLUSION TO FOCUS ON:\n{conclusion_text}"

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        content = response.choices[0].message.content.strip()

        # Robustly parse the AI's response for different tag formats
        text_match = re.search(r"\[(?:POST_TEXT|CAPTION|TWEET)\](.*?)\[/(?:POST_TEXT|CAPTION|TWEET)\]", content, re.DOTALL | re.IGNORECASE)
        hashtags_match = re.search(r"\[HASHTAGS\](.*?)\[/HASHTAGS\]", content, re.DOTALL | re.IGNORECASE)

        post_text = text_match.group(1).strip() if text_match else "Error: Could not parse post text."
        hashtags = hashtags_match.group(1).strip() if hashtags_match else "#error"
        
        print(f"  - Generated Text: {post_text[:80]}...")
        return {'text': post_text, 'hashtags': hashtags}

    except Exception as e:
        print(f"ERROR: OpenAI call failed during content generation. Error: {e}")
        return {'text': 'Error: AI generation failed.', 'hashtags': '#error'}

def find_best_image_for_post(post_text: str, image_urls: list) -> str | None:
    """
    Analyzes a list of images against a post text and returns the URL of the best match.

    Args:
        post_text: The text of the social media post.
        image_urls: A list of public URLs for the images to be analyzed.

    Returns:
        The URL of the best matching image, or None if no suitable match is found.
    """
    if not image_urls:
        print("  - No images provided for matching. Skipping.")
        return None
        
    print(f"--- Starting Step 3b: Matching best image for post: '{post_text[:50]}...' ---")
    
    system_prompt = _load_prompt(config.PROMPT_IMAGE_MATCHING)
    best_image = None
    highest_score = -1

    for url in image_urls:
        print(f"  - Analyzing image: {url.split('/')[-1][:40]}...")
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Social Media Post Text: \"{post_text}\""},
                            {"type": "image_url", "image_url": {"url": url}},
                        ],
                    }
                ],
                max_tokens=80, # Increased for safety with JSON
            )
            response_text = response.choices[0].message.content.strip()
            
            score = 0
            try:
                data = json.loads(response_text)
                score = int(data.get('score', 0))
            except (json.JSONDecodeError, KeyError):
                # Fallback to regex if JSON fails
                match = re.search(r'\d+', response_text)
                if match:
                    score = int(match.group(0))

            print(f"    - Score: {score}")
            if score > highest_score:
                highest_score = score
                best_image = url
        
        except Exception as e:
            # This handles content policy violations or other API errors
            print(f"  - WARNING: Could not analyze image {url}. Error: {e}")
            continue
            
    if highest_score < 5: # Set a minimum threshold for a match to be considered valid
        print("  - No sufficiently relevant image found (highest score < 5).")
        return None
        
    print(f"  - Best image found: {best_image.split('/')[-1]} (Score: {highest_score})")
    return best_image