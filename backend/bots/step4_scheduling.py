# backend/bots/step4_scheduling.py
import pandas as pd
from datetime import datetime, time, timedelta
import pytz
from .clients import get_gspread_client
from . import config

# Initialize the Google Sheets client
gspread_client = get_gspread_client()

def create_posting_schedule(platform_name: str):
    """
    Reads approved posts from 'Step 3', creates a smart schedule,
    and saves it to the 'Step 4' worksheet for a given platform.

    Args:
        platform_name: The platform to schedule posts for ('facebook', 'instagram', 'twitter').
    """
    print(f"--- Starting Step 4: Creating schedule for {platform_name.capitalize()} ---")
    
    try:
        platform_config = config.PLATFORMS[platform_name]
        spreadsheet = gspread_client.open(platform_config.sheet_name)
        worksheet_step3 = spreadsheet.worksheet(platform_config.steps['step3'])
        worksheet_step4 = spreadsheet.worksheet(platform_config.steps['step4'])
    except Exception as e:
        print(f"ERROR: Could not access Google Sheets for {platform_name}. Error: {e}")
        raise

    # Load approved but unscheduled posts from Step 3
    records_step3 = worksheet_step3.get_all_records()
    if not records_step3:
        print("  - 'Step 3' is empty. Nothing to schedule.")
        return
    
    df = pd.DataFrame(records_step3)
    df['Requires_human_approval'] = df['Requires_human_approval'].astype(str).str.lower().str.strip()
    df['Approved_by_human'] = df['Approved_by_human'].astype(str).str.lower().str.strip()

    approved_df = df[
        (df['Requires_human_approval'].isin(['no', ''])) | (df['Approved_by_human'] == 'yes')
    ].copy()

    if approved_df.empty:
        print("  - No approved posts found in 'Step 3'. Clearing schedule.")
        worksheet_step4.clear()
        # Ensure headers are set even when empty
        headers = list(df.columns) + ['Scheduled_Time', 'Posted_Status', 'Post_Link']
        worksheet_step4.update([headers])
        return

    print(f"  - Found {len(approved_df)} approved posts to schedule.")

    # Unified Scheduling Algorithm
    tz = pytz.timezone(config.TIMEZONE)
    now = datetime.now(tz)
    
    # Define posting window
    start_time = time(9, 0)
    end_time = time(21, 0)
    interval = timedelta(hours=4) # You can adjust this or make it platform-specific in config.py
    
    last_scheduled_time = now
    
    # Find the next valid starting slot
    if now.time() > end_time:
        last_scheduled_time = (now + timedelta(days=1)).replace(hour=start_time.hour, minute=start_time.minute, second=0)
    elif now.time() < start_time:
        last_scheduled_time = now.replace(hour=start_time.hour, minute=start_time.minute, second=0)

    scheduled_times = []
    for _ in range(len(approved_df)):
        # Ensure the current slot is not outside the posting window
        if last_scheduled_time.time() > end_time:
            last_scheduled_time = (last_scheduled_time + timedelta(days=1)).replace(hour=start_time.hour, minute=start_time.minute)
        
        scheduled_times.append(last_scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z'))
        last_scheduled_time += interval

    approved_df['Scheduled_Time'] = scheduled_times
    approved_df['Posted_Status'] = ''
    approved_df['Post_Link'] = ''

    # Save the new schedule to the Step 4 sheet, overwriting the old one
    print("  - Writing final schedule to 'Step 4' sheet...")
    worksheet_step4.clear()
    worksheet_step4.update([approved_df.columns.values.tolist()] + approved_df.fillna('').values.tolist())
    print(f"  - Successfully scheduled {len(approved_df)} posts.")