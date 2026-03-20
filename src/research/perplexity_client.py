import os
from typing import Any

import requests


class PerplexityError(Exception):
    """Raised when Perplexity API call fails."""


def _headers() -> dict[str, str]:
    api_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    if not api_key:
        raise PerplexityError("PERPLEXITY_API_KEY nu este setat.")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _extract_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str) and data.get("output_text").strip():
        return data.get("output_text", "").strip()

    choices = data.get("choices", [])
    if not choices:
        # v1/responses style fallback
        output_blocks = data.get("output", [])
        parts: list[str] = []
        if isinstance(output_blocks, list):
            for block in output_blocks:
                content = block.get("content", []) if isinstance(block, dict) else []
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") in {"output_text", "text"}:
                            txt = str(item.get("text", "")).strip()
                            if txt:
                                parts.append(txt)
        return "\n".join(parts).strip()
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "\n".join([p for p in parts if p]).strip()
    return str(content)


def _extract_citations(data: dict[str, Any]) -> list[str]:
    citations = data.get("citations")
    if isinstance(citations, list):
        return [str(url) for url in citations if str(url).startswith("http")]

    choices = data.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        c2 = message.get("citations")
        if isinstance(c2, list):
            return [str(url) for url in c2 if str(url).startswith("http")]

    # v1/responses often returns search results metadata
    search_results = data.get("search_results")
    if isinstance(search_results, list):
        urls: list[str] = []
        for item in search_results:
            if isinstance(item, dict):
                url = str(item.get("url", ""))
                if url.startswith("http"):
                    urls.append(url)
        return urls
    return []


def research_query(
    query: str,
    focus: str = "",
    model: str | None = None,
) -> dict[str, Any]:
    """Run one research query with Perplexity and return text + citations."""
    if not query.strip():
        raise PerplexityError("Query gol.")

    selected_model = (model or os.getenv("PERPLEXITY_MODEL", "")).strip()
    selected_preset = os.getenv("PERPLEXITY_PRESET", "fast-search").strip() or "fast-search"

    full_query = query.strip()
    if focus.strip():
        full_query = (
            f"{full_query}\n\nFocus area: {focus.strip()}.\n"
            "Return in Romanian with short summary, key findings, risks, and next actions."
        )

    payload: dict[str, Any] = {
        "preset": selected_preset,
        "input": full_query,
    }
    if selected_model:
        payload["model"] = selected_model

    resp = requests.post(
        "https://api.perplexity.ai/v1/responses",
        headers=_headers(),
        json=payload,
        timeout=120,
    )
    if not resp.ok:
        raise PerplexityError(f"Perplexity API {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    return {
        "model": selected_model,
        "answer": _extract_text(data),
        "citations": _extract_citations(data),
        "raw": data,
    }

