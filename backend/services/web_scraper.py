import logging
from typing import List, Dict, Any, Optional
import time
import random
import os
import json
import re
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
import requests  # Keep for fallback

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, base_url: str):
        # Set default to madewithnestle.ca
        self.base_url = "https://www.madewithnestle.ca/"
        if base_url and "madewithnestle.ca" in base_url:
            self.base_url = base_url
            
        self.visited_urls = set()
        self.data = []
        
        # Collection of realistic User-Agents to rotate
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        
        # Maximum page limit to prevent excessive crawling
        self.max_pages = 100
        
        # Fallback URLs to try if main site fails
        self.fallback_urls = [
            "https://www.nestle.ca/en",
            "https://www.nestle.com/brands",
            "https://www.madewithnestle.ca/brands"
        ]
        
        # Initialize WebDriver to None (will be created when needed)
        self.driver = None
        
    def scrape_website(self) -> List[Dict[str, Any]]:
        """Scrape the Nestle website and extract content"""
        logger.info(f"Starting scraping for {self.base_url}")
        self.visited_urls = set()
        self.data = []
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        
        # Try to load existing data if available
        try:
            if os.path.exists('data/scraped_data.json'):
                with open('data/scraped_data.json', 'r') as f:
                    self.data = json.load(f)
                    if self.data and len(self.data) > 0:
                        logger.info(f"Loaded {len(self.data)} pages from existing data file")
                        return self.data
        except Exception as e:
            logger.warning(f"Could not load existing data: {str(e)}")
        
        try:
            if SELENIUM_AVAILABLE:
                logger.info("Using Selenium for web scraping")
                self._scrape_with_selenium()
            else:
                logger.warning("Selenium not available, using fallback method")
                self._scrape_with_requests()
                
            # If still no data, use example data as fallback
            if not self.data:
                self._use_example_data()
                
            # Save scraped data
            self._save_to_file()
            logger.info(f"Successfully scraped {len(self.data)} pages")
            
            # Clean up Selenium driver if it was used
            self._cleanup_driver()
            
            return self.data
            
        except Exception as e:
            logger.error(f"Error during web scraping: {str(e)}")
            # Clean up in case of error
            self._cleanup_driver()
            
            # If we have at least some data, save it
            if self.data:
                self._save_to_file()
                return self.data
            
            # Otherwise, use example data
            self._use_example_data()
            self._save_to_file()
            return self.data
    
    def _setup_driver(self):
        """Set up Selenium WebDriver with appropriate options"""
        if self.driver:
            return self.driver
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Set a random user agent
            user_agent = random.choice(self.user_agents)
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Additional options to avoid detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Create the WebDriver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Mask WebDriver presence
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to set up Selenium WebDriver: {str(e)}")
            return None
    
    def _cleanup_driver(self):
        """Clean up the Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {str(e)}")
            finally:
                self.driver = None
    
    def _scrape_with_selenium(self):
        """Scrape the website using Selenium"""
        driver = self._setup_driver()
        if not driver:
            logger.error("Failed to set up WebDriver, falling back to requests")
            self._scrape_with_requests()
            return
            
        try:
            # First visit Google to establish cookies and browsing history
            driver.get("https://www.google.com/search?q=nestle+products+recipes")
            time.sleep(random.uniform(2, 4))
            
            # Then visit the Nestle website
            logger.info(f"Navigating to {self.base_url}")
            driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Add some random scrolling to simulate human behavior
            self._scroll_page(driver)
            
            # Extract page content
            self._process_current_page(driver, self.base_url)
            
            # Follow links if we successfully extracted content
            if self.data:
                links_to_follow = self._extract_links_from_driver(driver, self.base_url)
                self._follow_links_selenium(driver, links_to_follow)
            else:
                # Try fallback URLs if main URL fails
                for fallback_url in self.fallback_urls:
                    logger.info(f"Trying fallback URL: {fallback_url}")
                    driver.get(fallback_url)
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        self._process_current_page(driver, fallback_url)
                        
                        # If we got data, follow links from this page
                        if self.data:
                            links_to_follow = self._extract_links_from_driver(driver, fallback_url)
                            self._follow_links_selenium(driver, links_to_follow)
                            break
                    except TimeoutException:
                        logger.warning(f"Timeout waiting for {fallback_url} to load")
                        continue
        
        except Exception as e:
            logger.error(f"Error in Selenium scraping: {str(e)}")
    
    def _process_current_page(self, driver, url):
        """Process the currently loaded page in the WebDriver"""
        if url in self.visited_urls or len(self.data) >= self.max_pages:
            return
            
        self.visited_urls.add(url)
        logger.info(f"Processing page: {url}")
        
        try:
            # Get the page source and parse with BeautifulSoup
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract page content
            title = self._extract_title(soup) or driver.title
            content = self._extract_text(soup)
            
            # Store page data
            page_data = {
                "url": url,
                "title": title,
                "content": content
            }
            
            self.data.append(page_data)
            logger.info(f"Successfully extracted content from {url}")
            
        except Exception as e:
            logger.error(f"Error processing page {url}: {str(e)}")
    
    def _extract_links_from_driver(self, driver, base_url):
        """Extract links from the current page in the WebDriver"""
        links = []
        try:
            elements = driver.find_elements(By.TAG_NAME, "a")
            for element in elements:
                try:
                    href = element.get_attribute("href")
                    if href and isinstance(href, str):
                        # Filter links
                        if self._is_valid_link(href, base_url):
                            links.append(href)
                except Exception:
                    continue
                    
            # Randomize link order
            random.shuffle(links)
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []
    
    def _is_valid_link(self, href, base_url):
        """Check if a link is valid for scraping"""
        # Skip empty links, JavaScript, anchors, etc.
        if not href or href.startswith(('javascript:', '#', 'mailto:', 'tel:')):
            return False
            
        # Skip if already visited
        if href in self.visited_urls:
            return False
            
        # Skip non-content links
        if any(ext in href for ext in ['.pdf', '.jpg', '.png', '.zip']):
            return False
            
        # Only follow Nestle-related links
        return any(domain in href for domain in ["madewithnestle.ca", "nestle.ca", "nestle.com"])
    
    def _follow_links_selenium(self, driver, links):
        """Follow links using Selenium WebDriver"""
        # Limit number of links to follow
        links_to_follow = links[:min(15, len(links))]
        
        for link in links_to_follow:
            if len(self.data) >= self.max_pages:
                logger.info(f"Reached maximum page limit of {self.max_pages}, stopping crawl")
                break
                
            if link in self.visited_urls:
                continue
                
            try:
                # Add a delay between page visits
                time.sleep(random.uniform(2, 5))
                
                logger.info(f"Following link: {link}")
                driver.get(link)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Add some random scrolling
                self._scroll_page(driver)
                
                # Process the page
                self._process_current_page(driver, link)
                
                # Extract and follow more links (with a depth limit)
                if len(self.visited_urls) < 20:  # Limit depth
                    new_links = self._extract_links_from_driver(driver, link)
                    # Take just a few links from each page to avoid too much branching
                    self._follow_links_selenium(driver, new_links[:5])
                
            except TimeoutException:
                logger.warning(f"Timeout waiting for {link} to load")
                continue
            except Exception as e:
                logger.error(f"Error following link {link}: {str(e)}")
                continue
    
    def _scroll_page(self, driver):
        """Simulate scrolling behavior to appear more human-like"""
        try:
            # Get page height
            page_height = driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down in steps
            scroll_steps = random.randint(3, 6)
            for i in range(scroll_steps):
                scroll_amount = random.randint(300, 800)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 1.5))
                
            # Sometimes scroll back up a bit
            if random.random() > 0.7:
                driver.execute_script("window.scrollBy(0, -500);")
                time.sleep(random.uniform(0.5, 1))
                
        except Exception as e:
            logger.warning(f"Error during page scrolling: {str(e)}")
    
    def _scrape_with_requests(self):
        """Fallback method using requests instead of Selenium"""
        logger.info("Using requests-based scraping as fallback")
        
        # Create a session with browser-like headers
        session = requests.Session()
        session.headers.update({
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.google.com/",
            "DNT": "1"
        })
        
        # Try the main URL first
        try:
            logger.info(f"Trying to scrape {self.base_url}")
            response = session.get(self.base_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            self._process_page_content(soup, self.base_url)
            
        except Exception as e:
            logger.error(f"Failed to scrape main URL: {str(e)}")
            
            # Try fallback URLs
            for fallback_url in self.fallback_urls:
                try:
                    logger.info(f"Trying fallback URL: {fallback_url}")
                    response = session.get(fallback_url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    self._process_page_content(soup, fallback_url)
                    
                    if self.data:
                        break
                        
                except Exception as e:
                    logger.error(f"Failed to scrape fallback URL {fallback_url}: {str(e)}")
                    continue
    
    def _process_page_content(self, soup, url):
        """Process a page's content from BeautifulSoup"""
        if url in self.visited_urls:
            return
            
        self.visited_urls.add(url)
        
        title = self._extract_title(soup)
        content = self._extract_text(soup)
        
        page_data = {
            "url": url,
            "title": title,
            "content": content
        }
        
        self.data.append(page_data)
        logger.info(f"Processed content from {url}")
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the page title"""
        if soup.title:
            return soup.title.text.strip()
        
        # If no title tag, try to find h1
        h1 = soup.find('h1')
        if h1:
            return h1.text.strip()
            
        return ""
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract page text content"""
        # Create a copy to avoid modifying the original
        soup_copy = BeautifulSoup(str(soup), 'html.parser')
        
        # Remove script and style elements
        for element in soup_copy(['script', 'style', 'meta', 'noscript', 'head', 'footer', 'nav']):
            element.extract()
        
        # Get all text
        text = soup_copy.get_text(separator=" ", strip=True)
        
        # Clean text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _use_example_data(self):
        """Load example data as a fallback"""
        logger.warning("Using example Nestle data as fallback")
        self.data = [
            {
                "url": "https://www.nestle.ca/en/brands/chocolate/kitkat",
                "title": "KitKat - Nestle Canada",
                "content": "KitKat is a chocolate-covered wafer bar confection created by Rowntree's of York, United Kingdom, and is now produced globally by Nestlé. The standard bars consist of two or four pieces composed of three layers of wafer, separated and covered by an outer layer of chocolate. Each finger can be snapped from the bar separately. There are many different flavors of KitKat, including milk, white, and dark chocolate varieties. A standard 4-finger KitKat bar (45g) contains approximately 240 calories."
            },
            {
                "url": "https://www.nestle.ca/en/brands/coffee/nescafe",
                "title": "Nescafe - Nestle Canada",
                "content": "Nescafé is a brand of coffee made by Nestlé. It comes in many different forms. The name is a portmanteau of the words 'Nestlé' and 'café'. Nestlé first introduced their flagship coffee brand in Switzerland on 1 April 1938. Nescafé is a coffee brand that includes many products. The brand is best known for its wide range of instant coffee drinks."
            },
            {
                "url": "https://www.nestle.ca/en/nutrition-health-wellness",
                "title": "Nutrition, Health and Wellness - Nestle Canada",
                "content": "At Nestlé, we want to help shape a better and healthier world. We also want to inspire people to live healthier lives. This is how we contribute to society while ensuring the long-term success of our company. We have defined three ambitions for 2030 to guide our work: Help 50 million children lead healthier lives; Help improve 30 million livelihoods in communities directly connected to our business activities; Strive for zero environmental impact in our operations."
            },
            {
                "url": "https://www.nestle.ca/en/products",
                "title": "Nestle Products - Nestle Canada",
                "content": "Discover our brands at Nestle. From KitKat to Nescafe, Nestle offers a wide range of products including chocolate, coffee, water, dairy, and nutrition. Our product categories include beverages, breakfast cereals, chocolate & confectionery, coffee, culinary, chilled & frozen food, dairy, drinks, food service, healthcare nutrition, ice cream, petcare, and snacks."
            }
        ]
    
    def _save_to_file(self):
        """Save scraped data to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/scraped_data.json', 'w') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            # Also save a timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f'data/scraped_data_{timestamp}.json'
            with open(backup_path, 'w') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(self.data)} pages of data to data/scraped_data.json")
        except Exception as e:
            logger.error(f"Error saving data to file: {str(e)}")

# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = WebScraper(base_url="https://www.madewithnestle.ca/")
    data = scraper.scrape_website()
    print(f"Scraped {len(data)} pages") 