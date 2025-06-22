"""Base scraper class for MTG buylist scrapers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from mtg_buylist_aggregator.models import Card, PriceData


class BaseScraper(ABC):
    """Abstract base class for all MTG buylist scrapers."""
    
    def __init__(self, name: str, base_url: str):
        """Initialize the scraper.
        
        Args:
            name: Name of the scraper
            base_url: Base URL for the website
        """
        self.name = name
        self.base_url = base_url
    
    @abstractmethod
    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for a specific card and return price data.
        
        Args:
            card: Card to search for
            
        Returns:
            PriceData if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_buylist(self) -> List[PriceData]:
        """Get the complete buylist from the website.
        
        Returns:
            List of PriceData objects
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.name} Scraper ({self.base_url})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', base_url='{self.base_url}')" 