"""Card Kingdom buylist scraper."""

import logging
import time
import json
import re
from typing import Optional, List, Dict
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

from mtg_buylist_aggregator.scrapers.base_scraper import BaseScraper
from mtg_buylist_aggregator.models import Card, PriceData
from datetime import datetime
from mtg_buylist_aggregator.set_utils import get_all_set_identifiers

logger = logging.getLogger(__name__)


class CardKingdomScraper(BaseScraper):
    """Scraper for Card Kingdom buylist and retail prices."""

    def __init__(self):
        """Initialize the Card Kingdom scraper."""
        super().__init__("Card Kingdom", "https://www.cardkingdom.com")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.cardkingdom.com/",
            }
        )
        self.last_request_time = 0
        self.min_request_interval = 1.5  # Be respectful but a bit faster

    def _rate_limit(self) -> None:
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def _build_search_url(self, card: Card, is_buylist: bool) -> str:
        """Builds a search URL for Card Kingdom for either retail or buylist."""
        card_name = quote_plus(card.name)
        if is_buylist:
            # Buylist search URL structure
            return f"{self.base_url}/purchasing/mtg_singles?filter%5Bsearch%5D=mtg_advanced&filter%5Bname%5D={card_name}&filter%5Bfoils%5D={'1' if card.foil else '0'}"
        else:
            # Retail search URL structure
            return f"{self.base_url}/catalog/search?search=header&filter%5Bname%5D={card_name}"

    def search_card(self, card: Card) -> List[PriceData]:
        """Search Card Kingdom and return a list of all available prices."""
        all_prices: List[PriceData] = []

        try:
            # 1. Get buylist prices (cash and credit)
            buylist_prices = self._search_buylist(card)
            all_prices.extend(buylist_prices)
        except Exception as e:
            logger.error(f"CK: Failed to scrape buylist for {card.name}: {e}")

        try:
            # 2. Get retail prices for all conditions
            retail_prices = self._search_retail(card)
            all_prices.extend(retail_prices)
        except Exception as e:
            logger.error(f"CK: Failed to scrape retail for {card.name}: {e}")

        return all_prices

    def _get_set_code(self, card: Card) -> str:
        """Get the set code for a card, using Scryfall if needed."""
        if card.set_code:
            return card.set_code.lower()
        # Try to get set code from Scryfall
        try:
            resp = requests.get(f"https://api.scryfall.com/sets", timeout=10)
            resp.raise_for_status()
            sets = resp.json().get("data", [])
            for s in sets:
                if s["name"].lower() == card.set_name.lower():
                    return s["code"].lower()
        except Exception as e:
            logger.warning(f"CK: Failed to get set code from Scryfall for {card.set_name}: {e}")
        return ""

    def _matches_set(self, card: Card, text: str) -> bool:
        """Return True if the set name or set code matches anywhere in the text."""
        set_code = self._get_set_code(card)
        set_name = card.set_name.lower()
        text = text.lower()
        if set_name in text:
            logger.debug(f"CK: Matched set name '{set_name}' in text")
            return True
        if set_code and set_code in text:
            logger.debug(f"CK: Matched set code '{set_code}' in text")
            return True
        return False

    def _search_buylist(self, card: Card) -> List[PriceData]:
        """Extracts buylist prices (cash and credit). Returns a list of PriceData."""
        self._rate_limit()
        url = self._build_search_url(card, is_buylist=True)
        logger.debug(
            f"CK: Searching buylist for {card.name} ({card.set_name}) at {url}"
        )

        resp = self.session.get(url, timeout=20)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[PriceData] = []

        set_identifiers = get_all_set_identifiers(card.set_name)
        set_identifiers = [s.lower() for s in set_identifiers]
        card_name_lc = card.name.lower()

        item_rows = soup.select("div.itemContentWrapper")

        for item in item_rows:
            item_text = item.get_text(strip=True).lower()
            # Check if the card name matches
            if card_name_lc not in item_text:
                continue
            # Check if any set identifier matches
            if not any(s in item_text for s in set_identifiers):
                continue
            logger.debug(f"CK: Matched set for {card.name}: identifiers={set_identifiers} in item_text={item_text}")
            # Check foil
            set_name_div = item.select_one("div.productDetailTitle")
            is_foil_row = set_name_div and "foil" in set_name_div.get_text(strip=True).lower()
            if card.foil != is_foil_row:
                continue
            price_div = item.select_one("div.usd.price")
            qty_input = item.select_one('input[name="sell_quantity[1]"]')
            if price_div and qty_input:
                try:
                    price_str = price_div.get_text(strip=True).replace("$", "")
                    price = float(price_str)
                    cash_price_data = PriceData(
                        vendor=self.name,
                        price=price,
                        price_type="bid_cash",
                        condition="Near Mint",
                        quantity_limit=None,
                        last_price_update=datetime.now(),
                    )
                    results.append(cash_price_data)
                    credit_price = round(price * 1.30, 2)
                    credit_price_data = PriceData(
                        vendor=self.name,
                        price=credit_price,
                        price_type="bid_credit",
                        condition="Near Mint",
                        quantity_limit=None,
                        last_price_update=datetime.now(),
                    )
                    results.append(credit_price_data)
                    logger.debug(
                        f"CK: Found buylist prices for {card.name} ({card.set_name}): Cash ${price}, Credit ${credit_price}"
                    )
                    return results
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"CK: Could not parse price for {card.name} ({card.set_name}): {e}"
                    )
        logger.debug(
            f"CK: No matching buylist version found for {card.name} ({card.set_name})"
        )
        return []

    def _search_retail(self, card: Card) -> List[PriceData]:
        """Extracts retail prices for all available conditions. Returns a list of PriceData."""
        self._rate_limit()
        url = self._build_search_url(card, is_buylist=False)
        logger.debug(f"CK: Searching retail for {card.name} at {url}")

        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except requests.exceptions.RequestException as e:
            logger.error(f"CK: Request failed for retail search of {card.name}: {e}")
            return []

        results: List[PriceData] = []

        set_identifiers = get_all_set_identifiers(card.set_name)
        set_identifiers = [s.lower() for s in set_identifiers]
        card_name_lc = card.name.lower()

        # Find all product cards on the page
        product_items = soup.select("div.productItemWrapper")

        for item in product_items:
            item_text = item.get_text(strip=True).lower()
            if card_name_lc not in item_text:
                continue
            if not any(s in item_text for s in set_identifiers):
                continue
            logger.debug(f"CK: Matched set for {card.name}: identifiers={set_identifiers} in item_text={item_text}")
            is_foil_item = False
            for selector in ["span.productDetailTitle", "div.productDetailTitle", "h3.productDetailTitle", "a.productDetailTitle", ".productDetailTitle"]:
                title_div = item.select_one(selector)
                if title_div and "foil" in title_div.get_text(strip=True).lower():
                    is_foil_item = True
                    break
            if card.foil != is_foil_item:
                continue

            # Find all condition versions for this item
            condition_items = item.select("div.itemContentWrapper")
            for cond_item in condition_items:
                condition_div = cond_item.select_one("div.style")
                price_div = cond_item.select_one("span.price")

                if condition_div and price_div:
                    try:
                        condition_str = condition_div.get_text(strip=True)
                        price_str = price_div.get_text(strip=True).replace("$", "")

                        condition = self._normalize_condition(condition_str)
                        price = float(price_str)

                        if condition:
                            results.append(
                                PriceData(
                                    vendor=f"{self.name} (Retail)",
                                    price=price,
                                    price_type=f"offer_{condition.lower().replace(' ', '_')}",
                                    condition=condition,
                                    last_price_update=datetime.now(),
                                )
                            )
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"CK: Could not parse retail price/condition for {card.name}: {e}"
                        )

            if results:
                logger.debug(
                    f"CK: Found {len(results)} retail prices for {card.name} ({card.set_name})"
                )
                return results  # Found the correct item, stop searching

        logger.debug(f"CK: No retail item found for {card.name} ({card.set_name})")
        return []

    def _normalize_condition(self, cond_str: str) -> Optional[str]:
        """Normalize Card Kingdom condition strings."""
        cond_lower = cond_str.lower()
        if "near mint" in cond_lower or "nm" in cond_lower:
            return "Near Mint"
        if (
            "excellent" in cond_lower or "ex" in cond_lower or "g (vg)" in cond_lower
        ):  # "G (VG)" is their "Good"
            return "Excellent"
        if "played" in cond_lower or "pl" in cond_lower:
            return "Played"
        if "good" in cond_lower or "g" in cond_lower:
            return "Good"
        # Add other conditions as needed
        logger.debug(f"CK: Unknown condition '{cond_str}'")
        return None

    def get_buylist(self) -> List[PriceData]:
        """
        Main entry point for getting the entire Card Kingdom buylist.
        NOTE: Scraping the entire buylist is a heavy operation and not implemented.
        This scraper is designed to be used for targeted card searches.
        """
        logger.warning(
            "CK: Scraping the entire buylist is not supported. Use search_card instead."
        )
        return []

    def __str__(self) -> str:
        """String representation of the scraper."""
        return f"<CardKingdomScraper last_request={self.last_request_time}>"

    def get_retail_prices_by_condition(self, card: Card) -> Dict[str, PriceData]:
        """Convenience function to get a dict of retail prices keyed by condition."""
        retail_prices = self._search_retail(card)
        return {price.condition: price for price in retail_prices if price.condition}


# ... rest of the file ...
