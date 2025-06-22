"""Cardmarket scraper for European prices and buylist data."""

import requests
from .base_scraper import BaseScraper
from ..models import Card, PriceData
from typing import Optional, List
from datetime import datetime
import re


class CardmarketScraper(BaseScraper):
    """Fetches Cardmarket prices by scraping the public site (lowest available price)."""

    def __init__(self):
        super().__init__("Cardmarket", "https://www.cardmarket.com")
        self.BASE_URL = "https://www.cardmarket.com/en/Magic/Products/Singles"

    def search_card(self, card: Card) -> Optional[PriceData]:
        # Build search URL
        params = {"searchString": card.name}
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            html = resp.text
            # Find the first price in the search results (EUR)
            price_match = re.search(r"\u20ac\s*([\d,.]+)", html)
            if price_match:
                price_eur = float(
                    price_match.group(1).replace(",", "").replace(".", ".")
                )
                return PriceData(
                    vendor="Cardmarket",
                    price=price_eur,
                    condition="Near Mint",
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={"currency": "EUR"},
                )
            return None
        except Exception:
            return None

    def get_buylist(self) -> List[PriceData]:
        """Cardmarket buylist not implemented yet, return empty list."""
        return []
