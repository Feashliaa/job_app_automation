import random
import asyncio
from typing import Optional, List, Any
from backend.services import utils

class BaseScraper:
    def __init__(self):
        self.session = None  # utils.CDPSession
        self.context = None
        self.page = None

        env_vars = utils.load_env_variables()
        self.email_address = env_vars["EMAIL_ADDRESS"]
        self.email_password = env_vars["EMAIL_PASSWORD"]

    async def start(self, cdp_url: str = "http://localhost:9222", context_index: int = 0):
        """
        Connect to an existing Chrome via CDP and prepare a new page.
        """
        self.session = await utils.create_browser_cdp(cdp_url=cdp_url, context_index=context_index)
        self.context = self.session.context
        # create a new page in the (real) Chrome context so we don't reuse visible tabs
        self.page = await self.context.new_page()
        return self.page

    async def _go_to_url(self, url: str, timeout: int = 30000):
        """Navigate to `url` using Playwright page.goto with a small human delay after navigation."""
        if not self.page:
            raise RuntimeError("Page not initialized. Call start() first.")
        try:
            await self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        except Exception as e:
            # propagate so callers can retry if they want
            raise
        # small human-like delay
        await asyncio.sleep(random.uniform(2.5, 6.0))

    async def _wait_for_elements(self, selector: str, timeout: int = 30) -> List[Any]:
        """
        Poll until elements matching CSS selector appear or timeout.
        Returns list of ElementHandle or empty list on timeout.
        """
        if not self.page:
            return []

        end_time = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < end_time:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    return elements
            except Exception:
                pass
            await asyncio.sleep(random.uniform(1.0, 2.0))

        # timeout
        print(f"Timeout waiting for selector: {selector}")
        return []

    async def close(self):
        """Detach/close Playwright session while avoiding killing the real Chrome process."""
        try:
            if self.session:
                await utils.close_cdp_session(self.session, detach_only=True)
        except Exception:
            pass
