import logging
import math
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_PATH = BASE_DIR / "data" / "processed" / "topics_assigned.csv"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "influencers.csv"


def load_topic_posts() -> pd.DataFrame:
    logging.info("Loading topic posts from %s", INPUT_PATH)
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)

    required = [
        "post_id",
        "platform",
        "author_id",
        "author_name",
        "followers",
        "likes",
        "comments",
        "shares",
        "views",
        "topic_id",
        "created_at",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in topics_assigned.csv: {missing}")

    numeric_cols = ["followers", "likes", "comments", "shares", "views", "topic_id"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["author_name"] = df["author_name"].fillna("").astype(str)
    return df


def aggregate_by_creator(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Aggregating metrics by (platform, author_id)")
    grouped = (
        df.groupby(["platform", "author_id"], as_index=False)
        .agg(
            author_name=("author_name", "first"),
            followers=("followers", "max"),
            num_posts=("post_id", "count"),
            total_likes=("likes", "sum"),
            total_comments=("comments", "sum"),
            total_shares=("shares", "sum"),
            total_views=("views", "sum"),
        )
        .copy()
    )

    grouped["avg_likes"] = grouped["total_likes"] / grouped["num_posts"]
    grouped["avg_comments"] = grouped["total_comments"] / grouped["num_posts"]
    grouped["avg_shares"] = grouped["total_shares"] / grouped["num_posts"]
    grouped["avg_views"] = grouped["total_views"] / grouped["num_posts"]
    grouped["total_engagement"] = (
        grouped["total_likes"] + grouped["total_comments"] + grouped["total_shares"]
    )
    return grouped


def compute_scores(agg_df: pd.DataFrame, source_df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Computing engagement rates, influencer scores and top topics")

    def engagement_rate(row):
        if row["followers"] > 0 and row["num_posts"] > 0:
            return (row["total_engagement"] / (row["followers"] * row["num_posts"])) * 100
        return np.nan

    def influencer_score(row):
        if row["followers"] > 0 and pd.notna(row["engagement_rate"]):
            return row["engagement_rate"] * math.log10(1 + row["followers"])
        if row["num_posts"] > 0:
            return row["total_engagement"] / row["num_posts"]
        return 0.0

    agg_df = agg_df.copy()
    agg_df["engagement_rate"] = agg_df.apply(engagement_rate, axis=1)
    agg_df["influencer_score"] = agg_df.apply(influencer_score, axis=1)

    topic_counts = (
        source_df.groupby(["platform", "author_id", "topic_id"], as_index=False)
        .size()
        .rename(columns={"size": "topic_posts"})
    )
    topic_counts = topic_counts.sort_values(
        ["platform", "author_id", "topic_posts"], ascending=[True, True, False]
    )

    top_topics = (
        topic_counts.groupby(["platform", "author_id"])["topic_id"]
        .apply(lambda s: ",".join(str(int(v)) for v in s.head(3).tolist()))
        .reset_index(name="top_topics")
    )

    out = agg_df.merge(top_topics, on=["platform", "author_id"], how="left")
    out["top_topics"] = out["top_topics"].fillna("")
    return out


def save_influencers(df: pd.DataFrame) -> None:
    logging.info("Saving influencer scores to %s", OUTPUT_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "platform",
        "author_id",
        "author_name",
        "followers",
        "num_posts",
        "total_engagement",
        "engagement_rate",
        "influencer_score",
        "top_topics",
        "avg_likes",
        "avg_comments",
        "avg_shares",
        "avg_views",
    ]
    df[columns].sort_values("influencer_score", ascending=False).to_csv(
        OUTPUT_PATH, index=False, encoding="utf-8"
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    source_df = load_topic_posts()
    agg_df = aggregate_by_creator(source_df)
    scored_df = compute_scores(agg_df, source_df)
    save_influencers(scored_df)
    logging.info("Done. Saved %s creators.", len(scored_df))


if __name__ == "__main__":
    main()
