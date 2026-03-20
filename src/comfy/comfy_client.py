import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

# Root-ul proiectului ("social trends")
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)
load_dotenv()  # fallback: cwd

BASE_URL = "https://cloud.comfy.org"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ComfyCloudError(Exception):
    pass


def _get_headers() -> Dict[str, str]:
    api_key = os.getenv("COMFY_CLOUD_API_KEY")
    if not api_key:
        raise ComfyCloudError("COMFY_CLOUD_API_KEY nu este setat in .env")
    return {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }


def submit_workflow(workflow: Dict[str, Any]) -> str:
    """
    Trimite un workflow Comfy (API format) si intoarce prompt_id (job ID).
    """
    url = f"{BASE_URL}/api/prompt"
    resp = requests.post(url, headers=_get_headers(), json={"prompt": workflow}, timeout=60)
    if not resp.ok:
        raise ComfyCloudError(f"HTTP {resp.status_code}: {resp.text}")
    data = resp.json()
    prompt_id = data.get("prompt_id") or data.get("promptId") or data.get("id")
    if not prompt_id:
        raise ComfyCloudError(f"Nu am gasit prompt_id in raspuns: {data}")
    logger.info("Workflow trimis. prompt_id=%s", prompt_id)
    return prompt_id


def wait_for_completion(
    prompt_id: str, poll_interval: float = 2.0, timeout: int = 300
) -> Dict[str, Any]:
    """
    Polling simplu /api/job/{prompt_id}/status pana job-ul e completed sau eroare.
    Returneaza outputs din /api/history_v2/{prompt_id}.
    """
    url_status = f"{BASE_URL}/api/job/{prompt_id}/status"
    start = time.time()

    while True:
        resp = requests.get(url_status, headers=_get_headers(), timeout=30)
        if not resp.ok:
            raise ComfyCloudError(f"Status HTTP {resp.status_code}: {resp.text}")
        status = resp.json().get("status")
        logger.info("Job %s status: %s", prompt_id, status)

        if status == "completed":
            break
        if status in {"failed", "cancelled"}:
            raise ComfyCloudError(f"Job {prompt_id} s-a incheiat cu status={status}")
        if time.time() - start > timeout:
            raise ComfyCloudError(f"Timeout asteptand job {prompt_id}")
        time.sleep(poll_interval)

    url_hist = f"{BASE_URL}/api/history_v2/{prompt_id}"
    hist_resp = requests.get(url_hist, headers=_get_headers(), timeout=30)
    if not hist_resp.ok:
        raise ComfyCloudError(f"History HTTP {hist_resp.status_code}: {hist_resp.text}")
    history = hist_resp.json()
    outputs = history.get("outputs") or history
    return outputs


def download_outputs(outputs: Dict[str, Any], output_dir: str = "outputs") -> List[str]:
    """
    Descarca toate fisierele (images/video/audio) din outputs in output_dir.
    Returneaza lista de path-uri locale.
    """
    os.makedirs(output_dir, exist_ok=True)
    saved_paths: List[str] = []

    for node_outputs in outputs.values():
        for key in ["images", "video", "audio"]:
            for file_info in node_outputs.get(key, []) or []:
                params = {
                    "filename": file_info.get("filename"),
                    "subfolder": file_info.get("subfolder") or "",
                    "type": file_info.get("type") or "output",
                }
                view_url = f"{BASE_URL}/api/view"
                resp = requests.get(
                    view_url,
                    headers=_get_headers(),
                    params=params,
                    allow_redirects=False,
                    timeout=30,
                )
                if resp.status_code != 302:
                    raise ComfyCloudError(f"/api/view HTTP {resp.status_code}: {resp.text}")
                signed_url = resp.headers.get("location")
                if not signed_url:
                    raise ComfyCloudError("Lipseste header-ul Location pentru URL semnat")

                file_resp = requests.get(signed_url, timeout=120)
                if not file_resp.ok:
                    raise ComfyCloudError(
                        f"Download HTTP {file_resp.status_code}: {file_resp.text}"
                    )

                filename = file_info.get("filename") or f"output_{len(saved_paths)}"
                path = os.path.join(output_dir, filename)
                with open(path, "wb") as file:
                    file.write(file_resp.content)
                saved_paths.append(path)
                logger.info("Salvat: %s", path)

    return saved_paths


def load_workflow(path: str = "workflow_api.json") -> Dict[str, Any]:
    """
    Incarca workflow-ul exportat din Comfy Cloud in format API, din root-ul proiectului.
    Daca path nu exista in root, incearca path + ".json" (ex: workflow_api.json -> workflow_api.json.json).
    """
    base = ROOT / path
    tried = str(base)

    if not base.is_file() and path.endswith(".json"):
        alt = ROOT / (path + ".json")
        if alt.is_file():
            base = alt

    if not base.is_file():
        raise FileNotFoundError(f"Nu am gasit workflow-ul Comfy la: {tried} sau {base}")

    with base.open("r", encoding="utf-8") as file:
        return json.load(file)
