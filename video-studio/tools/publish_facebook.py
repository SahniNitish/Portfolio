"""Post an episode to a Facebook Page, as a normal video or as a Reel (9:16, 3-90s).

    python tools/publish_facebook.py episodes/ep01-never-sleep              # video, unpublished draft
    python tools/publish_facebook.py episodes/ep01-never-sleep --live       # video, posted now
    python tools/publish_facebook.py episodes/ep01-never-sleep --reel       # uses metadata "reel_video"

Env secrets: FB_PAGE_ID, FB_PAGE_TOKEN (a Page access token with pages_manage_posts,
pages_read_engagement and publish_video). Reads the same metadata.json as publish_youtube.py.
Needs: pip install requests
"""
import argparse, json, os
import requests

GRAPH = "v23.0"   # bump to the current Graph API version if Meta deprecates this one


def post_video(path, meta, live):
    with open(path, "rb") as f:
        r = requests.post(f"https://graph-video.facebook.com/{GRAPH}/{os.environ['FB_PAGE_ID']}/videos",
                          data={"access_token": os.environ["FB_PAGE_TOKEN"], "title": meta["title"],
                                "description": meta["description"], "published": str(live).lower()},
                          files={"source": f}, timeout=600)
    r.raise_for_status()
    print("video id:", r.json()["id"], "(live)" if live else "(unpublished draft: publish it from Meta Business Suite)")


def post_reel(path, meta, live):
    page, tok = os.environ["FB_PAGE_ID"], os.environ["FB_PAGE_TOKEN"]
    url = f"https://graph.facebook.com/{GRAPH}/{page}/video_reels"
    start = requests.post(url, data={"upload_phase": "start", "access_token": tok}, timeout=60)
    start.raise_for_status()
    vid = start.json()["video_id"]
    with open(path, "rb") as f:
        up = requests.post(f"https://rupload.facebook.com/video-upload/{GRAPH}/{vid}", data=f, timeout=600,
                           headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(os.path.getsize(path))})
    up.raise_for_status()
    fin = requests.post(url, timeout=60, data={"upload_phase": "finish", "video_id": vid, "access_token": tok,
                                               "video_state": "PUBLISHED" if live else "DRAFT",
                                               "description": meta.get("reel_caption", meta["description"])})
    fin.raise_for_status()
    print("reel id:", vid, "(live)" if live else "(draft)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--reel", action="store_true")
    ap.add_argument("--live", action="store_true", help="post publicly now instead of as a draft")
    a = ap.parse_args()
    meta = json.load(open(os.path.join(a.episode, "metadata.json")))
    if a.reel:
        post_reel(os.path.join(a.episode, meta["reel_video"]), meta, a.live)
    else:
        post_video(os.path.join(a.episode, meta["video"]), meta, a.live)
