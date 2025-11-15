# backend/services/utils.py

import os, re, random, json
import undetected_chromedriver as uc
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlencode

WINDOW_SIZES = [
    (1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720),
    (1680, 1050), (1600, 900), (2560, 1440), (1920, 1200)
]

USER_AGENTS = [
    # Chrome 120-140 on Windows 10/11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ver}.0.0.0 Safari/537.36 Edg/{ver}.0.0.0",
]

# Chrome versions that are fresh
CHROME_VERSIONS = [str(v) for v in range(120, 140)]

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
    return f"{base_url}?{urlencode(params)}"

def _random_user_agent() -> str:
    tmpl = random.choice(USER_AGENTS)
    ver  = random.choice(CHROME_VERSIONS)
    return tmpl.format(ver=ver)

def _random_window_size() -> str:
    w, h = random.choice(WINDOW_SIZES)
    # Add a tiny jitter (±0-30 px) so the size isn’t *exactly* the same every time
    w += random.randint(-15, 15)
    h += random.randint(-15, 15)
    return f"{w},{h}"

def create_driver(headless: bool = False):
    """Create and return a Selenium WebDriver instance."""
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-site-isolation-trials")

    options.add_argument(f"--window-size={_random_window_size()}")
    options.add_argument(f"user-agent={_random_user_agent()}")


    #  binary paths inside the container
    #chrome_path = os.getenv("CHROMIUM_PATH", "/usr/bin/chromium")
    #driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    #options.binary_location = chrome_path
    #service = Service(driver_path)

    driver = uc.Chrome(options=options, headless=headless)
    return driver