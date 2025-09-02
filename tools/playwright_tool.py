# playwright_tool.py
from typing import Dict, Optional
from playwright.sync_api import sync_playwright
import re
import html
import time

try:
    # if you have the same decorator you used for serper
    from agents import function_tool  # or wherever your decorator is
except Exception:
    # fallback no-op if you call it directly
    def function_tool(fn): return fn

def _collapse_ws(s: str) -> str:
    s = html.unescape(s or "")
    s = re.sub(r"\r\n|\r", "\n", s)
    s = re.sub(r"[ \t\f\v]+", " ", s)
    s = re.sub(r"\n[ \t]+", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

@function_tool
def playwright_web_read(
    url: str,
    wait_selector: Optional[str] = None,
    render_js: bool = True,
    timeout_ms: int = 15000,
    max_chars: int = 200_000,
    user_agent: Optional[str] = None,
) -> Dict[str, object]:
    """
    Fetch visible page text using Playwright (Chromium, headless).
    Args:
      url: The URL to visit.
      wait_selector: CSS selector to wait for (optional).
      render_js: If False, disable JS for faster loads on static pages.
      timeout_ms: Overall nav+wait timeout.
      max_chars: Truncate returned text to avoid huge payloads.
      user_agent: Optional UA string.
    Returns:
      { "title", "final_url", "status", "text", "elapsed_ms" }
    """
    t0 = time.time()
    title = ""
    final_url = url
    status = 0
    text = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context_kwargs = {}
            if user_agent:
                context_kwargs["user_agent"] = user_agent
            if not render_js:
                context_kwargs["java_script_enabled"] = False

            context = browser.new_context(**context_kwargs)
            page = context.new_page()

            # Conservative wait_until to get dynamic content when render_js=True
            wait_until = "networkidle" if render_js else "domcontentloaded"
            resp = page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            if resp:
                status = resp.status or 0
                final_url = page.url

            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=timeout_ms)
                except Exception:
                    pass  # don't fail just because selector not found

            try:
                title = page.title() or ""
            except Exception:
                title = ""

            # Prefer visible text; fall back to body textContent.
            try:
                # inner_text("body") respects visibility better than content()
                text = page.inner_text("body", timeout=2000)
            except Exception:
                try:
                    text = page.evaluate("document.body ? document.body.innerText : ''") or ""
                except Exception:
                    text = ""

            text = _collapse_ws(text)
            if len(text) > max_chars:
                text = text[:max_chars]

            return {
                "title": title,
                "final_url": final_url,
                "status": status,
                "text": text,
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
        finally:
            try:
                browser.close()
            except Exception:
                pass
