"""
Client pentru API-ul MiroFish (backend pe port 5001).
Toate apelurile sunt în română/engleză; răspunsurile de la server pot conține mesaje în chineză.
"""

import time
from typing import Any, Optional

import requests


class MiroFishError(Exception):
    """Eroare la apelul API MiroFish."""
    pass


def _url(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}{path}"


def check_health(base_url: str = "http://localhost:5001", timeout: int = 5) -> bool:
    """Verifică dacă backend-ul MiroFish răspunde."""
    try:
        r = requests.get(_url(base_url, "/health"), timeout=timeout)
        return r.ok
    except Exception:
        return False


def ontology_generate(
    base_url: str,
    files: list[tuple[str, bytes]],
    simulation_requirement: str,
    project_name: str = "Proiect Dashboard",
    additional_context: str = "",
) -> dict[str, Any]:
    """
    Pas 1: Încarcă documente și prompt, obține project_id.
    files: listă de (filename, content_bytes) – ex. [("doc.pdf", b"...")]
    """
    url = _url(base_url, "/api/graph/ontology/generate")
    data = {
        "simulation_requirement": simulation_requirement,
        "project_name": project_name,
        "additional_context": additional_context,
    }
    file_list = [("files", (name, content)) for name, content in files]
    r = requests.post(url, data=data, files=file_list, timeout=120)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    out = r.json()
    if not out.get("success"):
        raise MiroFishError(out.get("error", r.text))
    return out["data"]


def graph_build(
    base_url: str,
    project_id: str,
    graph_name: str = "Graf",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict[str, Any]:
    """Pas 2: Pornește construirea grafului; returnează task_id pentru polling."""
    url = _url(base_url, "/api/graph/build")
    r = requests.post(
        url,
        json={
            "project_id": project_id,
            "graph_name": graph_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        timeout=30,
    )
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    out = r.json()
    if not out.get("success"):
        raise MiroFishError(out.get("error", r.text))
    return out["data"]


def graph_task_status(base_url: str, task_id: str) -> dict[str, Any]:
    """Verifică statusul task-ului de construire graf."""
    url = _url(base_url, f"/api/graph/task/{task_id}")
    r = requests.get(url, timeout=10)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    return r.json()


def wait_graph_build(
    base_url: str,
    task_id: str,
    poll_interval: float = 2.0,
    timeout: int = 600,
) -> dict[str, Any]:
    """Așteaptă finalizarea construcției grafului. Returnează ultimul status."""
    start = time.time()
    while time.time() - start < timeout:
        status = graph_task_status(base_url, task_id)
        s = status.get("status") or status.get("data", {}).get("status")
        if s == "completed" or s == "success":
            return status
        if s in ("failed", "error", "cancelled"):
            raise MiroFishError(f"Task eșuat: {status}")
        time.sleep(poll_interval)
    raise MiroFishError("Timeout așteptând construcția grafului.")


def simulation_create(
    base_url: str,
    project_id: str,
    graph_id: Optional[str] = None,
    enable_twitter: bool = True,
    enable_reddit: bool = True,
) -> dict[str, Any]:
    """Pas 3: Creează simularea; returnează simulation_id."""
    url = _url(base_url, "/api/simulation/create")
    payload = {
        "project_id": project_id,
        "enable_twitter": enable_twitter,
        "enable_reddit": enable_reddit,
    }
    if graph_id:
        payload["graph_id"] = graph_id
    r = requests.post(url, json=payload, timeout=30)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    out = r.json()
    if not out.get("success"):
        raise MiroFishError(out.get("error", r.text))
    return out["data"]


def simulation_prepare(
    base_url: str,
    simulation_id: str,
    force_regenerate: bool = False,
) -> dict[str, Any]:
    """Pas 4: Pornește pregătirea simulării (async); returnează task_id pentru polling."""
    url = _url(base_url, "/api/simulation/prepare")
    r = requests.post(
        url,
        json={"simulation_id": simulation_id, "force_regenerate": force_regenerate},
        timeout=30,
    )
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    out = r.json()
    if not out.get("success"):
        raise MiroFishError(out.get("error", r.text))
    return out["data"]


def simulation_prepare_status(base_url: str, payload: dict) -> dict[str, Any]:
    """Verifică statusul pregătirii (POST cu task_id / simulation_id)."""
    url = _url(base_url, "/api/simulation/prepare/status")
    r = requests.post(url, json=payload, timeout=30)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    return r.json()


def simulation_start(
    base_url: str,
    simulation_id: str,
    platform: str = "parallel",
    max_rounds: Optional[int] = None,
    force: bool = False,
) -> dict[str, Any]:
    """Pas 5: Pornește rularea simulării."""
    url = _url(base_url, "/api/simulation/start")
    body = {"simulation_id": simulation_id, "platform": platform, "force": force}
    if max_rounds is not None:
        body["max_rounds"] = max_rounds
    r = requests.post(url, json=body, timeout=30)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    out = r.json()
    if not out.get("success"):
        raise MiroFishError(out.get("error", r.text))
    return out["data"]


def simulation_run_status(base_url: str, simulation_id: str) -> dict[str, Any]:
    """Statusul rulării simulării."""
    url = _url(base_url, f"/api/simulation/{simulation_id}/run-status")
    r = requests.get(url, timeout=10)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    return r.json()


def report_generate(
    base_url: str,
    simulation_id: str,
    force_regenerate: bool = False,
) -> dict[str, Any]:
    """Pas 6: Pornește generarea raportului (async); returnează task_id."""
    url = _url(base_url, "/api/report/generate")
    r = requests.post(
        url,
        json={"simulation_id": simulation_id, "force_regenerate": force_regenerate},
        timeout=30,
    )
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    out = r.json()
    if not out.get("success"):
        raise MiroFishError(out.get("error", r.text))
    return out["data"]


def report_generate_status(base_url: str, payload: dict) -> dict[str, Any]:
    """Verifică statusul generării raportului."""
    url = _url(base_url, "/api/report/generate/status")
    r = requests.post(url, json=payload, timeout=30)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    return r.json()


def report_by_simulation(base_url: str, simulation_id: str) -> Optional[dict[str, Any]]:
    """Obține raportul după simulation_id (dacă există)."""
    url = _url(base_url, f"/api/report/by-simulation/{simulation_id}")
    r = requests.get(url, timeout=10)
    if not r.ok:
        return None
    out = r.json()
    if not out.get("success"):
        return None
    return out.get("data")


def project_list(base_url: str, limit: int = 20) -> list[dict]:
    """Listează proiectele existente."""
    url = _url(base_url, "/api/graph/project/list")
    r = requests.get(url, params={"limit": limit}, timeout=10)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    out = r.json()
    if not out.get("success"):
        raise MiroFishError(out.get("error", r.text))
    return out.get("data", [])


def simulation_list(base_url: str) -> list[dict]:
    """Listează simulările."""
    url = _url(base_url, "/api/simulation/list")
    r = requests.get(url, timeout=10)
    if not r.ok:
        raise MiroFishError(f"API {r.status_code}: {r.text[:500]}")
    out = r.json()
    if not out.get("success"):
        raise MiroFishError(out.get("error", r.text))
    return out.get("data", [])
