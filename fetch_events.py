import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from pyairtable import Api
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

# Initialize Airtable API
airtable = Api(AIRTABLE_API_KEY).table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# Setup ChromeDriver for Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

CHROMEDRIVER_PATH = "/opt/homebrew/bin/chromedriver"  # Update path as needed
chrome_service = Service(CHROMEDRIVER_PATH)

def scrape_eventbrite():
    """Scrapes event data from Eventbrite category pages."""
    
    category_urls = {
        "Product Management": "https://www.eventbrite.co.uk/d/united-kingdom--london/product-management/",
        "AI": "https://www.eventbrite.co.uk/d/united-kingdom--london/ai/",
        "Software Engineering": "https://www.eventbrite.co.uk/d/united-kingdom--london/software-development/",
        "Business Development": "https://www.eventbrite.co.uk/d/united-kingdom--london/business/",
        "Design": "https://www.eventbrite.co.uk/d/united-kingdom--london/design/",
    }
    
    events = []
    
    for category, url in category_urls.items():
        print(f"Scraping category: {category} → {url}")
        
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        driver.get(url)

        # Wait for JavaScript to load
        time.sleep(5)

        # Scroll down dynamically to load more events
        for _ in range(5):  
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        # Select event containers based on latest class
        for event in soup.find_all("div", class_="discover-search-desktop-card discover-search-desktop-card--hiddeable"):
            try:
                # Extract Title
                title_element = event.find("div", class_="Stack_root__1ksk7")
                title = title_element.text.strip() if title_element else "No Title"

                # Extract Link
                link_element = event.find("a", class_="Stack_root__1ksk7")
                link = link_element["href"] if link_element else "No Link"
                if not link.startswith("https://"):
                    link = "https://www.eventbrite.co.uk" + link

                # Extract Date
                date_element = event.find("div", class_="Typography_root__487rx Typography_body-md__487rx event-card__clamp-line--one Typography_align-match-parent__487rx")
                date = date_element.text.strip() if date_element else "No Date"

                # Extract Price
                price_element = event.find("div", class_="DiscoverHorizontalEventCard-module__priceWrapper___3rOUY")
                price = price_element.text.strip() if price_element else "Free"

                event_type = "Online" if "online" in url else "In-Person"

                events.append({
                    "Title": title,
                    "Date & Time": date,
                    "Location": "London",
                    "City": "London",
                    "Event URL": link,
                    "Description": "No Description Available",
                    "Category": category,
                    "Price": price,
                    "Event Type": event_type,
                    "Tags": [category],
                    "Image URL": "No Image"
                })

            except Exception as e:
                print(f"Error scraping an event: {e}")

    return events

def save_to_airtable(events):
    """Saves events to Airtable."""
    for event in events:
        airtable.create({
            "Title": event["Title"],
            "Date & Time": event["Date & Time"],
            "Location": event["Location"],
            "City": event["City"],
            "Event URL": event["Event URL"],
            "Description": event["Description"],
            "Category": event["Category"],
            "Price": event["Price"],
            "Event Type": event["Event Type"],
            "Tags": event["Tags"],
            "Image URL": event["Image URL"]
        })
        print(f"Added to Airtable: {event['Title']}")

def main():
    print("Scraping Eventbrite...")
    eventbrite_events = scrape_eventbrite()

    print(f"Found {len(eventbrite_events)} events. Saving to Airtable...")
    save_to_airtable(eventbrite_events)

if __name__ == "__main__":
    main()
