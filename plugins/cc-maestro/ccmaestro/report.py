import json
import urllib.request
from . import config


def snapshot(rows):
    return {r["id"]: r["verdict"] for r in rows}


def diff(prev, cur):
    events = []
    for aid, verdict in cur.items():
        if verdict == "ok":
            continue
        if prev.get(aid) != verdict:
            events.append({"id": aid, "from": prev.get(aid), "to": verdict})
    return events


def record(event):
    f = config.STATE_DIR / "events.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "a") as fh:
        fh.write(json.dumps(event) + "\n")


def _urllib_poster(url, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5).close()


def post(url, event, poster=_urllib_poster):
    if not url:
        return False
    try:
        poster(url, event)
        return True
    except Exception:
        return False
