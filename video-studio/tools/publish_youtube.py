"""Upload an episode to YouTube (private by default, so you review before it goes live).

One-time, on your own computer (opens a browser to sign in):
    python tools/publish_youtube.py --auth client_secret.json
    -> prints a refresh token; store it with the client id/secret as environment secrets
       YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

Every episode:
    python tools/publish_youtube.py episodes/ep01-never-sleep            # private upload
    python tools/publish_youtube.py episodes/ep01-never-sleep --publish-at 2026-10-20T15:00:00Z

Reads episodes/<ep>/metadata.json: {"video", "title", "description", "tags", "thumbnail", "category_id"}
Needs: pip install google-api-python-client google-auth-oauthlib
"""
import argparse, json, os, sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]


def auth(client_secret):
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES).run_local_server(port=0)
    print("YT_REFRESH_TOKEN =", creds.refresh_token)


def service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"], scopes=SCOPES)
    return build("youtube", "v3", credentials=creds)


def upload(ep, publish_at):
    from googleapiclient.http import MediaFileUpload
    meta = json.load(open(os.path.join(ep, "metadata.json")))
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if publish_at:
        status["publishAt"] = publish_at          # YouTube flips it public at this time
    body = {"snippet": {"title": meta["title"][:100], "description": meta["description"],
                        "tags": meta.get("tags", []), "categoryId": meta.get("category_id", "27")},
            "status": status}
    yt = service()
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(os.path.join(ep, meta["video"]), chunksize=8 << 20, resumable=True))
    res = None
    while res is None:
        st, res = req.next_chunk()
        if st:
            print(f"uploading {int(st.progress() * 100)}%")
    vid = res["id"]
    if meta.get("thumbnail"):
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(os.path.join(ep, meta["thumbnail"]))).execute()
    print(f"done: https://youtu.be/{vid}  (private{' until ' + publish_at if publish_at else ''})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?")
    ap.add_argument("--auth", metavar="CLIENT_SECRET_JSON")
    ap.add_argument("--publish-at", help="RFC3339 UTC time to go public, e.g. 2026-10-20T15:00:00Z")
    a = ap.parse_args()
    if a.auth:
        auth(a.auth)
    elif a.episode:
        upload(a.episode, a.publish_at)
    else:
        sys.exit(ap.format_usage())
