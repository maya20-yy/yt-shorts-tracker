import os
import json
import urllib.request
from datetime import datetime, timezone
from supabase import create_client, Client

# Securely pull credentials from environment variables / GitHub Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_youtube_views(video_id, yt_api_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={yt_api_key}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            items = data.get("items", [])
            if items:
                return int(items[0]["statistics"]["viewCount"])
    except Exception as e:
        print(f"Error fetching YouTube views: {e}")
    return None

def main():
    print("--- Starting YouTube Shorts View Tracker ---")
    
    # 1. Fetch only the active list of video IDs from Supabase
    response = supabase.table("tracked_videos").select("videoid").execute()
    video_rows = response.data
    
    if not video_rows:
        print("No videos found in tracked_videos table.")
        return

    # 2. Loop through them cleanly (exactly 1 insert per video per run)
    for row in video_rows:
        video_id = row.get("videoid")
        print(f"\nChecking Video ID: {video_id}")
        
        live_views = get_youtube_views(video_id, YOUTUBE_API_KEY)
        
        if live_views is not None:
            print(f"-> Live YouTube Views: {live_views}")
            
            # --- SAVES EXACTLY ONE NEW ROW PER VIDEO ID ---
            supabase.table("short_views").insert({
                "videoid": video_id,
                "videocount": live_views,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            
            print("-> Inserted new historical row into Supabase successfully!")
        else:
            print("-> Could not fetch views.")

if __name__ == "__main__":
    main()
