# backend/services/scraper.py
import json
import urllib.parse
import time
import random
import base64
import requests
from datetime import datetime
from backend.services import utils
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Scraper:

    BASE_URL = "https://hiring.cafe/"

    DATE_POSTED_MAP = {"Past Month": 61, "Past Week": 14, "Past 24 Hours": 2}

    EXPERIENCE_LEVEL_MAP = {
        "Entry Level": "Entry Level",
        "Mid Level": "Mid Level",
        "Senior Level": "Senior Level",
    }

    JOB_TITLE_QUERY_MAP = {
        "Software Engineer": "software+engineer",
        "Quality Assurance Engineer": "quality+assurance+engineer",
        "Data Analyst": "data+analyst",
        "Frontend Developer": "frontend+developer",
        "Backend Developer": "backend+developer",
    }

    def __init__(self):
        self.driver = utils.create_driver()

        # load env variables if needed
        env_vars = utils.load_env_variables()
        self.email_address = env_vars["EMAIL_ADDRESS"]
        self.email_password = env_vars["EMAIL_PASSWORD"]

    def _build_search_url(self, date_posted, experience_level, job_title, location):
        # Map inputs to values or provide fallbacks
        date_posted_val = self.DATE_POSTED_MAP.get(date_posted, 14)
        exp_val = self.EXPERIENCE_LEVEL_MAP.get(experience_level, "Entry Level")
        job_val = self.JOB_TITLE_QUERY_MAP.get(job_title, "software+engineer")

        # Determine workplace type
        workplace_type = (
            ["Remote"] if "remote" in location.lower() else [location.title()]
        )

        # Build the JSON search state
        search_state = {
            "dateFetchedPastNDays": date_posted_val,
            "searchQuery": job_val,
            "workplaceTypes": workplace_type,
            "seniorityLevel": [exp_val],
        }

        # URL-encode the JSON
        encoded_state = urllib.parse.quote(json.dumps(search_state))

        return f"{self.BASE_URL}?searchState={encoded_state}"

    def _go_to_url(self, url):  # used to navigate to a URL
        self.driver.get(url)
        time.sleep(random.uniform(2, 5)) # wait for page to load

    def _scrape_logic(self, url, job_title, location, date_posted, experience_level):  # core scraping logic
        self._go_to_url(url)

        # Wait for job postings to load
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.relative.bg-white")
            )
        )

        job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.relative.bg-white")

        print(f"Found {len(job_cards)} job postings. Pausing for inspection...")

        results = []

        for card in job_cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, "span.font-bold.text-start").text
            except:
                title = "N/A"

            try:
                company = card.find_element(By.CSS_SELECTOR, "span.line-clamp-3.font-light span.font-bold").text
                # Remove trailing colon, e.g. "Navigant: " → "Navigant"
                company = company.rstrip(":").strip()
            except:
                company = "N/A"

            try:
                link = card.find_element(By.CSS_SELECTOR, "a[href*='viewjob']").get_attribute("href")
            except:
                link = "N/A"

            results.append(
                {
                    "JobTitle": title,
                    "Company": company,
                    "Location": location,
                    "URL": link,
                    "Status": "New",
                    "DateFound": datetime.today().date().isoformat(),
                }
            )


        print(f"\nExtracted {len(results) - 1} jobs:")
        
        # remove the first card, which ususally is an ad, or nothing at all
        if results:
            results = results[1:]

        for job in results:
            print(f"- {job['JobTitle']} at {job['Company']} ({job['URL']})")

        return results

    def close(self):  # close the driver
        self.driver.quit()

    def scrape(self, date_posted: str, experience_level: str, job_title: str, location: str):

        print(
            f"Scraping jobs for '{job_title}' in '{location}' "
            f"with date_posted='{date_posted}' and experience_level='{experience_level}'..."
        )

        url = self._build_search_url(date_posted, experience_level, job_title, location)
        print(f"[Hiring Cafe] Constructed URL: {url}")

        scraped_jobs = self._scrape_logic(
            url, job_title, location, date_posted, experience_level
        )

        # Mock fallback
        if not scraped_jobs:
            scraped_jobs = [
                {
                    "JobTitle": job_title,
                    "Company": "Indeed Corp.",
                    "Location": location,
                    "URL": "https://indeed.com/viewjob?jk=abc123",
                    "Status": "New",
                    "DateFound": datetime.today().date().isoformat(),
                }
            ]

        return scraped_jobs

    def _decode_company_param(self, href):
        if "company=" not in href:
            return None
        try:
            parsed = urllib.parse.urlparse(href)  # parse the URL
            qs = urllib.parse.parse_qs(parsed.query)  # get query parameters
            if "company" in qs:  # check for 'company' param
                encoded = urllib.parse.unquote(qs["company"][0])  # URL decode
                decoded = base64.b64decode(encoded).decode()  # Base64 decode
                return decoded
        except Exception:
            pass
        return None

    def _resolve_redirect(self, href):
        try:
            r = requests.get(href, allow_redirects=True, timeout=10)  # follow redirects
            return r.url  # final URL after redirects
        except Exception:
            return href  # return original if error
