"""MTGGoldfish scraper for real price data."""

import requests
import re
import logging
from typing import Optional, Dict, List
from .base_scraper import BaseScraper
from ..models import Card, PriceData
from datetime import datetime
import time


class MTGGoldfishScraper(BaseScraper):
    """Fetches real price data from MTGGoldfish."""

    def __init__(self):
        super().__init__("MTGGoldfish", "https://www.mtggoldfish.com")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        self.logger = logging.getLogger(__name__)

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for a card on MTGGoldfish and extract price data."""
        try:
            # Build search query
            search_query = f"{card.name}"
            if card.set_name:
                search_query += f" {card.set_name}"
            if card.foil:
                search_query += " foil"

            # MTGGoldfish search URL
            search_url = "https://www.mtggoldfish.com/search"
            params = {"q": search_query}

            # Add delay to be respectful
            time.sleep(1)

            response = self.session.get(search_url, params=params, timeout=15)
            response.raise_for_status()

            # Extract price from the search results
            price = self._extract_price_from_search(response.text, card)

            if price:
                return PriceData(
                    vendor="MTGGoldfish",
                    price=price,
                    condition="Near Mint",
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={"search_query": search_query, "url": response.url},
                )

            return None

        except Exception as e:
            self.logger.debug(f"Error searching MTGGoldfish for {card.name}: {e}")
            return None

    def _extract_price_from_search(
        self, html_content: str, card: Card
    ) -> Optional[float]:
        """Extract price from MTGGoldfish search results HTML."""
        try:
            # Look for price patterns in the HTML
            # MTGGoldfish typically shows prices in format like "$12.34"
            price_patterns = [
                r"\$(\d+\.?\d*)",  # Basic dollar pattern
                r'price["\']?\s*:\s*["\']?\$?(\d+\.?\d*)',  # JSON price pattern
                r'data-price["\']?\s*=\s*["\']?(\d+\.?\d*)',  # Data attribute pattern
                r'class="price["\']?\s*[^>]*>\s*\$?(\d+\.?\d*)',  # Price class pattern
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    # Convert to float and return the first reasonable price
                    for match in matches:
                        try:
                            price = float(match)
                            if 0.01 <= price <= 10000:  # Reasonable price range
                                return price
                        except ValueError:
                            continue

            return None

        except Exception as e:
            self.logger.debug(f"Error extracting price from MTGGoldfish HTML: {e}")
            return None

    def get_buylist(self) -> List[PriceData]:
        """MTGGoldfish doesn't have a public buylist API, return empty list."""
        return []
