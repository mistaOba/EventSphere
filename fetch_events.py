import requests
import shutil
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from pyairtable import Api
from dotenv import load_dotenv
import time

# Load API keys from .env file
load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

# Initialize Airtable API
airtable = Api(AIRTABLE_API_KEY).table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# Detect OS and set ChromeDriver path
CHROMEDRIVER_PATH = shutil.which("chromedriver")  # macOS/Linux default

# If not found, fallback to a common installation path
if not CHROMEDRIVER_PATH:
    CHROMEDRIVER_PATH = "/opt/homebrew/bin/chromedriver"  # macOS M1/M2

# Setup ChromeDriver for Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

chrome_service = Service(CHROMEDRIVER_PATH)

def test_chrome():
    """Test if ChromeDriver is working."""
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.get("https://www.google.com")
    print("ChromeDriver is working:", driver.title)
    driver.quit()

def scrape_meetup():
    """Scrapes event data from Meetup's website."""
    url = "https://www.meetup.com/find/events/"
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.get(url)
    time.sleep(5)  # Allow page to load

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    events = []
    for event in soup.find_all("div", class_="eventCard--mainContent"):
        title = event.find("h3").text.strip()
        date = event.find("time").text.strip()
        link = event.find("a")["href"]

        events.append({
            "title": title,
            "date": date,
            "url": link,
            "category": "General"
        })

    return events

def scrape_eventbrite():
    """Scrapes event data from Eventbrite's website."""
    url = "https://www.eventbrite.com/d/online/all-events/"
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    events = []
    for event in soup.find_all("div", class_="eds-event-card-content__content"):
        title = event.find("div", class_="eds-event-card-content__primary-content").text.strip()
        date = event.find("div", class_="eds-text-bs").text.strip()
        link = event.find("a")["href"]

        events.append({
            "title": title,
            "date": date,
            "url": link,
            "category": "General"
        })

    return events

def scrape_luma():
    """Scrapes event data from Luma's website."""
    url = "https://lu.ma/discover"
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    events = []
    for event in soup.find_all("div", class_="css-1dbjc4n r-18u37iz r-1wbh5a2 r-1pi2tsx r-1777fci r-13qz1uu"):
        title_tag = event.find("span", class_="r-18u37iz")
        if title_tag:
            title = title_tag.text.strip()
            link_tag = event.find("a")
            link = link_tag["href"] if link_tag else "#"

            events.append({
                "title": title,
                "date": "Unknown",
                "url": link,
                "category": "General"
            })

    return events

def save_to_airtable(events):
    """Saves events to Airtable."""
    for event in events:
        airtable.create({
            "Title": event["title"],
            "Date": event["date"],
            "URL": event["url"],
            "Category": event["category"]
        })
        print(f"Added: {event['title']}")

def main():
    print("Scraping Meetup...")
    meetup_events = scrape_meetup()

    print("Scraping Eventbrite...")
    eventbrite_events = scrape_eventbrite()

    print("Scraping Luma...")
    luma_events = scrape_luma()

    all_events = meetup_events + eventbrite_events + luma_events

    print(f"Found {len(all_events)} events. Saving to Airtable...")
    save_to_airtable(all_events)

if __name__ == "__main__":
    main()
