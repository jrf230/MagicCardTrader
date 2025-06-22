"""Troll and Toad scraper for buylist prices."""

from .base_scraper import BaseScraper
from ..models import Card, PriceData
from typing import Optional, List
from datetime import datetime

class TrollAndToadScraper(BaseScraper):
    """Stub: Fetches Troll and Toad buylist prices."""
    
    def __init__(self):
        super().__init__("Troll and Toad", "https://www.trollandtoad.com")
    
    def search_card(self, card: Card) -> Optional[PriceData]:
        # TODO: Implement scraping logic
        return None
    
    def get_buylist(self) -> List[PriceData]:
        """Troll and Toad buylist not implemented yet, return empty list."""
        return [] 