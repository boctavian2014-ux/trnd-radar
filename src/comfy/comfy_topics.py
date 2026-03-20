from typing import Optional
from pathlib import Path

from .comfy_client import download_outputs, load_workflow, submit_workflow, wait_for_completion


def generate_topic_image(
    topic_name: str,
    description: str,
    workflow_path: str = "workflow_api.json",
    text_node_id: str = "6",
    text_input_name: str = "text",
    output_dir: str = "outputs/topics",
) -> Optional[str]:
    """
    Ruleaza un workflow Comfy Cloud pentru a genera o imagine pentru un topic.
    Returneaza path-ul local la prima imagine generata sau None daca nu exista.
    """
    prompt_text = f"Viral social media thumbnail about topic: {topic_name}. {description}"
    workflow = load_workflow(workflow_path)

    if text_node_id in workflow:
        workflow[text_node_id]["inputs"][text_input_name] = prompt_text
    else:
        raise ValueError(f"Node ID {text_node_id} nu exista in workflow_api.json")

    prompt_id = submit_workflow(workflow)
    outputs = wait_for_completion(prompt_id)
    paths = download_outputs(outputs, output_dir=output_dir)
    return paths[0] if paths else None


def generate_topic_reel(
    topic_name: str,
    description: str,
    workflow_path: str = "workflow_video_api.json",
    text_node_id: str = "6",
    text_input_name: str = "text",
    output_dir: str = "outputs/reels",
) -> Optional[str]:
    """
    Ruleaza un workflow video in Comfy Cloud pentru a genera un clip vertical.
    Returneaza path-ul local la primul fisier video generat sau None.
    """
    prompt_text = (
        f"Vertical short-form video (Reels/TikTok style) about topic: {topic_name}. "
        f"{description}"
    )

    workflow = load_workflow(workflow_path)

    if text_node_id in workflow:
        workflow[text_node_id]["inputs"][text_input_name] = prompt_text
    else:
        raise ValueError(f"Node ID {text_node_id} nu exista in {workflow_path}")

    prompt_id = submit_workflow(workflow)
    outputs = wait_for_completion(prompt_id)
    paths = download_outputs(outputs, output_dir=output_dir)
    preferred_order = [".mp4", ".webm", ".mov"]

    for extension in preferred_order:
        matches = [p for p in paths if Path(p).suffix.lower() == extension]
        if matches:
            return matches[0]

    return paths[0] if paths else None
