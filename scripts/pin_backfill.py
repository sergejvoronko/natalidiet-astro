# Hourly cron (under uv, see make_pins.py). Each run: refreshes the Pinterest token when it
# is 20+ days old (it expires at 30), then pins the newest recipe or blog post that has no pin,
# at most PER_DAY a day. New posts are newest, so they are pinned within the hour; the rest is
# backfill. The queue is recomputed from the boards each run, so pins made by hand drop out.
import base64
import datetime
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_pins

PER_DAY = 3
ROOT = Path(__file__).resolve().parent.parent
N8N = Path.home() / "stacks/n8n"
TOKEN = N8N / "drafts/natalidiet/pinterest_token.json"
STATE = N8N / "drafts/natalidiet/pin_backfill.json"
BOARDS = {"recipes": "1095852590520469213", "blog": "1095852590520469538"}
API = "https://api.pinterest.com/v5"


def env(key):
    for line in (N8N / ".env").read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def token():
    t = json.loads(TOKEN.read_text())
    age = now() - datetime.datetime.fromisoformat(t["obtained_at"].replace("Z", "+00:00"))
    if age < datetime.timedelta(days=20):
        return t["access_token"]
    basic = base64.b64encode(f"{env('PINTEREST_APP_ID')}:{env('PINTEREST_APP_SECRET')}".encode()).decode()
    req = urllib.request.Request(
        API + "/oauth/token",
        urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": t["refresh_token"]}).encode(),
        {"Authorization": "Basic " + basic, "Content-Type": "application/x-www-form-urlencoded"},
    )
    r = json.load(urllib.request.urlopen(req, timeout=60))
    t.update(access_token=r["access_token"], obtained_at=now().isoformat())
    if r.get("refresh_token"):
        t["refresh_token"] = r["refresh_token"]
    TOKEN.write_text(json.dumps(t))
    print(now().isoformat(timespec="seconds"), "token refreshed")
    return t["access_token"]


def call(path, tok, body=None):
    req = urllib.request.Request(
        API + path,
        json.dumps(body).encode() if body else None,
        {"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=60))


def pinned(tok):
    links = set()
    for board in BOARDS.values():
        bookmark = None
        while True:
            d = call(f"/boards/{board}/pins?page_size=100" + (f"&bookmark={bookmark}" if bookmark else ""), tok)
            links |= {p["link"].split("?")[0].rstrip("/") for p in d["items"] if p.get("link")}
            bookmark = d.get("bookmark")
            if not bookmark:
                break
    return links


def posts():
    for kind in BOARDS:
        for path in (ROOT / "src/content" / kind).glob("*.md*"):
            fm = path.read_text().split("---")[1]
            get = lambda k: (m := re.search(rf'^{k}:\s*"?(.*?)"?\s*$', fm, re.M)) and m.group(1)
            if get("draft") == "true":
                continue
            slug = re.sub(r"\.mdx?$", "", path.name)
            yield {
                "kind": kind,
                "slug": slug,
                "date": get("publishDate") or get("pubDate") or "",
                "title": get("title"),
                "description": get("description") or "",
                "alt": get("imageAlt") or get("title"),
                "link": f"https://natalidiet.eu/{kind}/{slug}",
            }


def main():
    today = datetime.date.today().isoformat()
    try:
        state = json.loads(STATE.read_text())
    except (OSError, ValueError):
        state = {}
    if state.get("date") != today:
        state = {"date": today, "count": 0}
    tok = token()
    if state["count"] >= PER_DAY:
        return
    done = pinned(tok)
    queue = sorted((p for p in posts() if p["link"] not in done), key=lambda p: p["date"], reverse=True)
    if not queue:
        return
    p = queue[0]
    image = make_pins.OUT / f"{p['slug']}.jpg"
    if not image.exists():
        image = make_pins.make(p["kind"], p["slug"])
    body = {
        "board_id": BOARDS[p["kind"]],
        "title": p["title"][:100],
        "description": p["description"][:500],
        "link": p["link"] + "/",
        "alt_text": p["alt"][:500],
        "media_source": {
            "source_type": "image_base64",
            "content_type": "image/jpeg",
            "data": base64.b64encode(image.read_bytes()).decode(),
        },
    }
    stamp = now().isoformat(timespec="seconds")
    try:
        pin = call("/pins", tok, body)
    except urllib.error.HTTPError as e:
        print(stamp, e.code, p["slug"], e.read()[:300].decode())
        sys.exit(1)
    state["count"] += 1
    STATE.write_text(json.dumps(state))
    print(stamp, "pinned", p["kind"], p["slug"], pin["id"], f"{len(queue) - 1} left")


if __name__ == "__main__":
    main()
