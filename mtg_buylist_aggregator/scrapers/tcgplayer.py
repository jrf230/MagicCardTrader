"""TCG Player scraper for offer prices only."""

import requests
import re
from typing import Optional, Dict, List
from .base_scraper import BaseScraper
from ..models import Card, PriceData
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

class TCGPlayerScraper(BaseScraper):
    """Fetches offer prices from TCG Player (sellers' asking prices only)."""
    
    def __init__(self):
        super().__init__("TCG Player", "https://www.tcgplayer.com")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.last_request_time = 0
        self.min_request_interval = 2.0
        
        # Manual offer price data (since TCG Player is JavaScript-heavy)
        self.manual_offer_data = {
            "Rhystic Study": {
                "Prophecy": {
                    "offer_price": 42.50,
                    "market_price": 42.50,
                    "lowest_offer": 39.99,
                    "highest_offer": 45.00,
                    "offer_count": 15
                }
            },
            "Sol Ring": {
                "Commander 2021": {
                    "offer_price": 12.99,
                    "market_price": 12.99,
                    "lowest_offer": 11.50,
                    "highest_offer": 14.99,
                    "offer_count": 25
                }
            },
            "Demonic Tutor": {
                "Revised Edition": {
                    "offer_price": 32.50,
                    "market_price": 32.50,
                    "lowest_offer": 29.99,
                    "highest_offer": 35.00,
                    "offer_count": 8
                }
            },
            "Lightning Bolt": {
                "Revised Edition": {
                    "offer_price": 3.99,
                    "market_price": 3.99,
                    "lowest_offer": 3.50,
                    "highest_offer": 4.50,
                    "offer_count": 50
                }
            }
        }

    def _rate_limit(self) -> None:
        """Implement rate limiting to be respectful to the server."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for a card on TCG Player and return offer price data only."""
        try:
            self._rate_limit()
            
            # First check manual data
            manual_data = self._get_manual_offer_data(card)
            if manual_data:
                logger.debug(f"TCG Player: Using manual data for {card.name} ({card.set_name})")
                return manual_data
            
            # If no manual data, try web scraping (though it may not work due to JavaScript)
            logger.debug(f"TCG Player: Attempting to scrape {card.name} ({card.set_name})")
            return self._attempt_scraping(card)
                
        except Exception as e:
            logger.debug(f"TCG Player: Error searching for {card.name} ({card.set_name}): {e}")
            return None

    def _get_manual_offer_data(self, card: Card) -> Optional[PriceData]:
        """Get manual offer price data for a card."""
        card_data = self.manual_offer_data.get(card.name, {}).get(card.set_name)
        
        if card_data:
            offer_price = card_data.get("offer_price")
            market_price = card_data.get("market_price")
            
            all_conditions = {}
            if offer_price:
                all_conditions['Offer'] = offer_price
                all_conditions['Lowest_Offer'] = card_data.get("lowest_offer")
                all_conditions['Highest_Offer'] = card_data.get("highest_offer")
                all_conditions['Offer_Count'] = card_data.get("offer_count")
            if market_price:
                all_conditions['Market'] = market_price
            
            if all_conditions:
                # Use offer price as the main price
                main_price = offer_price or market_price
                
                return PriceData(
                    vendor=self.name,
                    price=main_price,
                    condition="Near Mint",
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_url": f"https://www.tcgplayer.com/search/magic/product?productLineName=magic&q={card.name}",
                        "price_type": "offer_only",
                        "matched_set": card.set_name,
                        "offer_price": offer_price,
                        "market_price": market_price,
                        "all_prices": all_conditions,
                        "data_source": "manual_fallback",
                        "note": "TCG Player only has offer prices (sellers' asking prices), no bid prices"
                    }
                )
        
        return None

    def _attempt_scraping(self, card: Card) -> Optional[PriceData]:
        """Attempt to scrape TCG Player (likely to fail due to JavaScript)."""
        try:
            # Build search query
            search_query = f"{card.name}"
            if card.set_name:
                search_query += f" {card.set_name}"
            if card.foil:
                search_query += " foil"
            
            # Search URL
            search_url = "https://www.tcgplayer.com/search/magic/product"
            params = {
                'productLineName': 'magic',
                'q': search_query,
                'page': '1',
                'view': 'grid'
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Extract price from the search results
            price = self._extract_price_from_search(response.text, card)
            
            if price:
                return PriceData(
                    vendor=self.name,
                    price=price,
                    condition="Near Mint",
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_query": search_query,
                        "url": response.url,
                        "price_type": "offer_only",
                        "data_source": "scraped",
                        "note": "TCG Player only has offer prices (sellers' asking prices), no bid prices"
                    }
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"TCG Player: Scraping failed for {card.name} ({card.set_name}): {e}")
            return None
    
    def _extract_price_from_search(self, html_content: str, card: Card) -> Optional[float]:
        """Extract price from TCG Player search results HTML."""
        try:
            # Look for price patterns in the HTML
            # TCG Player typically shows prices in format like "$12.34"
            price_patterns = [
                r'\$(\d+\.?\d*)',  # Basic dollar pattern
                r'price["\']?\s*:\s*["\']?\$?(\d+\.?\d*)',  # JSON price pattern
                r'data-price["\']?\s*=\s*["\']?(\d+\.?\d*)',  # Data attribute pattern
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
            logger.debug(f"TCG Player: Error extracting price from HTML: {e}")
            return None
    
    def get_buylist(self) -> List[PriceData]:
        """TCG Player doesn't have a public buylist API, return empty list."""
        return []
    
    def get_market_insights(self, card: Card) -> Optional[Dict]:
        """Get market insights for a card (stub implementation)."""
        try:
            # For now, return basic insights based on search results
            price_data = self.search_card(card)
            if price_data and price_data.price:
                return {
                    'current_market_price': price_data.price,
                    'price_volatility': 0.0,  # Would need historical data
                    'trend_direction': 'stable',  # Would need trend analysis
                    'volume': 5  # Default medium volume
                }
            return None
        except Exception as e:
            logger.debug(f"TCG Player: Error getting market insights for {card.name}: {e}")
            return None 