import json
import urllib.request
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = "https://rdskmehttiglnhexiduy.supabase.co"
SUPABASE_KEY = "sb_publishable_SJzSUlutr_arJSykFISk7w_fqklQWIk"
YOUTUBE_API_KEY = "AIzaSyALVfY4lmhw5UwlOxzXyauDnoVTCwUbPE8"

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
    
    response = supabase.table("short_views").select("*").execute()
    rows = response.data
    
    if not rows:
        print("No videos found in short_views.")
        return

    for row in rows:
        record_id = row.get("id")
        video_id = row.get("videoid")
        print(f"\nChecking Video ID: {video_id}")
        
        live_views = get_youtube_views(video_id, YOUTUBE_API_KEY)
        
        if live_views is not None:
            print(f"-> Live YouTube Views: {live_views}")
            supabase.table("short_views").update({
                "videocount": live_views,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", record_id).execute()
            print("-> Updated Supabase successfully!")
        else:
            print("-> Could not fetch views.")

if __name__ == "__main__":
    main()
