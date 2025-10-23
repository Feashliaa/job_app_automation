# backend/services/utils.py

import os
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def load_env_variables():
    """Load and return required environment variables."""
    load_dotenv()
    return {
        "SQL_PASSWORD": os.getenv("SQL_PASSWORD"),
        "SQL_USER": os.getenv("SQL_USER"),
        "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
    }


def sanitize_filename(filename: str) -> str:
    """Remove invalid filename characters."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename).strip()


def build_url(base_url: str, params: dict) -> str:
    """Build a URL with encoded query parameters."""
    from urllib.parse import urlencode
    return f"{base_url}?{urlencode(params)}"


def create_driver(headless: bool = False):
    """Create and return a Selenium Chrome driver."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    return driver
