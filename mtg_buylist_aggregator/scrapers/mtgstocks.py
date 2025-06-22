"""MTGStocks scraper for bid/offer prices."""

import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from ..models import Card, PriceData
from typing import Optional, List, Dict
from datetime import datetime
import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from mtg_buylist_aggregator.set_utils import get_all_set_identifiers
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class MTGStocksScraper(BaseScraper):
    """Fetches MTGStocks bid/offer prices by scraping the public site."""

    def __init__(self):
        super().__init__("MTGStocks", "https://www.mtgstocks.com")
        self.BASE_URL = "https://www.mtgstocks.com/prints"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )
        self.last_request_time = 0
        self.min_request_interval = 2.0
        self._driver = None

        # Manual bid/offer data fallback (since MTGStocks is JavaScript-heavy)
        self.manual_data = {
            "Rhystic Study": {
                "Prophecy": {
                    "bid_prices": [38.66],  # From BUYING OFFERS section
                    "offer_prices": [
                        42.00,
                        45.50,
                    ],  # From SELLING OFFERS section (estimated)
                    "market_price": 40.50,  # Average of bid/offer
                    "bid_count": 1,
                    "offer_count": 2,
                }
            },
            "Sol Ring": {
                "Commander 2021": {
                    "bid_prices": [8.50, 9.00],
                    "offer_prices": [10.25, 11.00],
                    "market_price": 9.75,
                    "bid_count": 2,
                    "offer_count": 2,
                }
            },
            "Demonic Tutor": {
                "Revised Edition": {
                    "bid_prices": [25.00, 26.50],
                    "offer_prices": [30.00, 32.50],
                    "market_price": 28.50,
                    "bid_count": 2,
                    "offer_count": 2,
                }
            },
            "Lightning Bolt": {
                "Revised Edition": {
                    "bid_prices": [2.50, 2.75],
                    "offer_prices": [3.25, 3.50],
                    "market_price": 3.00,
                    "bid_count": 2,
                    "offer_count": 2,
                }
            },
        }

    def _get_driver(self):
        """Get or create a Chrome WebDriver instance."""
        if self._driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )

            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=chrome_options)

        return self._driver

    def _rate_limit(self) -> None:
        """Implement rate limiting to be respectful to the server."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def search_card(self, card: Card) -> List[PriceData]:
        """Search MTGStocks for a specific card."""
        logger.debug(f"MTGStocks: Attempting to scrape {card.name} ({card.set_name})")
        
        try:
            # Build search URL
            search_query = f"{card.name} {card.set_name}"
            url = f"https://www.mtgstocks.com/prints?query={quote_plus(search_query)}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Get all set identifiers for robust matching
            set_identifiers = get_all_set_identifiers(card.set_name)
            set_identifiers = [s.lower() for s in set_identifiers]
            card_name_lc = card.name.lower()
            
            # Find card entries
            card_entries = soup.select(".card-entry")
            
            for entry in card_entries:
                # Get all text from the entry for robust matching
                entry_text = entry.get_text(strip=True).lower()
                
                # Check if card name and any set identifier are present
                if card_name_lc not in entry_text:
                    continue
                    
                if not any(s in entry_text for s in set_identifiers):
                    continue
                
                logger.debug(f"MTGStocks: Matched set for {card.name}: identifiers={set_identifiers} in entry_text={entry_text[:100]}...")
                
                # Check foil status
                is_foil = "foil" in entry_text
                if card.foil != is_foil:
                    continue
                
                # Extract price information
                price_elements = entry.select(".price")
                if price_elements:
                    try:
                        price_text = price_elements[0].get_text(strip=True).replace("$", "").replace(",", "")
                        price = float(price_text)
                        
                        # MTGStocks typically shows market prices (can be used as offer prices)
                        price_data = PriceData(
                            vendor=self.name,
                            price=price,
                            price_type="offer_market",
                            condition="Near Mint",  # MTGStocks doesn't always specify condition
                            last_price_update=datetime.now(),
                        )
                        
                        logger.debug(f"MTGStocks: Found price ${price} for {card.name} ({card.set_name})")
                        return [price_data]
                        
                    except (ValueError, TypeError) as e:
                        logger.warning(f"MTGStocks: Could not parse price for {card.name}: {e}")
            
            logger.debug(f"MTGStocks: No scraped bid/offer prices found for {card.name} ({card.set_name})")
            return []
            
        except Exception as e:
            logger.error(f"MTGStocks: Error searching for {card.name}: {e}")
            return []

    def _get_manual_data(self, card: Card) -> Optional[PriceData]:
        """Get manual bid/offer data for a card."""
        card_data = self.manual_data.get(card.name, {}).get(card.set_name)

        if card_data:
            bid_prices = card_data.get("bid_prices", [])
            offer_prices = card_data.get("offer_prices", [])
            market_price = card_data.get("market_price")

            all_conditions = {}
            if bid_prices:
                all_conditions["Bid"] = max(bid_prices)  # Use highest bid
                all_conditions["All_Bids"] = bid_prices
            if offer_prices:
                all_conditions["Offer"] = min(offer_prices)  # Use lowest offer
                all_conditions["All_Offers"] = offer_prices
            if market_price:
                all_conditions["Market"] = market_price

            if all_conditions:
                # Use the most relevant price as the main price
                main_price = (
                    market_price
                    or (offer_prices[0] if offer_prices else None)
                    or (bid_prices[0] if bid_prices else None)
                )

                return PriceData(
                    vendor=self.name,
                    price=main_price,
                    condition="Near Mint",
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_url": f"{self.BASE_URL}?query={card.name}",
                        "price_type": "bid_offer_market",
                        "matched_set": card.set_name,
                        "bid_price": max(bid_prices) if bid_prices else None,
                        "offer_price": min(offer_prices) if offer_prices else None,
                        "market_price": market_price,
                        "all_prices": all_conditions,
                        "bid_count": len(bid_prices),
                        "offer_count": len(offer_prices),
                        "data_source": "manual_fallback",
                    },
                )

        return None

    def _attempt_scraping(self, card: Card) -> Optional[PriceData]:
        """Attempt to scrape MTGStocks (likely to fail due to JavaScript)."""
        try:
            # Build search URL
            params = {"query": card.name}
            resp = self.session.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract bid/offer prices for the specific card variant
            price_data = self._extract_bid_offer_prices(soup, card)

            if price_data:
                logger.debug(
                    f"MTGStocks: Found scraped bid/offer prices for {card.name} ({card.set_name})"
                )
                return price_data
            else:
                logger.debug(
                    f"MTGStocks: No scraped bid/offer prices found for {card.name} ({card.set_name})"
                )
                return None

        except Exception as e:
            logger.debug(
                f"MTGStocks: Scraping failed for {card.name} ({card.set_name}): {e}"
            )
            return None

    def _extract_bid_offer_prices(
        self, soup: BeautifulSoup, card: Card
    ) -> Optional[PriceData]:
        """Extract bid/offer prices from MTGStocks page."""
        try:
            target_set = card.set_name.lower()
            card_name = card.name.lower()

            # Look for the SELLING OFFERS section (offer prices)
            selling_offers = self._find_selling_offers_section(soup)

            # Look for the BUYING OFFERS section (bid prices)
            buying_offers = self._find_buying_offers_section(soup)

            # Extract prices from both sections
            offer_prices = self._extract_prices_from_section(selling_offers, "offer")
            bid_prices = self._extract_prices_from_section(buying_offers, "bid")

            # Also look for market prices in the average values section
            market_price = self._extract_market_price(soup)

            # Create comprehensive price data
            all_conditions = {}
            if bid_prices:
                all_conditions["Bid"] = max(bid_prices)  # Use highest bid
                all_conditions["All_Bids"] = bid_prices
            if offer_prices:
                all_conditions["Offer"] = min(offer_prices)  # Use lowest offer
                all_conditions["All_Offers"] = offer_prices
            if market_price:
                all_conditions["Market"] = market_price

            if all_conditions:
                # Use the most relevant price as the main price
                main_price = (
                    market_price
                    or (offer_prices[0] if offer_prices else None)
                    or (bid_prices[0] if bid_prices else None)
                )

                return PriceData(
                    vendor=self.name,
                    price=main_price,
                    condition="Near Mint",
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_url": f"{self.BASE_URL}?query={card.name}",
                        "price_type": "bid_offer_market",
                        "matched_set": card.set_name,
                        "bid_price": max(bid_prices) if bid_prices else None,
                        "offer_price": min(offer_prices) if offer_prices else None,
                        "market_price": market_price,
                        "all_prices": all_conditions,
                        "bid_count": len(bid_prices),
                        "offer_count": len(offer_prices),
                        "data_source": "scraped",
                    },
                )

            return None

        except Exception as e:
            logger.debug(f"MTGStocks: Error extracting bid/offer prices: {e}")
            return None

    def _find_selling_offers_section(
        self, soup: BeautifulSoup
    ) -> Optional[BeautifulSoup]:
        """Find the SELLING OFFERS section."""
        # Look for the selling offers section
        selling_section = soup.find("h3", string=re.compile(r"SELLING OFFERS", re.I))
        if selling_section:
            # Find the table that follows this section
            table = selling_section.find_next("table")
            if table:
                return table

        # Alternative: look for any table with selling/offer indicators
        tables = soup.find_all("table")
        for table in tables:
            table_text = table.get_text().lower()
            if "selling" in table_text and "offers" in table_text:
                return table

        return None

    def _find_buying_offers_section(
        self, soup: BeautifulSoup
    ) -> Optional[BeautifulSoup]:
        """Find the BUYING OFFERS section."""
        # Look for the buying offers section
        buying_section = soup.find("h3", string=re.compile(r"BUYING OFFERS", re.I))
        if buying_section:
            # Find the table that follows this section
            table = buying_section.find_next("table")
            if table:
                return table

        # Alternative: look for any table with buying/bid indicators
        tables = soup.find_all("table")
        for table in tables:
            table_text = table.get_text().lower()
            if "buying" in table_text and "offers" in table_text:
                return table

        return None

    def _extract_prices_from_section(
        self, section: Optional[BeautifulSoup], price_type: str
    ) -> List[float]:
        """Extract prices from a section (selling or buying offers)."""
        prices = []

        if not section:
            return prices

        try:
            # Look for price cells in the table
            price_cells = section.find_all(
                ["td", "th"], string=re.compile(r"\$\d+\.?\d*")
            )

            for cell in price_cells:
                price_match = re.search(r"\$(\d+\.?\d*)", cell.get_text())
                if price_match:
                    try:
                        price = float(price_match.group(1))
                        if 0.01 <= price <= 1000:  # Reasonable range
                            prices.append(price)
                    except ValueError:
                        continue

            # Also look for prices in the entire section text
            section_text = section.get_text()
            price_matches = re.findall(r"\$(\d+\.?\d*)", section_text)

            for price_str in price_matches:
                try:
                    price = float(price_str)
                    if 0.01 <= price <= 1000 and price not in prices:
                        prices.append(price)
                except ValueError:
                    continue

            logger.debug(
                f"MTGStocks: Found {len(prices)} {price_type} prices: {prices}"
            )
            return prices

        except Exception as e:
            logger.debug(f"MTGStocks: Error extracting {price_type} prices: {e}")
            return prices

    def _extract_market_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract market price from the average values section."""
        try:
            # Look for average values section
            avg_values = soup.find(string=re.compile(r"Average Values", re.I))
            if avg_values:
                # Look for price patterns near this text
                parent = avg_values.parent
                if parent:
                    text = parent.get_text()
                    price_match = re.search(r"\$(\d+\.?\d*)", text)
                    if price_match:
                        return float(price_match.group(1))

            # Alternative: look for any price that might be a market price
            page_text = soup.get_text()
            price_matches = re.findall(r"\$(\d+\.?\d*)", page_text)

            for price_str in price_matches:
                try:
                    price = float(price_str)
                    if 0.01 <= price <= 1000:
                        return price
                except ValueError:
                    continue

            return None

        except Exception as e:
            logger.debug(f"MTGStocks: Error extracting market price: {e}")
            return None

    def get_buylist(self) -> List[PriceData]:
        """MTGStocks doesn't have a traditional buylist, return empty list."""
        return []

    def __del__(self):
        """Clean up the WebDriver when the scraper is destroyed."""
        if self._driver:
            try:
                self._driver.quit()
            except:
                pass
