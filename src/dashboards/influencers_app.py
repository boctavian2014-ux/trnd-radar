from pathlib import Path
import sys

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from comfy.comfy_client import (  # noqa: E402
    ComfyCloudError,
)
from comfy.comfy_topics import generate_topic_image, generate_topic_reel  # noqa: E402

INFLUENCERS_PATH = BASE_DIR / "data" / "processed" / "influencers.csv"
TOPICS_PATH = BASE_DIR / "data" / "processed" / "topics_assigned.csv"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not INFLUENCERS_PATH.exists():
        raise FileNotFoundError(f"Missing file: {INFLUENCERS_PATH}")
    if not TOPICS_PATH.exists():
        raise FileNotFoundError(f"Missing file: {TOPICS_PATH}")

    influencers = pd.read_csv(INFLUENCERS_PATH)
    topics = pd.read_csv(TOPICS_PATH)

    influencers["influencer_score"] = pd.to_numeric(
        influencers["influencer_score"], errors="coerce"
    ).fillna(0)
    influencers["engagement_rate"] = pd.to_numeric(
        influencers.get("engagement_rate"), errors="coerce"
    )
    influencers["followers"] = pd.to_numeric(influencers.get("followers"), errors="coerce").fillna(0)
    influencers["num_posts"] = pd.to_numeric(influencers.get("num_posts"), errors="coerce").fillna(0)

    topics["created_at"] = pd.to_datetime(topics.get("created_at"), errors="coerce")
    for col in ["likes", "comments", "shares"]:
        if col in topics.columns:
            topics[col] = pd.to_numeric(topics[col], errors="coerce").fillna(0)
        else:
            topics[col] = 0
    topics["total_engagement"] = topics["likes"] + topics["comments"] + topics["shares"]
    return influencers, topics


def main() -> None:
    st.set_page_config(page_title="Influencers Dashboard", layout="wide")
    st.title("Influencers Dashboard")

    try:
        influencers, topics = load_data()
    except Exception as exc:
        st.error(str(exc))
        st.info("Ruleaza mai intai pipeline-ul pentru influencers.csv si topics_assigned.csv.")
        return

    platforms = ["All"] + sorted(influencers["platform"].dropna().astype(str).unique().tolist())
    selected_platform = st.selectbox("Platform", platforms, index=0)

    max_score = float(influencers["influencer_score"].max()) if not influencers.empty else 0.0
    min_score = st.slider("Min influencer_score", 0.0, max(1.0, max_score), 0.0)
    topic_filter = st.text_input("Filtru topic_id (optional)")

    filtered = influencers.copy()
    if selected_platform != "All":
        filtered = filtered[filtered["platform"] == selected_platform]
    filtered = filtered[filtered["influencer_score"] >= min_score]
    if topic_filter.strip():
        filtered = filtered[
            filtered["top_topics"]
            .fillna("")
            .astype(str)
            .str.contains(topic_filter.strip(), case=False, regex=False)
        ]

    filtered = filtered.sort_values("influencer_score", ascending=False)
    st.subheader("Top influenceri")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    if filtered.empty:
        st.info("Nu exista influenceri pentru filtrele alese.")
        return

    options = (
        filtered.apply(
            lambda r: f"{r['author_name']} ({r['platform']} | {r['author_id']})",
            axis=1,
        )
        .tolist()
    )
    selected_label = st.selectbox("Selecteaza influencer", options)
    selected_row = filtered.iloc[options.index(selected_label)]

    st.metric("Followers", f"{int(selected_row['followers']):,}")
    engagement_rate_value = selected_row["engagement_rate"]
    st.metric(
        "Engagement rate",
        "N/A" if pd.isna(engagement_rate_value) else f"{engagement_rate_value:.2f}%",
    )
    st.metric("Num posts", int(selected_row["num_posts"]))

    posts = topics[
        (topics["platform"] == selected_row["platform"])
        & (topics["author_id"].astype(str) == str(selected_row["author_id"]))
    ].copy()
    posts = posts.sort_values("created_at")

    if posts.empty:
        st.info("Nu exista postari pentru influencerul selectat.")
        return

    chart_df = posts[["created_at", "likes", "total_engagement"]].set_index("created_at")
    st.subheader("Evolutie likes / total_engagement")
    st.line_chart(chart_df, use_container_width=True)

    st.subheader("Genereaza cover cu Comfy Cloud")
    workflow_path = st.text_input(
        "Workflow API JSON path",
        str(BASE_DIR / "workflow_api.json"),
        help="Exporta workflow-ul din Comfy UI si pune fisierul in proiect.",
    )
    node_id = st.text_input("Node ID pentru prompt text", "6")
    input_key = st.text_input("Input key in node", "text")
    default_prompt = (
        f"Poster social media pentru creatorul {selected_row['author_name']} "
        f"({selected_row['platform']}) cu topicuri: {selected_row.get('top_topics', '')}"
    )
    prompt_text = st.text_area("Prompt text", default_prompt, height=120)

    if st.button("Genereaza cover cu Comfy"):
        try:
            with st.spinner("Trimit workflow catre Comfy Cloud..."):
                image_path = generate_topic_image(
                    topic_name=str(selected_row.get("top_topics", "topic")),
                    description=prompt_text,
                    workflow_path=workflow_path,
                    text_node_id=node_id,
                    text_input_name=input_key,
                    output_dir=str(BASE_DIR / "outputs" / "topics"),
                )
            if image_path:
                st.success("Imagine generata cu succes.")
                st.image(image_path, caption=Path(image_path).name)
            else:
                st.error("Nu am primit niciun fisier de la Comfy Cloud.")
        except ComfyCloudError as exc:
            st.error(f"Eroare Comfy Cloud: {exc}")
        except Exception as exc:
            st.error(f"Eroare Comfy Cloud: {exc}")

    st.subheader("Genereaza Reels cu Comfy Cloud")
    workflow_video_path = st.text_input(
        "Workflow video API JSON path",
        str(BASE_DIR / "workflow_video_api.json"),
        help="Foloseste un workflow video exportat din Comfy Cloud.",
    )
    video_node_id = st.text_input("Node ID pentru prompt video", "6")
    video_input_key = st.text_input("Input key in video node", "text")
    default_video_prompt = (
        f"Scurt clip vertical despre creatorul {selected_row['author_name']} "
        f"si topicurile {selected_row.get('top_topics', '')}."
    )
    video_prompt_text = st.text_area("Prompt video", default_video_prompt, height=100)

    if st.button("Genereaza Reels"):
        try:
            with st.spinner("Generez video cu Comfy Cloud..."):
                video_path = generate_topic_reel(
                    topic_name=str(selected_row.get("top_topics", "topic")),
                    description=video_prompt_text,
                    workflow_path=workflow_video_path,
                    text_node_id=video_node_id,
                    text_input_name=video_input_key,
                    output_dir=str(BASE_DIR / "outputs" / "reels"),
                )
            if video_path:
                st.success("Video generat cu succes.")
                st.video(video_path)
                st.caption(Path(video_path).name)
            else:
                st.error("Nu am primit niciun video de la Comfy Cloud.")
        except ComfyCloudError as exc:
            st.error(f"Eroare Comfy Cloud: {exc}")
        except Exception as exc:
            st.error(f"Eroare Comfy Cloud: {exc}")


if __name__ == "__main__":
    main()
