# backend/services/base_scraper.py
# Sets up variables shared among scrapes, the url method, 
# the create driver method, wait method, and close method
import time
import random
from backend.services import utils
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

CAUGHT_UP = "__CAUGHT_UP__"

class BaseScraper:
    def __init__(self):
        self.driver = utils.create_driver()
        env_vars = utils.load_env_variables()
        self.email_address = env_vars["EMAIL_ADDRESS"]
        self.email_password = env_vars["EMAIL_PASSWORD"]

    def _go_to_url(self, url):
        self.driver.delete_all_cookies()
        self.driver.get("about:blank")
        time.sleep(random.uniform(1, 2))
        self.driver.get(url)
        time.sleep(random.uniform(1, 2))

    def _wait_for_elements(self, selector, timeout=30):
        try:
            
            self.driver.save_screenshot("/app/debug_wait.png")  # Debug screenshot
            
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)),
                    EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), \"You're all caught up!\")]"))
                )
            )

            caught_up = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), \"You're all caught up!\")]"
            )

            if caught_up:
                return {"status": "caught_up", "elements": []}

            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            return {"status": "ok", "elements": elements}

        except Exception:
            print(f"Timeout waiting for selector: {selector}")
            return {"status": "timeout", "elements": []}



    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass 
