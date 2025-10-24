import urllib.parse
import json
from datetime import datetime
from backend.services.scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By


class LinkedInScraper(BaseScraper):

    COMPANYS_TO_IGNORE = {
        "Jobs via Dice",
        "Mindrift",
        "DataAnnotation",
        "CyberCoders"
    }

    BASE_URL = "https://www.linkedin.com/jobs/search/"
    GEO_ID_US = 103644278

    EXPERIENCE_LEVEL_MAP = {
        "Entry Level": 2, 
        "Mid Level": 3, 
        "Senior Level": 4
    }
    
    DATE_POSTED_MAP = {
        "Past 24 Hours": "r86400",
        "Past Week": "r604800",
        "Past Month": "r2592000",
    }
    
    WORKPLACE_TYPE_MAP = {
        "On-site": 1, 
        "Remote": 2, 
        "Hybrid": 3
    }

    def _build_search_url(self, date_posted, experience_level, job_title, location):
        params = {
            "f_E": self.EXPERIENCE_LEVEL_MAP.get(experience_level, 2),
            "f_TPR": self.DATE_POSTED_MAP.get(date_posted, "r604800"),
            "keywords": job_title.replace(" ", " "),
            "geoId": self.GEO_ID_US,
            "f_WT": self._get_workplace_type(location),
            "origin": "JOB_SEARCH_PAGE_JOB_FILTER",
            "refresh": "true",
        }
        query = urllib.parse.urlencode(params)
        return f"{self.BASE_URL}?{query}"

    def _get_workplace_type(self, location):
        return self.WORKPLACE_TYPE_MAP["Remote"] if "remote" in location.lower() else self.WORKPLACE_TYPE_MAP["On-site"]

    def scrape(self, date_posted, experience_level, job_title, location):
        url = self._build_search_url(date_posted, experience_level, job_title, location)
        print(f"[LinkedIn] URL: {url}")

        results = self._scrape_logic(url, job_title, location, date_posted, location)
        
        if not results:
            results = [{
                "JobTitle": job_title,
                "Company": "LinkedIn (Mock)",
                "Location": location,
                "URL": url,
                "Status": "New",
                "DateFound": datetime.today().date().isoformat(),
            }]
        
        return results

    def _scrape_logic(self, url, job_title, location, date_posted, experience_level):
        
        print("Entered _scrape_logic")
        
        self._go_to_url(url)
        
        self._wait_for_elements("ul.jobs-search__results-list")
        
        print(f"Found Element")
        
            # Then get each job card within it
        job_cards = self.driver.find_elements(
            By.CSS_SELECTOR, "ul.jobs-search__results-list div.base-card.base-search-card"
        )
        
        print(f"Found {len(job_cards)} job postings.")
        
        ignore_set = {company.lower() for company in self.COMPANYS_TO_IGNORE}

        results = []
        
        for card in job_cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text.strip()
            except:
                title = "N/A"
            try:
                company = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle a").text.strip()
            except:
                company = "N/A"
            try:
                loc = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location").text.strip()
            except:
                loc = location or "N/A"
            try:
                link = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
            except:
                link = "N/A"
            try:
                posted_date = card.find_element(By.CSS_SELECTOR, "time").get_attribute("datetime")
            except:
                posted_date = datetime.today().date().isoformat()
                
            if company.strip().lower() in ignore_set:
                print(f"Skipping {company}")
                continue
            
            results.append(
                {
                    "JobTitle": title,
                    "Company": company,
                    "Location": loc,
                    "URL": link,
                    "Status": "New",
                    "DateFound": datetime.today().date().isoformat(),
                    "DatePosted": posted_date,
                }
            )

        print(f"\nExtracted {len(results)} jobs:")
        for job in results:
            print(f"- {job['JobTitle']} at {job['Company']} ({job['URL']})")
            
                
        input("Press Enter")
        
        
        return results