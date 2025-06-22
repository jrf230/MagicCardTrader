"""Price cache management for daily price updates."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .models import Card, CardPrices, PriceData
from .scrapers.scraper_manager import ScraperManager

logger = logging.getLogger(__name__)


@dataclass
class CachedPriceData:
    """Cached price data for a card."""

    card_name: str
    set_name: str
    foil: bool
    timestamp: str
    best_bid: float
    best_offer: float
    best_vendor: str
    vendor_prices: Dict[str, Dict[str, Any]]
    last_updated: str
    best_bid_vendor: Optional[str]
    best_offer_vendor: Optional[str]
    vendor_prices_json: str


class PriceCache:
    """Manages cached price data with daily updates."""

    def __init__(self, cache_file: str = "price_cache.json"):
        """Initialize price cache.

        Args:
            cache_file: Path to JSON file storing cached prices
        """
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, CachedPriceData]:
        """Load cached prices from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    # Convert back to CachedPriceData objects
                    cache = {}
                    for key, item in data.items():
                        cache[key] = CachedPriceData(**item)
                    return cache
            except Exception as e:
                logger.error(f"Failed to load price cache: {e}")
                return {}
        return {}

    def _save_cache(self) -> None:
        """Save cached prices to file."""
        try:
            # Convert CachedPriceData objects to dictionaries
            data = {key: asdict(value) for key, value in self.cache.items()}
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved price cache to {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to save price cache: {e}")

    def _get_cache_key(self, card: Card) -> str:
        """Generate cache key for a card."""
        return f"{card.name} ({card.set_name}) [{'Foil' if card.is_foil() else 'Non-foil'}]"

    def get_cached_prices(self, cards: List[Card]) -> List[Dict]:
        """Get cached prices for cards in collection.

        Args:
            cards: List of cards in collection

        Returns:
            List of cached price data for each card
        """
        result = []
        current_time = datetime.now()

        for card in cards:
            cache_key = self._get_cache_key(card)
            cached_data = self.cache.get(cache_key)

            if cached_data:
                # Check if cache is still valid (less than 24 hours old)
                cache_time = datetime.fromisoformat(cached_data.timestamp)
                if current_time - cache_time < timedelta(hours=24):
                    # Cache is valid, use it
                    card_prices = CardPrices.parse_raw(cached_data.vendor_prices_json)

                    # Convert vendor_prices to serializable format
                    serializable_vendor_prices = {}
                    for vendor, price_data_list in card_prices.prices.items():
                        serializable_vendor_prices[vendor] = [
                            {
                                "price": pd.price,
                                "condition": pd.condition,
                                "price_type": pd.price_type,
                                "quantity_limit": pd.quantity_limit,
                                "last_price_update": (
                                    pd.last_price_update.isoformat()
                                    if pd.last_price_update
                                    else None
                                ),
                                "notes": pd.notes,
                            }
                            for pd in price_data_list
                        ]

                    result.append(
                        {
                            "card": card_prices.card.dict(),
                            "best_bid": (
                                card_prices.best_bid.dict()
                                if card_prices.best_bid
                                else None
                            ),
                            "best_offer": (
                                card_prices.best_offer.dict()
                                if card_prices.best_offer
                                else None
                            ),
                            "vendor_prices": serializable_vendor_prices,
                            "last_updated": cached_data.last_updated,
                        }
                    )
                    continue

            # No valid cache, return empty data
            result.append(
                {
                    "card": {
                        "name": card.name,
                        "set_name": card.set_name,
                        "foil": card.is_foil(),
                    },
                    "best_bid": None,
                    "best_offer": None,
                    "vendor_prices": [],
                    "cache_age": None,
                    "last_updated": None,
                }
            )

        return result

    def update_cache(self, cards: List[Card], force_update: bool = False) -> None:
        """Update price cache for all cards.

        Args:
            cards: List of cards to update
            force_update: Force update even if cache is recent
        """
        if not cards:
            return

        current_time = datetime.now()
        scraper_manager = ScraperManager(use_mock=False)

        # Get current prices
        card_prices_list = scraper_manager.get_collection_prices(cards)

        for card_prices in card_prices_list:
            card = card_prices.card
            cache_key = self._get_cache_key(card)

            # Check if we need to update (cache is old or forced)
            cached_data = self.cache.get(cache_key)
            if cached_data and not force_update:
                cache_time = datetime.fromisoformat(cached_data.timestamp)
                if current_time - cache_time < timedelta(hours=24):
                    # Cache is still fresh, skip
                    continue

            # Prepare vendor prices
            vendor_prices = {}
            best_bid = 0
            best_bid_vendor = None
            best_offer = float("inf")
            best_offer_vendor = None

            for vendor, price_data_list in card_prices.prices.items():
                # price_data_list is now a list of PriceData objects
                for price_data in price_data_list:
                    # Determine if this is a bid (buylist) or offer (sell) price
                    is_bid = True  # Default assumption

                    # Check all_conditions for price type indicators
                    all_conditions = getattr(price_data, "all_conditions", {})
                    price_type = all_conditions.get("price_type", "")

                    # Determine price type based on vendor and price type
                    if "offer" in price_type.lower() or "sell" in price_type.lower():
                        is_bid = False
                    elif "bid" in price_type.lower() or "buylist" in price_type.lower():
                        is_bid = True
                    else:
                        # Fallback: use vendor name to determine type
                        vendor_lower = vendor.lower()
                        if any(
                            keyword in vendor_lower
                            for keyword in ["tcg", "ebay", "marketplace"]
                        ):
                            is_bid = False  # These typically have offer prices
                        else:
                            is_bid = True  # Most others are buylist/bid prices

                    vendor_prices[vendor] = {
                        "price": price_data.price,
                        "condition": price_data.condition,
                        "is_bid": is_bid,
                    }

                    # Track best bid and offer
                    if is_bid:
                        if price_data.price > best_bid:
                            best_bid = price_data.price
                            best_bid_vendor = vendor
                    else:
                        if price_data.price < best_offer:
                            best_offer = price_data.price
                            best_offer_vendor = vendor

            # Create cached data with separate best bid and offer vendors
            cached_data = CachedPriceData(
                card_name=card.name,
                set_name=card.set_name,
                foil=card.is_foil(),
                timestamp=current_time.isoformat(),
                best_bid=best_bid,
                best_offer=best_offer if best_offer != float("inf") else 0,
                best_vendor=best_bid_vendor or best_offer_vendor or "Unknown",
                vendor_prices=vendor_prices,
                last_updated=current_time.isoformat(),
                best_bid_vendor=best_bid_vendor,
                best_offer_vendor=best_offer_vendor,
                vendor_prices_json=card_prices.json(),
            )

            self.cache[cache_key] = cached_data

        self._save_cache()
        logger.info(f"Updated price cache for {len(cards)} cards")

    def get_cache_status(self) -> Dict:
        """Get status of price cache.

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache:
            return {
                "total_cards": 0,
                "fresh_cache": 0,
                "stale_cache": 0,
                "last_update": None,
                "next_update": None,
            }

        current_time = datetime.now()
        fresh_count = 0
        stale_count = 0
        last_update = None

        for cached_data in self.cache.values():
            cache_time = datetime.fromisoformat(cached_data.timestamp)
            if current_time - cache_time < timedelta(hours=24):
                fresh_count += 1
            else:
                stale_count += 1

            if last_update is None or cache_time > last_update:
                last_update = cache_time

        next_update = last_update + timedelta(hours=24) if last_update else None

        return {
            "total_cards": len(self.cache),
            "fresh_cache": fresh_count,
            "stale_cache": stale_count,
            "last_update": last_update.isoformat() if last_update else None,
            "next_update": next_update.isoformat() if next_update else None,
        }

    def cleanup_old_cache(self, days_to_keep: int = 7) -> None:
        """Remove cache entries older than specified days.

        Args:
            days_to_keep: Number of days of cache to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0

        for cache_key in list(self.cache.keys()):
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data.timestamp)

            if cache_time < cutoff_date:
                del self.cache[cache_key]
                removed_count += 1

        if removed_count > 0:
            self._save_cache()
            logger.info(f"Cleaned up {removed_count} old cache entries")
