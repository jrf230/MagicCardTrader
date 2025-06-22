"""General marketplace scraper for Whatnot, Mercari, Facebook Marketplace, Amazon."""

from .base_scraper import BaseScraper
from ..models import Card, PriceData
from typing import Optional, List
from datetime import datetime


class GeneralMarketplaceScraper(BaseScraper):
    """Stub: Fetches sales data from general marketplaces."""

    def __init__(self):
        super().__init__("General Marketplaces", "https://various-marketplaces.com")

    def search_card(self, card: Card) -> Optional[PriceData]:
        # TODO: Implement scraping logic for Whatnot, Mercari, Facebook Marketplace, Amazon
        return None

    def get_buylist(self) -> List[PriceData]:
        """General marketplaces don't have traditional buylists, return empty list."""
        return []
