import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction import text as sklearn_text
from sklearn.feature_extraction.text import TfidfVectorizer


BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_PATH = BASE_DIR / "data" / "processed" / "corpus.csv"
ASSIGNED_PATH = BASE_DIR / "data" / "processed" / "topics_assigned.csv"
TERMS_PATH = BASE_DIR / "data" / "processed" / "topic_terms.csv"
N_CLUSTERS = 20
TOP_TERMS = 15
INFLUENCER_COLS = ["author_name", "followers", "likes", "comments", "shares", "views"]

ROMANIAN_STOPWORDS = {
    "si",
    "sau",
    "in",
    "la",
    "cu",
    "de",
    "din",
    "pe",
    "un",
    "o",
    "este",
    "sunt",
    "pentru",
    "ca",
    "mai",
    "iar",
    "fi",
    "fie",
    "a",
    "al",
    "ai",
    "ale",
    "am",
    "au",
    "nu",
    "da",
    "ce",
    "care",
    "cum",
    "unde",
    "cand",
}


def load_corpus() -> pd.DataFrame:
    logging.info("Loading corpus from %s", INPUT_PATH)
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)
    required_cols = ["post_id", "platform", "author_id", "text", "created_at"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in corpus.csv: {missing}")
    df["text"] = df["text"].fillna("").astype(str)
    df["author_id"] = df["author_id"].fillna("").astype(str)

    # Ingest normalization: ensure influencer metrics exist and propagate downstream.
    if "author_name" not in df.columns:
        df["author_name"] = df["author_id"]
    df["author_name"] = df["author_name"].fillna(df["author_id"]).astype(str)

    for col in ["followers", "likes", "comments", "shares", "views"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    missing_influencer_cols = [c for c in INFLUENCER_COLS if c not in df.columns]
    if missing_influencer_cols:
        logging.warning(
            "Ingest data missing influencer columns; defaults applied: %s",
            ", ".join(missing_influencer_cols),
        )
    return df


def build_tfidf_matrix(df: pd.DataFrame):
    logging.info("Building TF-IDF matrix (unigrams + bigrams)")
    stopwords = set(sklearn_text.ENGLISH_STOP_WORDS).union(ROMANIAN_STOPWORDS)
    vectorizer = TfidfVectorizer(
        stop_words=list(stopwords),
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
    )
    matrix = vectorizer.fit_transform(df["text"])
    return vectorizer, matrix


def run_kmeans(matrix):
    logging.info("Running KMeans with n_clusters=%s", N_CLUSTERS)
    model = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    labels = model.fit_predict(matrix)
    return model, labels


def assign_topics(df: pd.DataFrame, model: KMeans, matrix, labels: np.ndarray) -> pd.DataFrame:
    logging.info("Assigning topic IDs and confidence scores")
    distances = model.transform(matrix)
    min_dist = distances.min(axis=1)
    confidence = 1 / (1 + min_dist)
    if confidence.max() > confidence.min():
        confidence = (confidence - confidence.min()) / (confidence.max() - confidence.min())
    else:
        confidence = np.ones_like(confidence)

    out = df.copy()
    out["topic_id"] = labels
    out["topic_confidence"] = np.round(confidence, 6)
    return out[
        [
            "post_id",
            "platform",
            "author_id",
            "author_name",
            "followers",
            "likes",
            "comments",
            "shares",
            "views",
            "text",
            "created_at",
            "topic_id",
            "topic_confidence",
        ]
    ]


def extract_top_terms(model: KMeans, vectorizer: TfidfVectorizer, labels: np.ndarray) -> pd.DataFrame:
    logging.info("Extracting top %s terms per topic", TOP_TERMS)
    terms = vectorizer.get_feature_names_out()
    centers = model.cluster_centers_
    rows = []

    for topic_id in range(centers.shape[0]):
        top_idx = centers[topic_id].argsort()[::-1][:TOP_TERMS]
        top_terms = ", ".join(terms[top_idx])
        num_posts = int((labels == topic_id).sum())
        rows.append(
            {
                "topic_id": topic_id,
                "top_terms": top_terms,
                "num_posts": num_posts,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    corpus_df = load_corpus()
    vectorizer, matrix = build_tfidf_matrix(corpus_df)
    model, labels = run_kmeans(matrix)
    assigned_df = assign_topics(corpus_df, model, matrix, labels)
    terms_df = extract_top_terms(model, vectorizer, labels)

    ASSIGNED_PATH.parent.mkdir(parents=True, exist_ok=True)
    assigned_df.to_csv(ASSIGNED_PATH, index=False, encoding="utf-8")
    terms_df.to_csv(TERMS_PATH, index=False, encoding="utf-8")
    logging.info("Saved topics to %s", ASSIGNED_PATH)
    logging.info("Saved topic terms to %s", TERMS_PATH)


if __name__ == "__main__":
    main()
