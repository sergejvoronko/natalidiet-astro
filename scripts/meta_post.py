# Hourly cron (under uv: --with pillow). Posts to the natalidiet Facebook Page and Instagram:
#  - any recipe or blog post not seen before, once its page is live (within the hour of deploy);
#  - from 10:00 local, one older post a day, never-shared first, then the longest ago shared.
# Instagram only takes an image by public URL, so the 4:5 crop is uploaded to the Page as an
# unpublished photo and its CDN URL is handed to Instagram. The Page token does not expire.
import datetime
import io
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
N8N = Path.home() / "stacks/n8n"
STATE = N8N / "drafts/natalidiet/meta_state.json"
GRAPH = "https://graph.facebook.com/v19.0/"
RESHARE_HOUR = 10
TAG_SKIP = re.compile(r"^(under-\d+-kcal|pillar-guide|makeover|healthy-techniques)$")
# Cloudflare answers 403 to the default Python User-Agent.
UA = {"User-Agent": "natalidiet-meta-post/1.0"}


def creds():
    return json.loads((N8N / "secrets/meta_page_tokens.json").read_text())["Natalidiet"]


def graph(path, token, data=None, files=None):
    if files:
        boundary = uuid.uuid4().hex
        body = b""
        for k, v in data.items():
            body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for k, (name, blob) in files.items():
            body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{name}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode() + blob + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    elif data is not None:
        body, headers = urllib.parse.urlencode(data).encode(), {}
    else:
        body, headers = None, {}
    sep = "&" if "?" in path else "?"
    req = urllib.request.Request(f"{GRAPH}{path}{sep}access_token={token}", body, headers)
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, TimeoutError):
            # Connection-level failures (TLS handshake timeouts seen in practice) happen before
            # Meta has the request, so a retry cannot double-post.
            if attempt == 2:
                raise
            time.sleep(20)


def posts():
    for kind in ("recipes", "blog"):
        for path in (ROOT / "src/content" / kind).glob("*.md*"):
            fm = path.read_text().split("---")[1]
            get = lambda k: (m := re.search(rf'^{k}:\s*"?(.*?)"?\s*$', fm, re.M)) and m.group(1)
            if get("draft") == "true":
                continue
            tags = re.search(r"^tags:\s*\[(.*?)\]", fm, re.M)
            slug = re.sub(r"\.mdx?$", "", path.name)
            yield {
                "kind": kind,
                "slug": slug,
                "date": get("publishDate") or get("pubDate") or "",
                "title": get("title"),
                "description": get("description") or "",
                "image": get("image"),
                "cuisine": get("cuisine"),
                "calories": get("calories"),
                "time": get("totalTime"),
                "servings": get("servings"),
                "tags": [t.strip().strip('"') for t in tags.group(1).split(",")] if tags else [],
                "link": f"https://natalidiet.eu/{kind}/{slug}/",
            }


def live(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=30).status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def hashtags(p):
    tags = [p["cuisine"] and f"{p['cuisine']}food"] + [t for t in p["tags"] if not TAG_SKIP.match(t)]
    tags += ["healthyrecipes", "easterneuropeanfood", "natalidiet"]
    seen, out = set(), []
    for t in tags:
        t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
        t = re.sub(r"[^a-z0-9]", "", t.lower())
        if t and t not in seen:
            seen.add(t)
            out.append("#" + t)
    return " ".join(out[:12])


def caption(p):
    stats = ", ".join(
        x for x in (
            p["calories"] and f"{p['calories']} kcal per serving",
            p["time"] and f"{p['time']} minutes",
            p["servings"] and f"serves {p['servings']}",
        ) if x
    )
    lines = [p["title"], "", p["description"]]
    if stats:
        lines += ["", stats[0].upper() + stats[1:] + "."]
    lines += ["", "Full " + ("recipe" if p["kind"] == "recipes" else "guide") + ": link in bio.", "", hashtags(p)]
    return "\n".join(lines)


def ig_image(p):
    im = Image.open(ROOT / "public" / p["image"].lstrip("/")).convert("RGB")
    w, h = 1080, 1350
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    buf = io.BytesIO()
    im.crop((l, t, l + w, t + h)).save(buf, "JPEG", quality=90)
    return buf.getvalue()


def share(p, c):
    tok = c["page_token"]
    fb = graph(c["page_id"] + "/feed", tok, {"message": p["description"], "link": p["link"]})
    photo = graph(c["page_id"] + "/photos", tok, {"published": "false", "temporary": "true"},
                  {"source": (p["slug"] + ".jpg", ig_image(p))})
    url = graph(photo["id"] + "?fields=images", tok)["images"][0]["source"]
    container = graph(c["ig_user_id"] + "/media", tok, {"image_url": url, "caption": caption(p)})
    for _ in range(20):
        if graph(container["id"] + "?fields=status_code", tok).get("status_code") == "FINISHED":
            break
        time.sleep(3)
    ig = graph(c["ig_user_id"] + "/media_publish", tok, {"creation_id": container["id"]})
    return fb["id"], ig["id"]


def main():
    now = datetime.datetime.now()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    all_posts = list(posts())
    if "shared" not in state:
        # First run: everything already published is backlog for re-sharing, not "new".
        state = {"shared": {p["slug"]: None for p in all_posts}, "reshared_on": now.date().isoformat()}
        state["shared"]["light-czech-segedinsky-gulas"] = now.date().isoformat()
    new = [p for p in all_posts if p["slug"] not in state["shared"]]
    if new:
        p = max(new, key=lambda p: p["date"])
        if not live(p["link"]):
            print(now.isoformat(timespec="seconds"), "waiting for deploy", p["slug"])
            STATE.write_text(json.dumps(state))
            return
        reason = "new"
    elif now.hour >= RESHARE_HOUR and state["reshared_on"] != now.date().isoformat():
        backlog = [p for p in all_posts if p["image"]]
        never = sorted((p for p in backlog if not state["shared"].get(p["slug"])), key=lambda p: p["date"], reverse=True)
        p = never[0] if never else min(backlog, key=lambda p: state["shared"][p["slug"]])
        state["reshared_on"] = now.date().isoformat()
        reason = "reshare"
    else:
        STATE.write_text(json.dumps(state))
        return
    # Marked before posting: a failure after the Facebook post must not repost it every hour.
    state["shared"][p["slug"]] = now.date().isoformat()
    STATE.write_text(json.dumps(state))
    try:
        fb, ig = share(p, creds())
    except urllib.error.HTTPError as e:
        print(now.isoformat(timespec="seconds"), e.code, p["slug"], e.read()[:300].decode())
        sys.exit(1)
    print(now.isoformat(timespec="seconds"), reason, p["kind"], p["slug"], "fb", fb, "ig", ig)


if __name__ == "__main__":
    main()
