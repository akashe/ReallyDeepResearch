import os, json, uuid
from typing import Any, Dict

def parse_json(maybe_json: Any) -> Dict:
    """Accept dict or JSON string; return dict. If model returned prose, try to extract JSON fallback."""
    if isinstance(maybe_json, dict):
        return maybe_json
    if isinstance(maybe_json, str):
        s = maybe_json.strip()
        # fast path
        try:
            return json.loads(s)
        except Exception:
            # naive JSON block extraction
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(s[start:end+1])
                except Exception:
                    pass
    # last resort
    return {"_raw": maybe_json, "_error": "unparsed"}

def ensure_keys(d: Dict, required: Dict[str, Any]) -> Dict:
    """Fill missing top-level keys with defaults (shallow)."""
    out = dict(d or {})
    for k, v in required.items():
        if k not in out:
            out[k] = v
    return out

def new_id(prefix="s"):
    return f"{prefix}{uuid.uuid4().hex[:8]}"

def as_messages(payload: Dict) -> list:
    """Convert a dict payload to a single user message so Runner.run can .extend(...)."""
    return [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]

import json

def to_text(maybe) -> str:
    if isinstance(maybe, str):
        return maybe
    for attr in ("output_text", "text", "content"):
        if hasattr(maybe, attr) and isinstance(getattr(maybe, attr), str):
            return getattr(maybe, attr)
    if hasattr(maybe, "messages") and isinstance(maybe.messages, list):
        for m in reversed(maybe.messages):
            if isinstance(m, dict) and m.get("role") in ("assistant", "tool"):
                if isinstance(m.get("content"), str):
                    return m["content"]
    return str(maybe)

def parse_json_or_none(raw):
    s = to_text(raw).strip()
    try:
        return json.loads(s)
    except Exception:
        # second chance: grab the first {...} block
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j != -1 and j > i:
            try:
                return json.loads(s[i:j+1])
            except Exception:
                pass
    return None  # <— IMPORTANT: never stash raw objects in a dict
