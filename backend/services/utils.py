import os
import re
import random
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from urllib.parse import urlencode
from dataclasses import dataclass

from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext

# -----------------------------
# RANDOMIZATION CONSTANTS
# -----------------------------
WINDOW_SIZES = [
    (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
    (1280, 720), (1680, 1050), (1600, 900), (2560, 1440),
    (1920, 1200)
]

# -----------------------------
# ENV LOADER
# -----------------------------
def load_env_variables():
    load_dotenv()
    return {
        "SQL_PASSWORD": os.getenv("SQL_PASSWORD"),
        "SQL_USER": os.getenv("SQL_USER"),
        "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
    }

# -----------------------------
# HELPERS
# -----------------------------
def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", filename).strip()

def build_url(base_url: str, params: dict) -> str:
    return f"{base_url}?{urlencode(params)}"

def _random_window_size():
    w, h = random.choice(WINDOW_SIZES)
    w += random.randint(-20, 20)
    h += random.randint(-20, 20)
    return (w, h)

# -----------------------------
# Playwright CDP ATTACH (async)
# -----------------------------
@dataclass
class CDPSession:
    playwright: Playwright
    browser: Browser
    context: BrowserContext

async def create_browser_cdp(cdp_url: str = "http://localhost:9222", context_index: int = 0) -> CDPSession:
    """
    Connect to an existing Chrome instance via CDP and return a session object.
    - cdp_url: URL where Chrome is exposing remote debugging (default http://localhost:9222).
    - context_index: if Chrome has contexts, use the indexed one (default 0). If none exist, a new context is created.
    """
    playwright = await async_playwright().start()
    # connect_over_cdp will not launch a browser; it connects to an existing Chrome
    browser = await playwright.chromium.connect_over_cdp(cdp_url)

    contexts = browser.contexts
    if contexts and len(contexts) > context_index:
        context = contexts[context_index]
    else:
        # create a new context to isolate pages created by the scraper
        context = await browser.new_context()

    return CDPSession(playwright=playwright, browser=browser, context=context)

async def close_cdp_session(session: CDPSession, detach_only: bool = True):
    """
    Cleanly release Playwright resources. If detach_only is True we disconnect the Playwright Browser
    object without terminating the real Chrome process. If False, Playwright will attempt to close the
    connection which may have different side effects.
    """
    try:
        if detach_only:
            # Disconnect the Playwright connection without killing the remote browser process
            await session.detach() # type: ignore
        else:
            # Close will attempt to close the remote browser connection
            await session.browser.close()
    except Exception:
        pass
    try:
        await session.playwright.stop()
    except Exception:
        pass
