import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import praw
import streamlit as st
import tweepy
from dotenv import load_dotenv


ROMANIA_WOEID = 23424849
TOP_LIMIT = 10
BASE_DIR = Path(__file__).resolve().parent


def load_env() -> None:
    load_dotenv(BASE_DIR / ".env")


def missing_env_vars() -> list[str]:
    required = []
    return [name for name in required if not os.getenv(name)]


@st.cache_data(ttl=300, show_spinner=False)
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


@st.cache_data(ttl=300, show_spinner=False)
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


def render_dashboard() -> None:
    st.set_page_config(page_title="Social Trends Dashboard", layout="wide")
    load_env()

    missing = missing_env_vars()
    if missing:
        st.error("Lipsesc variabile din .env:")
        st.code("\n".join(missing))
        st.info("Copiaza `.env.example` in `.env` si completeaza valorile.")
        st.stop()

    # --- Sidebar: explicatii si actiuni (populat dupa ce avem combined_df) ---
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # --- Titlu principal ---
    st.title("Social Trends Dashboard")
    st.markdown("Prezentare generala: **top trenduri** din Twitter (Romania), Reddit si TikTok.")

    # --- Incarcare date Twitter + Reddit ---
    twitter_df = pd.DataFrame(columns=["Rank", "Source", "Title", "Popularity", "Link"])
    if twitter_credentials_present():
        try:
            twitter_df = fetch_twitter_trends()
        except Exception as exc:
            st.warning(f"Twitter indisponibil (fallback activ): {exc}")
    else:
        st.info("Twitter: credentials lipsesc; afisez doar celelalte surse.")

    reddit_df = pd.DataFrame(columns=["Rank", "Source", "Title", "Popularity", "Link"])
    if reddit_credentials_present():
        try:
            reddit_df = fetch_reddit_hot()
        except Exception as exc:
            st.warning(f"Reddit indisponibil (fallback activ): {exc}")
    else:
        st.info("Reddit: credentials lipsesc; afisez doar celelalte surse.")

    combined_df = pd.concat([twitter_df, reddit_df], ignore_index=True)

    # --- Sidebar: explicatii si actiuni ---
    with st.sidebar:
        st.header("Ajutor")
        st.markdown("**Coloane:** Rank, Title, Popularity, Link. Surse: Twitter (RO), Reddit, TikTok.")
        st.divider()
        st.markdown("**MiroFish** (swarm / predicții): integrat prin API mai jos. Pornește backend-ul din **Desktop**: `cd C:\\Users\\octav\\Desktop\\MiroFish` apoi `npm run dev`.")
        st.divider()
        st.caption(f"Actualizat: {now_utc}")
        if not combined_df.empty:
            csv_data = combined_df.to_csv(index=False).encode("utf-8")
            st.download_button("Descarca CSV (Twitter + Reddit)", data=csv_data, file_name="social_trends.csv", mime="text/csv")

    # --- Rezumat rapid (metrici) ---
    n_tw = len(twitter_df)
    n_rd = len(reddit_df)
    st.subheader("Rezumat surse")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Twitter (Romania)", f"{n_tw} trenduri", "WOEID 23424849")
    with c2:
        st.metric("Reddit r/all", f"{n_rd} trenduri", "hot posts")
    with c3:
        st.metric("Total afisat", f"{len(combined_df)} randuri", "combinat")

    # --- Tabele pe surse ---
    st.subheader("Trenduri pe sursa")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Twitter – Romania**")
        if twitter_df.empty:
            st.caption("Niciun rezultat (sursa oprita sau indisponibila).")
        else:
            st.dataframe(twitter_df, use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**Reddit – r/all hot**")
        if reddit_df.empty:
            st.caption("Niciun rezultat (sursa oprita sau indisponibila).")
        else:
            st.dataframe(reddit_df, use_container_width=True, hide_index=True)

    # --- Tabel combinat (opțional, in expander) ---
    with st.expander("Tabel combinat"):
        if combined_df.empty:
            st.info("Niciun rezultat. Completeaza .env (Twitter/Reddit) sau incarca TikTok mai jos.")
        else:
            st.dataframe(combined_df, use_container_width=True, hide_index=True)
        st.caption("CSV: buton in bara stanga.")


if __name__ == "__main__":
    render_dashboard()
