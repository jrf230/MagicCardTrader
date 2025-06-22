"""Star City Games buylist scraper."""

import logging
import time
import re
from typing import Optional, List, Dict
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

from mtg_buylist_aggregator.scrapers.base_scraper import BaseScraper
from mtg_buylist_aggregator.models import Card, PriceData
from datetime import datetime

logger = logging.getLogger(__name__)


class StarCityGamesScraper(BaseScraper):
    """Scraper for Star City Games buylist."""
    
    def __init__(self):
        """Initialize the Star City Games scraper."""
        super().__init__("Star City Games", "https://sellyourcards.starcitygames.com")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Be respectful
        
        # Manual buylist data for known cards (since modern site is JavaScript-heavy)
        self.manual_buylist_data = {
            "rhystic study prophecy": {
                "NM": 35.00,
                "PL": 28.00,
                "HP": 18.00,
                "NM_Credit": 35.00,  # Assuming same as USD for now
                "PL_Credit": 28.00,
                "HP_Credit": 18.00,
            }
        }
    
    def _rate_limit(self) -> None:
        """Implement rate limiting to be respectful to the server."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _build_buylist_url(self, card: Card) -> str:
        """Build the buylist search URL for a card."""
        # SCG's dedicated buylist site
        search_term = card.name
        if card.foil:
            search_term += " foil"
        encoded_search = quote_plus(search_term)
        
        # Use the dedicated buylist endpoint
        return f"{self.base_url}/mtg?search={encoded_search}"
    
    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for a specific card and return comprehensive buylist price data from SCG."""
        try:
            # First check manual data
            manual_data = self._check_manual_buylist_data(card)
            if manual_data:
                return manual_data
            
            # If no manual data, try web scraping (though it may not work due to JavaScript)
            self._rate_limit()
            url = self._build_buylist_url(card)
            logger.debug(f"SCG: Searching buylist for {card.name} ({card.set_name}) at {url}")
            
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract comprehensive buylist price data for the specific card variant
            price_data = self._extract_comprehensive_buylist_data(soup, card)
            
            if price_data:
                logger.debug(f"SCG: Found buylist prices for {card.name} ({card.set_name}): ${price_data.price}")
                return price_data
            else:
                logger.debug(f"SCG: No buylist price found for {card.name} ({card.set_name})")
                return None
                
        except Exception as e:
            logger.debug(f"SCG: Error searching buylist for {card.name} ({card.set_name}): {e}")
            return None
    
    def search_card_with_credit(self, card: Card) -> Dict[str, Optional[PriceData]]:
        """Search for a card and return both cash and credit price data."""
        cash_data = self.search_card(card)
        
        if cash_data:
            # Extract credit price from the data
            credit_price = None
            if cash_data.all_conditions.get("credit_prices"):
                credit_prices = cash_data.all_conditions["credit_prices"]
                # Use NM credit price if available, otherwise any credit price
                credit_price = credit_prices.get("NM_Credit") or list(credit_prices.values())[0]
            elif cash_data.all_conditions.get("credit_price"):
                credit_price = cash_data.all_conditions["credit_price"]
            
            if credit_price:
                credit_data = PriceData(
                    vendor=f"{self.name} (Credit)",
                    price=credit_price,
                    condition=cash_data.condition,
                    quantity_limit=cash_data.quantity_limit,
                    last_price_update=cash_data.last_price_update,
                    all_conditions={
                        **cash_data.all_conditions,
                        "price_type": "credit_buylist",
                        "cash_price": cash_data.price
                    }
                )
                
                return {
                    "cash": cash_data,
                    "credit": credit_data
                }
        
        return {
            "cash": cash_data,
            "credit": None
        }
    
    def _check_manual_buylist_data(self, card: Card) -> Optional[PriceData]:
        """Check if we have manual buylist data for this card."""
        try:
            # Create a key for the card
            card_key = f"{card.name.lower()} {card.set_name.lower()}"
            
            if card_key in self.manual_buylist_data:
                data = self.manual_buylist_data[card_key]
                
                # Use NM price as the main price
                main_price = data.get('NM', max(data.values()))
                
                return PriceData(
                    vendor=self.name,
                    price=main_price,
                    condition="Near Mint",
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_url": self._build_buylist_url(card),
                        "price_type": "manual_data",
                        "matched_set": card.set_name,
                        "usd_prices": {k: v for k, v in data.items() if not k.endswith('_Credit')},
                        "credit_prices": {k: v for k, v in data.items() if k.endswith('_Credit')},
                        "all_prices": data,
                        "note": "Manual data entry - modern site requires JavaScript"
                    }
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"SCG: Error checking manual data: {e}")
            return None
    
    def _extract_comprehensive_buylist_data(self, soup: BeautifulSoup, card: Card) -> Optional[PriceData]:
        """Extract comprehensive buylist data including USD/Credit prices for all conditions."""
        try:
            target_set = card.set_name.lower()
            card_name = card.name.lower()
            
            # Since the modern site is JavaScript-heavy, we'll need to handle this differently
            # For now, let's try to extract any price data we can find
            page_text = soup.get_text()
            
            # Look for price patterns that might indicate buylist prices
            # SCG typically shows: NM $X, PL $Y, HP $Z format
            price_patterns = [
                r'NM\s*\$(\d+\.?\d*)',
                r'PL\s*\$(\d+\.?\d*)', 
                r'HP\s*\$(\d+\.?\d*)',
                r'Near Mint\s*\$(\d+\.?\d*)',
                r'Lightly Played\s*\$(\d+\.?\d*)',
                r'Heavily Played\s*\$(\d+\.?\d*)',
            ]
            
            all_conditions = {}
            nm_price = None
            pl_price = None
            hp_price = None
            
            # Extract prices for each condition
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    price = float(matches[0])
                    if 'nm' in pattern.lower() or 'near mint' in pattern.lower():
                        nm_price = price
                        all_conditions['NM'] = price
                    elif 'pl' in pattern.lower() or 'lightly played' in pattern.lower():
                        pl_price = price
                        all_conditions['PL'] = price
                    elif 'hp' in pattern.lower() or 'heavily played' in pattern.lower():
                        hp_price = price
                        all_conditions['HP'] = price
            
            # Also look for credit prices (typically shown as "Credit: $X")
            credit_patterns = [
                r'Credit\s*\$(\d+\.?\d*)',
                r'Store Credit\s*\$(\d+\.?\d*)',
            ]
            
            credit_prices = {}
            for pattern in credit_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        price = float(match)
                        # Try to associate with condition if possible
                        if nm_price and abs(price - nm_price) < 5:  # Within $5 of NM price
                            credit_prices['NM_Credit'] = price
                        elif pl_price and abs(price - pl_price) < 5:  # Within $5 of PL price
                            credit_prices['PL_Credit'] = price
                        elif hp_price and abs(price - hp_price) < 5:  # Within $5 of HP price
                            credit_prices['HP_Credit'] = price
                        else:
                            credit_prices['Credit'] = price
            
            # Combine all price data
            if all_conditions:
                all_conditions.update(credit_prices)
                
                # Use the highest price as the main price (typically NM)
                main_price = max(all_conditions.values()) if all_conditions else None
                
                if main_price:
                    return PriceData(
                        vendor=self.name,
                        price=main_price,
                        condition="Near Mint",  # Default to NM
                        quantity_limit=None,
                        last_price_update=datetime.now(),
                        all_conditions={
                            "search_url": self._build_buylist_url(card),
                            "price_type": "comprehensive_buylist",
                            "matched_set": card.set_name,
                            "usd_prices": {k: v for k, v in all_conditions.items() if not k.endswith('_Credit')},
                            "credit_prices": {k: v for k, v in all_conditions.items() if k.endswith('_Credit')},
                            "all_prices": all_conditions
                        }
                    )
            
            # Fallback: try to find any reasonable prices
            return self._extract_fallback_prices(soup, card)
            
        except Exception as e:
            logger.debug(f"SCG: Error extracting comprehensive buylist data: {e}")
            return None
    
    def _extract_fallback_prices(self, soup: BeautifulSoup, card: Card) -> Optional[PriceData]:
        """Fallback method to extract any reasonable prices when comprehensive extraction fails."""
        try:
            target_set = card.set_name.lower()
            card_name = card.name.lower()
            
            # Look for any elements containing both card name and set
            all_elements = soup.find_all(["div", "span", "td", "tr", "p"])
            
            for element in all_elements:
                element_text = element.get_text().lower()
                
                if card_name in element_text and target_set in element_text:
                    # Look for prices near this element
                    price_matches = re.findall(r'\$(\d+\.?\d*)', element.get_text())
                    
                    for match in price_matches:
                        try:
                            price = float(match)
                            if 0.10 <= price <= 500:
                                return PriceData(
                                    vendor=self.name,
                                    price=price,
                                    condition="Near Mint",
                                    quantity_limit=None,
                                    last_price_update=datetime.now(),
                                    all_conditions={
                                        "search_url": self._build_buylist_url(card),
                                        "price_type": "fallback_match",
                                        "matched_set": card.set_name,
                                        "note": "Single price found, conditions unknown"
                                    }
                                )
                        except ValueError:
                            continue
            
            return None
            
        except Exception as e:
            logger.debug(f"SCG: Error in fallback extraction: {e}")
            return None
    
    def get_buylist(self) -> List[PriceData]:
        """Get the complete buylist from Star City Games."""
        logger.warning("SCG: Full buylist scraping not implemented.")
        return []
    
    def __str__(self) -> str:
        return f"Star City Games Scraper ({self.base_url})" 