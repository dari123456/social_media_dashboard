# backend/bots/orchestrator.py
import uuid
import json
import pandas as pd
from . import config, clients
from . import step1_ingestion, step2_decomposition, step3_generation, step4_scheduling, email_sender

# Initialize the Google Sheets client once for the orchestrator
gspread_client = clients.get_gspread_client()

def run_ingestion_to_generation(article_url: str, platforms: list[str], approver_emails: list[str]):
    """
    Runs the full workflow and sends a notification email at the end.
    """
    article_data = step1_ingestion.process_article_url(article_url)
    conclusions = step2_decomposition.extract_conclusions_from_summary(article_data['summary'])
    if not conclusions:
        print("ORCHESTRATOR: No conclusions found. Workflow for this URL will stop.")
        return

    print(f"\nORCHESTRATOR: Found {len(conclusions)} conclusions. Processing each...")

    for conclusion_text in conclusions:
        # ... (the existing for loop logic for generating and saving posts is the same) ...
        base_data = {
            "post_id": str(uuid.uuid4()), "article_url": article_data['article_url'],
            "Name": article_data['title'], "Summary": article_data['summary'],
            "Conclusion": conclusion_text, "Image_Paths": json.dumps(article_data['image_urls']),
            "Requires_human_approval": "yes", "Approved_by_human": "",
            # We can also store the emails with each post for later use (e.g., post-live notifications)
            "Approver_Emails": ";".join(approver_emails) 
        }
        for platform_name in platforms:
            row_to_add = base_data.copy()
            post_content = step3_generation.generate_post_for_platform(conclusion_text, article_data['summary'], platform_name)
            # ... (rest of the loop logic)
            if platform_name == 'facebook':
                row_to_add['Facebook_Post_Text'] = post_content['text']; row_to_add['Facebook_Hashtags'] = post_content['hashtags']
            elif platform_name == 'instagram':
                row_to_add['Instagram_Caption'] = post_content['text']; row_to_add['Instagram_Hashtags'] = post_content['hashtags']
            elif platform_name == 'twitter':
                row_to_add['Tweet'] = post_content['text']
            best_image = step3_generation.find_best_image_for_post(post_content['text'], article_data['image_urls'])
            row_to_add["Matched_Image_Path"] = best_image if best_image else ""
            try:
                platform_config = config.PLATFORMS[platform_name]
                spreadsheet = gspread_client.open(platform_config.sheet_name)
                worksheet_step3 = spreadsheet.worksheet(platform_config.steps['step3'])
                headers = worksheet_step3.row_values(1)
                ordered_values = [row_to_add.get(h, "") for h in headers]
                worksheet_step3.append_row(ordered_values, value_input_option='USER_ENTERED')
                print(f"ORCHESTRATOR: -> Successfully added post to '{platform_name.capitalize()}' Step 3 sheet.")
            except Exception as e:
                print(f"ORCHESTRATOR: -> ERROR! Failed to write to Google Sheet for {platform_name}. Error: {e}")

    # --- SEND NOTIFICATION EMAIL AT THE END ---
    if approver_emails:
        print("\nORCHESTRATOR: All posts generated. Sending approval notification email...")
        email_sender.send_approval_notification(
            article_title=article_data['title'],
            recipient_emails=approver_emails
        )

    print("\nORCHESTRATOR: All conclusions processed. Workflow complete.")

# --- THIS IS THE CORRECTED FUNCTION NAME ---
def run_scheduling_for_all_platforms():
    """
    Runs the scheduling logic (Step 4) for all configured platforms.
    """
    print("\nORCHESTRATOR: Starting scheduling run for all platforms...")
    for platform_name in config.PLATFORMS:
        try:
            step4_scheduling.create_posting_schedule(platform_name)
        except Exception as e:
            print(f"ORCHESTRATOR: -> ERROR! Failed to run scheduling for {platform_name}. Error: {e}")


def run_publishing_for_all_platforms():
    """
    Checks the schedule for all platforms and publishes any post that is due.
    """
    print("\nORCHESTRATOR: Starting publishing run for all platforms...")
    from . import step5_publishing
    from datetime import datetime
    import pytz

    target_tz = pytz.timezone(config.TIMEZONE)
    now_tz = datetime.now(target_tz)
    print(f"Current time is {now_tz.strftime('%Y-%m-%d %H:%M:%S')}")

    for platform_name in config.PLATFORMS:
        print(f"--- Checking schedule for {platform_name.capitalize()} ---")
        try:
            platform_config = config.PLATFORMS[platform_name]
            spreadsheet = gspread_client.open(platform_config.sheet_name)
            worksheet_schedule = spreadsheet.worksheet(platform_config.steps['step4'])
            all_posts_df = pd.DataFrame(worksheet_schedule.get_all_records())
            if all_posts_df.empty:
                print("  - Schedule is empty. Nothing to post.")
                continue
            for idx, post in all_posts_df.iterrows():
                if post.get("Posted_Status", "").strip() == "":
                    try:
                        scheduled_time_str = " ".join(post.get("Scheduled_Time").split(" ")[0:2])
                        naive_dt = pd.to_datetime(scheduled_time_str).tz_localize(None)
                        scheduled_time = target_tz.localize(naive_dt)
                        if now_tz >= scheduled_time:
                            print(f"  - POSTING DUE: Row {idx + 2}, '{post.get('Name', 'N/A')[:40]}...'")
                            success, result = step5_publishing.publish_post(platform_name, post)
                            all_posts_df.loc[idx, 'Posted_Status'] = "Posted" if success else f"Error: {result}"
                            all_posts_df.loc[idx, 'Post_Link'] = result if success else ""
                            worksheet_schedule.update([all_posts_df.columns.values.tolist()] + all_posts_df.fillna('').values.tolist())
                            print(f"  - Result logged to sheet. Status: {all_posts_df.loc[idx, 'Posted_Status']}")
                            break
                    except Exception as e:
                        print(f"  - ERROR processing row {idx + 2}. Error: {e}")
        except Exception as e:
            print(f"ORCHESTRATOR: -> ERROR! Failed to run publishing for {platform_name}. Error: {e}")