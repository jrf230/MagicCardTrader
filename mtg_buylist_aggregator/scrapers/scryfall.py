"""Scryfall scraper for card metadata and price links."""

import requests
from typing import Optional, Dict, List
from .base_scraper import BaseScraper
from ..models import Card, PriceData, Condition
from datetime import datetime
import logging


class ScryfallScraper(BaseScraper):
    """Scraper for Scryfall, primarily for market prices."""

    def __init__(self):
        super().__init__("Scryfall", "https://api.scryfall.com")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.BASE_URL = "https://api.scryfall.com/cards/named"

    def search_card(self, card: Card) -> List[PriceData]:
        """Search Scryfall and return a list of PriceData objects."""
        try:
            # Build search parameters
            params = {"fuzzy": card.name}
            if card.set_name:
                # Try exact set match first
                try:
                    set_params = {
                        "exact": card.name,
                        "set": card.set_name.lower().replace(" ", "-"),
                    }
                    resp = requests.get(self.BASE_URL, params=set_params, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        return self._parse_scryfall_data(data, card)
                except:
                    pass  # Fall back to fuzzy search

            # Fuzzy search as fallback
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            return self._parse_scryfall_data(data, card)

        except Exception as e:
            self.logger.debug(f"Error searching Scryfall for {card.name}: {e}")
            return []

    def _parse_scryfall_data(self, data: Dict, card: Card) -> List[PriceData]:
        """Parse Scryfall API response into PriceData."""
        try:
            # Handle cases where Scryfall returns a list of cards for a fuzzy match
            if data.get("object") == "list":
                self.logger.debug(
                    f"Scryfall returned a list for {card.name}. Searching for best match..."
                )
                # Try to find the exact set match from the list
                for card_data in data.get("data", []):
                    if card_data.get("set_name", "").lower() == card.set_name.lower():
                        data = card_data
                        self.logger.debug(
                            f"Found exact set match in list: {card.set_name}"
                        )
                        break
                else:
                    # If no exact match, use the first result as a fallback
                    data = data.get("data", [{}])[0]
                    self.logger.debug(
                        "No exact set match found, using first result from list."
                    )

            # Get prices
            prices = data.get("prices", {})
            if not prices:
                self.logger.warning(
                    f"No price data in Scryfall response for {card.name}"
                )
                return []

            usd = prices.get("usd")
            usd_foil = prices.get("usd_foil")
            usd_etched = prices.get("usd_etched")

            # Choose appropriate price based on card type
            price = None
            if card.foil and usd_foil:
                price = float(usd_foil)
            elif card.foil and usd_etched:
                price = float(usd_etched)
            elif usd:
                price = float(usd)

            if not price:
                return []

            # Get price links
            price_links = data.get("purchase_uris", {})

            # Get additional metadata
            all_conditions = {
                "usd": usd,
                "usd_foil": usd_foil,
                "usd_etched": usd_etched,
                "eur": prices.get("eur"),
                "eur_foil": prices.get("eur_foil"),
                "price_links": price_links,
                "rarity": data.get("rarity"),
                "set_name": data.get("set_name"),
                "collector_number": data.get("collector_number"),
            }

            results = [
                PriceData(
                    vendor=self.name,
                    price=price,
                    price_type="offer_market_foil" if card.foil else "offer_market",
                    condition=Condition.NM,
                    notes=f"Scryfall market price for {data.get('set_name')}",
                )
            ]

            return results

        except (TypeError, KeyError, IndexError) as e:
            self.logger.error(
                f"Error parsing Scryfall data for {card.name}: {e}. Data: {data}"
            )
            return []

    def get_buylist(self) -> List[PriceData]:
        """Scryfall doesn't have a traditional buylist, return empty list."""
        return []
