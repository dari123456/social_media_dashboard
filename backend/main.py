# backend/main.py
import re
from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List
import pandas as pd

from .bots import orchestrator, config, clients

# --- API Data Models ---
class StartWorkflowRequest(BaseModel):
    article_url: HttpUrl
    platforms: List[str]
    approver_emails: str
class PostActionRequest(BaseModel):
    platform: str
    post_id: str

# --- FastAPI Application ---
app = FastAPI(title="Social Media Admin Dashboard API")

# ... (The first 5 endpoints are the same) ...
@app.get("/")
def read_root(): return {"status": "Social Media API is running!"}
@app.post("/api/v1/workflow/start")
def start_ingestion_workflow(request: StartWorkflowRequest, background_tasks: BackgroundTasks):
    """
    Starts the full ingestion-to-generation workflow for a new article.
    """
    valid_platforms = ["facebook", "instagram", "twitter"]
    for p in request.platforms:
        if p not in valid_platforms:
            raise HTTPException(status_code=400, detail=f"Invalid platform '{p}' provided.")
            
    # Convert comma/semicolon separated string of emails into a clean list
    emails = [email.strip() for email in re.split(r'[;,]', request.approver_emails) if email.strip()]
    
    print(f"API: Received request to start workflow for URL: {request.article_url} with emails: {emails}")
    
    # --- THE FIX IS HERE ---
    # We now pass the 'emails' list to the orchestrator.
    background_tasks.add_task(
        orchestrator.run_ingestion_to_generation,
        article_url=str(request.article_url),
        platforms=request.platforms,
        approver_emails=emails # This argument was missing
    )
    
    return {
        "status": "success",
        "message": f"Workflow started in the background for {request.article_url}."
    }

@app.post("/api/v1/workflow/schedule")
def schedule_approved_posts(background_tasks: BackgroundTasks):
    background_tasks.add_task(orchestrator.run_scheduling_for_all_platforms)
    return {"status": "success", "message": "Scheduling has started."}
@app.post("/api/v1/workflow/publish")
def publish_due_posts(background_tasks: BackgroundTasks):
    background_tasks.add_task(orchestrator.run_publishing_for_all_platforms)
    return {"status": "success", "message": "Publishing run has started."}
@app.get("/api/v1/posts/awaiting-approval")
def get_posts_awaiting_approval():
    all_posts = []
    gspread_client = clients.get_gspread_client()
    for platform_name, platform_cfg in config.PLATFORMS.items():
        try:
            worksheet = gspread_client.open(platform_cfg.sheet_name).worksheet(platform_cfg.steps['step3'])
            records = worksheet.get_all_records()
            if not records or 'Approved_by_human' not in records[0]: continue
            awaiting_df = pd.DataFrame(records).query("Approved_by_human == ''")
            for _, post in awaiting_df.iterrows():
                post_data = post.to_dict(); post_data['platform'] = platform_name
                all_posts.append(post_data)
        except Exception: continue
    return all_posts
@app.get("/api/v1/posts/scheduled")
def get_scheduled_posts():
    all_scheduled = []
    gspread_client = clients.get_gspread_client()
    for platform_name, platform_cfg in config.PLATFORMS.items():
        try:
            worksheet = gspread_client.open(platform_cfg.sheet_name).worksheet(platform_cfg.steps['step4'])
            records = worksheet.get_all_records()
            if not records: continue
            for post in records:
                post['platform'] = platform_name; all_scheduled.append(post)
        except Exception: continue
    if all_scheduled: all_scheduled.sort(key=lambda x: x.get('Scheduled_Time', ''))
    return all_scheduled
@app.get("/api/v1/posts/posted")
def get_posted_posts():
    all_posted = []
    gspread_client = clients.get_gspread_client()
    for platform_name, platform_cfg in config.PLATFORMS.items():
        try:
            worksheet = gspread_client.open(platform_cfg.sheet_name).worksheet(platform_cfg.steps['step4'])
            records = worksheet.get_all_records()
            if not records: continue
            for post in records:
                if post.get('Posted_Status', '') == 'Posted':
                    post['platform'] = platform_name; all_posted.append(post)
        except Exception: continue
    if all_posted: all_posted.sort(key=lambda x: x.get('Scheduled_Time', ''), reverse=True)
    return all_posted


# --- THIS IS THE UPGRADED FUNCTION ---
def _update_approval_status(request: PostActionRequest, status: str):
    """Helper function to update the sheet with 'yes' or 'no'."""
    gspread_client = clients.get_gspread_client()
    platform_cfg = config.PLATFORMS.get(request.platform)
    if not platform_cfg:
        raise HTTPException(status_code=404, detail="Platform not found")
    try:
        spreadsheet = gspread_client.open(platform_cfg.sheet_name)
        worksheet = spreadsheet.worksheet(platform_cfg.steps['step3'])
        cell = worksheet.find(request.post_id)
        if not cell:
            raise HTTPException(status_code=404, detail=f"Post with ID {request.post_id} not found.")
        
        # --- ROBUST COLUMN FINDER ---
        headers = worksheet.row_values(1)
        approval_col_index = -1
        # Loop through headers, strip whitespace, and compare in lowercase
        for i, header in enumerate(headers):
            if header.strip().lower() == 'approved_by_human':
                approval_col_index = i + 1 # Add 1 because gspread is 1-indexed
                break
        
        if approval_col_index == -1:
            raise HTTPException(status_code=500, detail="Could not find 'Approved_by_human' column in the sheet.")
        # --- END OF ROBUST FINDER ---
            
        worksheet.update_cell(cell.row, approval_col_index, status)
        return {"status": "success", "message": f"Post {request.post_id} on {request.platform} status set to '{status}'."}
    except Exception as e:
        # Pass along the specific error from gspread or our own logic
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/api/v1/posts/approve")
def approve_post(request: PostActionRequest): return _update_approval_status(request, "yes")
@app.post("/api/v1/posts/reject")
def reject_post(request: PostActionRequest): return _update_approval_status(request, "no")