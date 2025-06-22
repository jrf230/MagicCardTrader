"""MagicCardPrices.io scraper for market price and trend data."""

from .base_scraper import BaseScraper
from ..models import Card, PriceData
from typing import Optional, List
from datetime import datetime

class MagicCardPricesScraper(BaseScraper):
    """Stub: Fetches MagicCardPrices.io market price and trend data."""
    
    def __init__(self):
        super().__init__("MagicCardPrices.io", "https://magiccardprices.io")
    
    def search_card(self, card: Card) -> Optional[PriceData]:
        # TODO: Implement scraping logic
        return None
    
    def get_buylist(self) -> List[PriceData]:
        """MagicCardPrices.io doesn't have a traditional buylist, return empty list."""
        return [] 