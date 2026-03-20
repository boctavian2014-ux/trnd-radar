import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
DEFAULT_ACTOR_IDS = [
    "thuannguyenit~tiktok-trending-scraper",
    "clockworks~tiktok-scraper",
]


def get_actor_ids() -> list[str]:
    configured = os.getenv("APIFY_ACTOR_IDS", "").strip()
    if configured:
        return [actor_id.strip() for actor_id in configured.split(",") if actor_id.strip()]
    single = os.getenv("APIFY_ACTOR_ID", "").strip()
    if single:
        return [single]
    return DEFAULT_ACTOR_IDS


def _raise_with_details(prefix: str, response: requests.Response) -> None:
    details = response.text[:500].replace("\n", " ")
    raise RuntimeError(f"{prefix} HTTP {response.status_code}: {details}")


def _csv_env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


def run_actor(actor_id: str, input_body: dict):
    if not APIFY_TOKEN:
        raise RuntimeError("Lipseste APIFY_TOKEN in .env")

    start_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_TOKEN}"
    res = requests.post(start_url, json=input_body, timeout=30)
    if not res.ok:
        _raise_with_details(f"Run actor failed for {actor_id}", res)
    data = res.json()
    run_id = data["data"]["id"]

    # Poll pana cand actorul termina.
    while True:
        run_res = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            params={"token": APIFY_TOKEN},
            timeout=30,
        )
        run_res.raise_for_status()
        run_data = run_res.json()["data"]
        if run_data["status"] in ["SUCCEEDED", "FAILED", "ABORTED", "TIMING_OUT"]:
            break
        time.sleep(3)

    if run_data["status"] != "SUCCEEDED":
        raise RuntimeError(f"Actor failed with status: {run_data['status']}")

    # Ia dataset-ul cu rezultate.
    dataset_id = run_data["defaultDatasetId"]
    items_res = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        params={"token": APIFY_TOKEN, "clean": "true", "format": "json"},
        timeout=60,
    )
    items_res.raise_for_status()
    return items_res.json()


def get_tiktok_trends(limit: int = 20, region: str = "RO"):
    """
    Returneaza o lista de trenduri TikTok (video / hashtag) pentru regiunea selectata.
    """
    last_error = None
    items = None
    for actor_id in get_actor_ids():
        # clockworks~tiktok-scraper requires at least one seed key:
        # postURLs, hashtags, searchQueries, music references or profiles.
        search_queries = _csv_env_list(
            "APIFY_TIKTOK_SEARCH_QUERIES",
            [f"{region} trends", f"{region} viral", "fyp"],
        )
        hashtags = _csv_env_list(
            "APIFY_TIKTOK_HASHTAGS",
            [region.lower(), "viral", "fyp"],
        )
        profiles = _csv_env_list(
            "APIFY_TIKTOK_PROFILES",
            ["https://www.tiktok.com/@tiktok"],
        )

        if "clockworks~tiktok-scraper" in actor_id:
            input_candidates = [
                {"searchQueries": search_queries, "maxItems": limit},
                {"hashtags": hashtags, "maxItems": limit},
                {"profiles": profiles, "maxItems": limit},
                {"searchQueries": search_queries, "resultsPerPage": limit},
                {"hashtags": hashtags, "resultsPerPage": limit},
            ]
        else:
            input_candidates = [
                {"maxItems": limit, "region": region},
                {"limit": limit, "region": region},
                {"maxItems": limit, "country": region},
                {"resultsPerPage": limit, "country": region},
                {"maxItems": limit},
                {"limit": limit},
                {},
            ]

        for input_body in input_candidates:
            try:
                items = run_actor(actor_id, input_body)
                break
            except Exception as exc:
                last_error = exc
        if items is not None:
            break

    if items is None:
        raise RuntimeError(
            "Nu am putut rula niciun actor Apify pentru TikTok. "
            f"Ultima eroare: {last_error}. "
            "Seteaza APIFY_ACTOR_ID sau APIFY_ACTOR_IDS in .env cu un actor valid pentru contul tau."
        )

    # Normalizeaza rezultatul in campuri utile pentru dashboard.
    results = []
    for item in items:
        results.append(
            {
                "id": item.get("id") or item.get("videoId"),
                "title": item.get("title") or item.get("desc"),
                "author": item.get("authorName") or item.get("author", {}).get("uniqueId"),
                "likes": item.get("diggCount") or item.get("stats", {}).get("diggCount"),
                "plays": item.get("playCount") or item.get("stats", {}).get("playCount"),
                "shares": item.get("shareCount") or item.get("stats", {}).get("shareCount"),
                "comments": item.get("commentCount") or item.get("stats", {}).get("commentCount"),
                "url": item.get("url") or item.get("webVideoUrl"),
                "cover": item.get("cover") or item.get("video", {}).get("cover"),
                "hashtags": [h.get("name") for h in item.get("hashtags", [])] if item.get("hashtags") else None,
            }
        )
    return results


if __name__ == "__main__":
    trends = get_tiktok_trends(limit=10, region="RO")
    for trend in trends:
        print(f"{trend['title']} | @{trend['author']} | {trend['plays']} views | {trend['url']}")
