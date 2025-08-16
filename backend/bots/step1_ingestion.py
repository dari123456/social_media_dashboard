# backend/bots/step1_ingestion.py
import requests
from bs4 import BeautifulSoup
import json
import io
import uuid
import re
from urllib.parse import urljoin

# Use direct imports to avoid circular dependency issues
from .clients import get_openai_client, get_gcs_client
from . import config

# Initialize clients once
openai_client = get_openai_client()
gcs_client = get_gcs_client()

def _load_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        return f.read().strip()

def _get_text_from_url(url):
    """Scrapes the title and main text content from a URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else soup.title.string.strip()
        text = "\n".join([p.get_text(strip=True) for p in soup.find_all('p')])
        return title, text
    except Exception as e:
        print(f"ERROR: Could not fetch or parse text from URL {url}. Error: {e}")
        raise

def _get_summary_from_text(text):
    """Generates a summary and conclusions using OpenAI."""
    prompt = _load_prompt(config.PROMPT_SUMMARIZE)
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": text}]
    )
    return response.choices[0].message.content.strip()

def _is_image_a_chart(image_url):
    """Uses GPT-4o with JSON mode for reliable chart detection."""
    prompt = _load_prompt(config.PROMPT_IS_CHART)
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_url}}]}
            ],
            max_tokens=50,
        )
        result = json.loads(response.choices[0].message.content)
        is_chart = result.get("is_chart", False)
        confidence = result.get("confidence", 0.0)
        return is_chart and confidence >= 0.7
    except Exception:
        return False

def _upload_image_to_gcs(image_url, article_name):
    """Downloads an image from a URL and uploads it to GCS, returning the public URL."""
    try:
        response = requests.get(image_url, stream=True, timeout=15)
        response.raise_for_status()
        
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', article_name)
        filename = f"{safe_name[:50]}_{uuid.uuid4().hex[:8]}.jpg"

        bucket = gcs_client.bucket(config.GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_file(io.BytesIO(response.content), content_type='image/jpeg')
        return blob.public_url
    except Exception as e:
        print(f"ERROR: Failed to download or upload image {image_url}. Error: {e}")
        return None

def process_article_url(url: str):
    """
    The main function for Step 1.
    Takes a URL and performs all ingestion and processing tasks.
    Returns a dictionary with all the extracted data.
    """
    print(f"--- Starting Step 1: Ingestion for URL: {url} ---")
    
    title, article_text = _get_text_from_url(url)
    print(f"Title found: {title}")
    
    summary = _get_summary_from_text(article_text)
    print("AI Summary generated.")
    
    image_urls = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'lxml')
        img_tags = soup.find_all('img')

        for img in img_tags:
            src = img.get('data-src') or img.get('src')
            if not src or src.startswith('data:image'):
                continue
            
            full_img_url = urljoin(url, src)
            if _is_image_a_chart(full_img_url):
                print(f"Chart detected. Uploading: {full_img_url}")
                public_url = _upload_image_to_gcs(full_img_url, title)
                if public_url:
                    image_urls.append(public_url)
    except Exception as e:
        print(f"WARNING: Could not process images for {url}. Error: {e}")

    print(f"Found and uploaded {len(image_urls)} relevant images.")
    
    return {
        "article_url": url,
        "title": title,
        "summary": summary,
        "image_urls": image_urls
    }