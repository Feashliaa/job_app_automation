# backend/services/hiring_cafe.py
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
from backend.services.scrapers.base_scraper import BaseScraper

class HiringCafeScraper(BaseScraper):
    
    BASE_URL = "https://hiring.cafe/"

    DATE_POSTED_MAP = {
        "Past Month": 61, 
        "Past Week": 14, 
        "Past 24 Hours": 2
        }

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
    
    def _scrape_logic(self, url, job_title, location, date_posted, experience_level):  # core scraping logic
        self._go_to_url(url)

        # Wait for job postings to load
        self._wait_for_elements("div.relative.bg-white")

        job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.relative.bg-white")
        print(f"Found {len(job_cards)} job postings.")

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
    
    def scrape(self, date_posted, experience_level, job_title, location):
        print(
            f"[Hiring Cafe] Scraping '{job_title}' in '{location}' "
            f"({experience_level}, {date_posted})"
        )

        url = self._build_search_url(date_posted, experience_level, job_title, location)
        print(f"[Hiring Cafe] URL: {url}")

        results = self._scrape_logic(url, job_title, location, date_posted, experience_level)

        if not results:
            results = [{
                "JobTitle": job_title,
                "Company": "Hiring Cafe (Mock)",
                "Location": location,
                "URL": url,
                "Status": "New",
                "DateFound": datetime.today().date().isoformat(),
            }]

        return results