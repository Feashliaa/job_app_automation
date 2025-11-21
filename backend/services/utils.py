# backend/services/utils.py

import os, re, random
import undetected_chromedriver as uc
from dotenv import load_dotenv
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

def create_driver(headless: bool = False):
    options = uc.ChromeOptions()

    if not headless:
        os.environ["DISPLAY"] = os.environ.get("DISPLAY", ":99")
    else:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--allow-insecure-localhost")
    
    options.add_argument("--disable-gpu")
    options.add_argument("--use-gl=swiftshader")
    options.add_argument("--enable-unsafe-swiftshader")

    driver = uc.Chrome(options=options,
                       headless=headless, 
                       use_subprocess=False, 
                       enable_logging=True,
                       browser_executable_path="/usr/bin/google-chrome")
    
    print("navigator.webdriver:", driver.execute_script("return navigator.webdriver"))

    return driver
