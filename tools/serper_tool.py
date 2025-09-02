# tools/serper_tool.py
import os, requests, html
from typing import Literal, Optional, Dict, Any, List, TypedDict
from agents import function_tool   # from OpenAI Agents SDK (python)
from dotenv import load_dotenv

load_dotenv(override=True)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_BASE = "https://google.serper.dev"

class SerperItem(TypedDict, total=False):
    title: str
    link: str
    snippet: str
    source: str
    date: str
    position: int

def _http_post(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if not SERPER_API_KEY:
        raise RuntimeError("SERPER_API_KEY not set")
    resp = requests.post(
        f"{SERPER_BASE}/{endpoint}",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()

def _normalize_search(data: Dict[str, Any]) -> List[SerperItem]:
    items: List[SerperItem] = []
    for it in data.get("organic", []) or []:
        items.append({
            "title": it.get("title"),
            "link": it.get("link"),
            "snippet": it.get("snippet"),
            "date": it.get("date"),
            "position": it.get("position"),
        })
    # Include Answer Box / KG as pseudo-items (optional)
    ab = data.get("answerBox")
    if ab and isinstance(ab, dict) and ab.get("title") and ab.get("link"):
        items.insert(0, {"title": ab.get("title"), "link": ab.get("link"), "snippet": ab.get("snippet", "")})
    return items

def _normalize_news(data: Dict[str, Any]) -> List[SerperItem]:
    items: List[SerperItem] = []
    for it in data.get("news", []) or []:
        items.append({
            "title": it.get("title"),
            "link": it.get("link"),
            "source": it.get("source"),
            "date": it.get("date"),
            "snippet": it.get("snippet"),
        })
    return items

@function_tool
def serper_search(
    q: str,
    kind: Literal["search", "news"] = "search",
    num: int = 10,
    page: int = 1,
    gl: str = "us",
    hl: str = "en",
    tbs: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Google web/news search via Serper.dev.

    Args:
      q: The search query (use operators like site:, filetype:, OR, -term, "exact").
      kind: "search" (standard web) or "news".
      num: Number of results to return (1–20 typical).
      page: Results page (1-based).
      gl: Country code (e.g., "us","gb","in","de").
      hl: Interface language (e.g., "en","de","ja").
      tbs: Optional Google time filter (e.g., "qdr:d","qdr:w","qdr:m").
    Returns:
      JSON with {"kind","query","items":[{title,link,snippet,source?,date?,position?}], "raw":{...}}
    """
    payload = {"q": q, "num": num, "page": page, "gl": gl, "hl": hl}
    if tbs:
        payload["tbs"] = tbs

    endpoint = "news" if kind == "news" else "search"
    data = _http_post(endpoint, payload)

    items = _normalize_news(data) if kind == "news" else _normalize_search(data)
    # basic HTML unescape on snippets
    for it in items:
        if "snippet" in it and it["snippet"]:
            it["snippet"] = html.unescape(it["snippet"])

    return {"kind": kind, "query": q, "items": items, "raw": {"meta": {k: data.get(k) for k in ("knowledgeGraph","answerBox")}}}
