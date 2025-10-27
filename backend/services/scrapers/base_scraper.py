# backend/services/base_scraper.py
# Sets up variables shared among scrapes, the url method, 
# the create driver method, wait method, and close method
import time
import random
from backend.services import utils
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class BaseScraper:
    def __init__(self):
        self.driver = utils.create_driver()
        env_vars = utils.load_env_variables()
        self.email_address = env_vars["EMAIL_ADDRESS"]
        self.email_password = env_vars["EMAIL_PASSWORD"]

    def _go_to_url(self, url):
        
        print(f"DEBUG navigating to: {url}")
        
        self.driver.delete_all_cookies()
        self.driver.get("about:blank")
        time.sleep(1)
        self.driver.get(url)
        self.driver.get(url)
        time.sleep(random.uniform(1, 3))

    def _wait_for_elements(self, selector, timeout=30):
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
        )

    def close(self):
        self.driver.quit()