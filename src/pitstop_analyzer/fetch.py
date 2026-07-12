from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_FEED_URL = (
    "https://cf.nascar.com/cacher/live/series_2/5314/live-pit-data.json"
)


def fetch_json(url: str, output_path: str | Path) -> Path:
    """Download a NASCAR JSON feed and save a validated JSON array locally."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "nascar-pit-stop-analyzer/1.0"})

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not download valid JSON from {url}: {exc}") from exc

    if not isinstance(payload, list):
        raise ValueError("Expected the feed root to be a JSON array.")

    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination
