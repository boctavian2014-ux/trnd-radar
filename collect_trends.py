import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
import pandas as pd
import praw
import tweepy
from dotenv import load_dotenv
from tiktok_trends import get_tiktok_trends


ROMANIA_WOEID = 23424849
TOP_LIMIT = 10
TIMEZONE = "Europe/Bucharest"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
CHART_DIR = DATA_DIR / "charts"


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "scheduler.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_env() -> None:
    load_dotenv(BASE_DIR / ".env")


def missing_env_vars() -> list[str]:
    required = [
        "APIFY_TOKEN",
    ]
    return [name for name in required if not os.getenv(name)]


def fetch_twitter_trends() -> pd.DataFrame:
    auth = tweepy.OAuth1UserHandler(
        os.getenv("TWITTER_CONSUMER_KEY", ""),
        os.getenv("TWITTER_CONSUMER_SECRET", ""),
        os.getenv("TWITTER_ACCESS_TOKEN", ""),
        os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
    )
    api = tweepy.API(auth)
    trends = api.get_place_trends(ROMANIA_WOEID)[0]["trends"][:TOP_LIMIT]

    rows = []
    for idx, trend in enumerate(trends, start=1):
        rows.append(
            {
                "Rank": idx,
                "Source": "Twitter",
                "Title": trend.get("name", ""),
                "Popularity": trend.get("tweet_volume"),
                "Link": trend.get("url", ""),
            }
        )

    return pd.DataFrame(rows)


def twitter_credentials_present() -> bool:
    keys = [
        "TWITTER_CONSUMER_KEY",
        "TWITTER_CONSUMER_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    ]
    return all(os.getenv(key) for key in keys)


def reddit_credentials_present() -> bool:
    keys = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
    ]
    return all(os.getenv(key) for key in keys)


def fetch_reddit_hot() -> pd.DataFrame:
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        user_agent=os.getenv("REDDIT_USER_AGENT", ""),
    )

    rows = []
    for idx, post in enumerate(reddit.subreddit("all").hot(limit=TOP_LIMIT), start=1):
        rows.append(
            {
                "Rank": idx,
                "Source": "Reddit",
                "Title": post.title,
                "Popularity": int(post.score),
                "Link": f"https://reddit.com{post.permalink}",
            }
        )

    return pd.DataFrame(rows)


def fetch_tiktok_trends() -> pd.DataFrame:
    items = get_tiktok_trends(limit=TOP_LIMIT, region="RO")

    rows = []
    for idx, item in enumerate(items[:TOP_LIMIT], start=1):
        rows.append(
            {
                "Rank": idx,
                "Source": "TikTok",
                "Title": item.get("title") or "(fara titlu)",
                "Popularity": item.get("plays"),
                "Link": item.get("url") or "",
            }
        )

    return pd.DataFrame(rows)


def save_visualization(combined_df: pd.DataFrame, timestamp: str) -> Path:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    chart_df = (
        combined_df.copy()
        .assign(Popularity=lambda df: pd.to_numeric(df["Popularity"], errors="coerce").fillna(0))
        .sort_values("Popularity", ascending=False)
        .head(10)
    )

    plt.figure(figsize=(12, 6))
    bars = plt.barh(chart_df["Title"], chart_df["Popularity"], color="#1f77b4")
    plt.gca().invert_yaxis()
    plt.title("Top Social Trends (Twitter Romania + Reddit + TikTok)")
    plt.xlabel("Popularity (tweet volume / score / plays)")
    plt.tight_layout()

    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height() / 2, f" {int(width)}", va="center")

    output_path = CHART_DIR / f"top_trends_{timestamp}.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def save_outputs(combined_df: pd.DataFrame) -> tuple[Path, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(ZoneInfo(TIMEZONE))
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    csv_file = DATA_DIR / f"social_trends_{timestamp}.csv"
    latest_file = DATA_DIR / "social_trends_latest.csv"
    combined_df.to_csv(csv_file, index=False, encoding="utf-8")
    combined_df.to_csv(latest_file, index=False, encoding="utf-8")

    chart_file = save_visualization(combined_df, timestamp)
    return csv_file, chart_file


def main() -> int:
    setup_logging()
    load_env()

    missing = missing_env_vars()
    if missing:
        logging.error("Missing .env variables: %s", ", ".join(missing))
        return 1

    try:
        twitter_df = pd.DataFrame(columns=["Rank", "Source", "Title", "Popularity", "Link"])
        if twitter_credentials_present():
            try:
                twitter_df = fetch_twitter_trends()
            except Exception as exc:
                logging.warning("Twitter unavailable (fallback active): %s", exc)
        else:
            logging.info("Twitter credentials missing. Running with remaining sources only.")

        reddit_df = pd.DataFrame(columns=["Rank", "Source", "Title", "Popularity", "Link"])
        if reddit_credentials_present():
            try:
                reddit_df = fetch_reddit_hot()
            except Exception as exc:
                logging.warning("Reddit unavailable (fallback active): %s", exc)
        else:
            logging.info("Reddit credentials missing. Running with remaining sources only.")

        tiktok_df = fetch_tiktok_trends()
        combined_df = pd.concat([twitter_df, reddit_df, tiktok_df], ignore_index=True)
        csv_path, chart_path = save_outputs(combined_df)
        logging.info("Saved CSV: %s", csv_path)
        logging.info("Saved chart: %s", chart_path)
        logging.info(
            "Breakdown: Twitter=%s, Reddit=%s, TikTok=%s",
            len(twitter_df),
            len(reddit_df),
            len(tiktok_df),
        )
        logging.info("Collected %s records.", len(combined_df))
        return 0
    except Exception as exc:
        logging.exception("Daily collection failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
