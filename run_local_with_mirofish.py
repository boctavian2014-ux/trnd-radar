"""
Start local dashboard together with local MiroFish backend.

Usage (PowerShell):
  python run_local_with_mirofish.py

Optional env vars:
  MIROFISH_PATH   - path to MiroFish repo (default: ../MiroFish)
  MIROFISH_PORT   - backend port (default: 5001)
  DASHBOARD_PORT  - Streamlit port (default: 8501)
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _default_mirofish_path() -> Path:
    return (_project_root().parent / "MiroFish").resolve()


def _wait_for_health(base_url: str, timeout_s: int = 60) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            response = requests.get(f"{base_url.rstrip('/')}/health", timeout=2)
            if response.ok:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main() -> int:
    mirofish_path = Path(os.getenv("MIROFISH_PATH", str(_default_mirofish_path()))).resolve()
    mirofish_port = int(os.getenv("MIROFISH_PORT", "5001"))
    dashboard_port = int(os.getenv("DASHBOARD_PORT", "8501"))
    mirofish_url = f"http://localhost:{mirofish_port}"

    if not mirofish_path.exists():
        print(f"[ERROR] MiroFish path not found: {mirofish_path}")
        print("Set MIROFISH_PATH env var to your local MiroFish repo.")
        return 1

    backend_dir = mirofish_path / "backend"
    run_file = backend_dir / "run.py"
    if not run_file.exists():
        print(f"[ERROR] Missing MiroFish backend entrypoint: {run_file}")
        return 1

    print(f"[INFO] Starting MiroFish backend from: {backend_dir}")
    backend_env = os.environ.copy()
    backend_env["FLASK_HOST"] = backend_env.get("FLASK_HOST", "0.0.0.0")
    backend_env["FLASK_PORT"] = str(mirofish_port)
    backend_proc = subprocess.Popen(
        ["uv", "run", "python", "run.py"],
        cwd=str(backend_dir),
        env=backend_env,
    )

    print(f"[INFO] Waiting for MiroFish health: {mirofish_url}/health")
    if not _wait_for_health(mirofish_url, timeout_s=90):
        print("[ERROR] MiroFish backend did not become healthy in time.")
        backend_proc.terminate()
        return 1

    print("[INFO] MiroFish backend is healthy.")
    print("[INFO] Starting Streamlit dashboard...")

    dashboard_env = os.environ.copy()
    dashboard_env["MIROFISH_API_URL"] = mirofish_url

    dashboard_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.address",
            "0.0.0.0",
            "--server.port",
            str(dashboard_port),
            "--server.headless",
            "true",
        ],
        cwd=str(_project_root()),
        env=dashboard_env,
    )

    print(f"[READY] Dashboard: http://localhost:{dashboard_port}")
    print("[INFO] Press Ctrl+C to stop both processes.")

    def _shutdown(*_args: object) -> None:
        for proc in (dashboard_proc, backend_proc):
            if proc.poll() is None:
                proc.terminate()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            if backend_proc.poll() is not None:
                print("[ERROR] MiroFish backend stopped.")
                _shutdown()
                return 1
            if dashboard_proc.poll() is not None:
                print("[INFO] Dashboard stopped.")
                _shutdown()
                return 0
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
