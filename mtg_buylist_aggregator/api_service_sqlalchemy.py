"""
Enhanced API service using SQLAlchemy database layer.
Provides optimized data access with intelligent caching and background processing.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import joinedload
from sqlalchemy import func, desc, and_

from mtg_buylist_aggregator.database_sqlalchemy import (
    get_database_manager,
    Card,
    Vendor,
    Price,
    Cache,
    Analytics,
)
from mtg_buylist_aggregator.scrapers.scraper_manager import ScraperManager
from mtg_buylist_aggregator.enhanced_price_analyzer import EnhancedPriceAnalyzer
from mtg_buylist_aggregator.hot_card_detector import HotCardDetector
from mtg_buylist_aggregator.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class EnhancedAPIService:
    """Enhanced API service with SQLAlchemy backend and intelligent caching."""

    def __init__(self):
        """Initialize the enhanced API service."""
        self.db_manager = get_database_manager()
        self.scraper_manager = ScraperManager()
        self.price_analyzer = EnhancedPriceAnalyzer()
        self.hot_card_detector = HotCardDetector()
        self.recommendation_engine = RecommendationEngine()

        # Cache configuration
        self.cache_duration = timedelta(hours=24)
        self.price_cache_duration = timedelta(hours=6)
        self.analytics_cache_duration = timedelta(hours=12)

    def _get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache."""
        try:
            with self.db_manager.get_session() as session:
                cache_entry = (
                    session.query(Cache)
                    .filter(
                        and_(Cache.key == key, Cache.expires_at > datetime.utcnow())
                    )
                    .first()
                )

                if cache_entry:
                    return json.loads(cache_entry.data)
                return None
        except Exception as e:
            logger.error(f"Cache retrieval error for key '{key}': {e}")
            return None

    def _set_cache(
        self, key: str, data: Dict[str, Any], duration: Optional[timedelta] = None
    ) -> bool:
        """Set data in cache."""
        try:
            if duration is None:
                duration = self.cache_duration

            with self.db_manager.get_session() as session:
                # Remove existing cache entry
                session.query(Cache).filter(Cache.key == key).delete()

                # Create new cache entry
                cache_entry = Cache(
                    key=key,
                    data=json.dumps(data),
                    expires_at=datetime.utcnow() + duration,
                )
                session.add(cache_entry)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Cache storage error for key '{key}': {e}")
            return False

    def get_collection(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get collection data with caching."""
        cache_key = "collection"

        if not force_refresh:
            cached_data = self._get_cache(cache_key)
            if cached_data:
                return cached_data

        try:
            with self.db_manager.get_session() as session:
                cards = (
                    session.query(Card)
                    .options(joinedload(Card.prices).joinedload(Price.vendor))
                    .all()
                )

                collection_data = []
                for card in cards:
                    # Get latest prices for this card
                    latest_prices = (
                        session.query(Price)
                        .filter(Price.card_id == card.id)
                        .order_by(desc(Price.timestamp))
                        .limit(10)
                        .all()
                    )

                    # Calculate best buy price
                    buy_prices = [p.price for p in latest_prices if p.is_buy_price]
                    best_buy_price = max(buy_prices) if buy_prices else None
                    best_buy_vendor = None
                    if best_buy_price:
                        best_price_entry = next(
                            (
                                p
                                for p in latest_prices
                                if p.price == best_buy_price and p.is_buy_price
                            ),
                            None,
                        )
                        if best_price_entry:
                            best_buy_vendor = best_price_entry.vendor.name

                    card_data = {
                        "id": card.id,
                        "name": card.name,
                        "set_name": card.set_name,
                        "foil": card.foil,
                        "condition": card.condition,
                        "quantity": card.quantity,
                        "best_buy_price": best_buy_price,
                        "best_buy_vendor": best_buy_vendor,
                        "total_value": (best_buy_price or 0) * card.quantity,
                        "last_updated": (
                            card.updated_at.isoformat() if card.updated_at else None
                        ),
                    }
                    collection_data.append(card_data)

                # Cache the result
                self._set_cache(cache_key, collection_data)
                return collection_data

        except Exception as e:
            logger.error(f"Error getting collection: {e}")
            return []

    def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive dashboard data with intelligent caching."""
        cache_key = "dashboard"

        if not force_refresh:
            cached_data = self._get_cache(cache_key)
            if cached_data:
                return cached_data

        try:
            # Get collection data
            collection = self.get_collection(force_refresh=force_refresh)

            # Calculate summary statistics
            total_cards = len(collection)
            total_value = sum(card["total_value"] for card in collection)
            cards_with_prices = len(
                [card for card in collection if card["best_buy_price"] is not None]
            )

            # Get recent price updates
            with self.db_manager.get_session() as session:
                recent_prices = (
                    session.query(Price)
                    .order_by(desc(Price.timestamp))
                    .limit(20)
                    .options(joinedload(Price.card), joinedload(Price.vendor))
                    .all()
                )

                recent_updates = []
                for price in recent_prices:
                    recent_updates.append(
                        {
                            "card_name": price.card.name,
                            "vendor": price.vendor.name,
                            "price": price.price,
                            "condition": price.condition,
                            "is_foil": price.is_foil,
                            "is_buy_price": price.is_buy_price,
                            "timestamp": price.timestamp.isoformat(),
                        }
                    )

            # Get vendor statistics
            vendor_stats = self._get_vendor_statistics()

            dashboard_data = {
                "collection": collection,
                "summary": {
                    "total_cards": total_cards,
                    "total_value": total_value,
                    "cards_with_prices": cards_with_prices,
                    "price_coverage": (
                        (cards_with_prices / total_cards * 100)
                        if total_cards > 0
                        else 0
                    ),
                },
                "recent_updates": recent_updates,
                "vendor_stats": vendor_stats,
                "last_updated": datetime.utcnow().isoformat(),
            }

            # Cache the result
            self._set_cache(cache_key, dashboard_data)
            return dashboard_data

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                "collection": [],
                "summary": {
                    "total_cards": 0,
                    "total_value": 0,
                    "cards_with_prices": 0,
                    "price_coverage": 0,
                },
                "recent_updates": [],
                "vendor_stats": {},
                "last_updated": datetime.utcnow().isoformat(),
            }

    def _get_vendor_statistics(self) -> Dict[str, Any]:
        """Get vendor performance statistics."""
        try:
            with self.db_manager.get_session() as session:
                # Get vendor success rates
                vendor_stats = (
                    session.query(
                        Vendor.name,
                        Vendor.success_rate,
                        Vendor.last_scrape,
                        func.count(Price.id).label("price_count"),
                    )
                    .outerjoin(Price)
                    .group_by(Vendor.id)
                    .all()
                )

                stats = {}
                for vendor in vendor_stats:
                    stats[vendor.name] = {
                        "success_rate": vendor.success_rate,
                        "last_scrape": (
                            vendor.last_scrape.isoformat()
                            if vendor.last_scrape
                            else None
                        ),
                        "price_count": vendor.price_count,
                        "is_active": (
                            vendor.success_rate > 0.5 if vendor.success_rate else False
                        ),
                    }

                return stats
        except Exception as e:
            logger.error(f"Error getting vendor statistics: {e}")
            return {}

    def get_market_analysis(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get market analysis with caching."""
        cache_key = "market_analysis"

        if not force_refresh:
            cached_data = self._get_cache(cache_key)
            if cached_data:
                return cached_data

        try:
            collection = self.get_collection(force_refresh=force_refresh)

            # Analyze price trends
            analysis_data = self.price_analyzer.analyze_collection(collection)

            # Cache the result
            self._set_cache(cache_key, analysis_data, self.analytics_cache_duration)
            return analysis_data

        except Exception as e:
            logger.error(f"Error getting market analysis: {e}")
            return {"error": str(e)}

    def get_hot_cards(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get hot cards with caching."""
        cache_key = "hot_cards"

        if not force_refresh:
            cached_data = self._get_cache(cache_key)
            if cached_data:
                return cached_data

        try:
            collection = self.get_collection(force_refresh=force_refresh)
            hot_cards = self.hot_card_detector.detect_hot_cards(collection)

            # Cache the result
            self._set_cache(cache_key, hot_cards, self.analytics_cache_duration)
            return hot_cards

        except Exception as e:
            logger.error(f"Error getting hot cards: {e}")
            return []

    def get_recommendations(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get recommendations with caching."""
        cache_key = "recommendations"

        if not force_refresh:
            cached_data = self._get_cache(cache_key)
            if cached_data:
                return cached_data

        try:
            collection = self.get_collection(force_refresh=force_refresh)
            recommendations = self.recommendation_engine.get_recommendations(collection)

            # Cache the result
            self._set_cache(cache_key, recommendations, self.analytics_cache_duration)
            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    def add_card(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a card to the collection."""
        try:
            with self.db_manager.get_session() as session:
                # Check if card already exists
                existing_card = (
                    session.query(Card)
                    .filter(
                        and_(
                            Card.name == card_data["name"],
                            Card.set_name == card_data["set_name"],
                            Card.foil == card_data.get("foil", False),
                        )
                    )
                    .first()
                )

                if existing_card:
                    # Update quantity
                    existing_card.quantity += card_data.get("quantity", 1)
                    existing_card.updated_at = datetime.utcnow()
                    card = existing_card
                else:
                    # Create new card
                    card = Card(
                        name=card_data["name"],
                        set_name=card_data["set_name"],
                        foil=card_data.get("foil", False),
                        condition=card_data.get("condition", "NM"),
                        quantity=card_data.get("quantity", 1),
                    )
                    session.add(card)

                session.commit()

                # Clear relevant caches
                self._clear_collection_cache()

                return {
                    "success": True,
                    "card_id": card.id,
                    "message": "Card added successfully",
                }

        except Exception as e:
            logger.error(f"Error adding card: {e}")
            return {"success": False, "error": str(e)}

    def remove_card(self, card_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Remove a card from the collection."""
        try:
            with self.db_manager.get_session() as session:
                card = session.query(Card).filter(Card.id == card_id).first()

                if not card:
                    return {"success": False, "error": "Card not found"}

                if card.quantity <= quantity:
                    # Remove the entire card
                    session.delete(card)
                else:
                    # Reduce quantity
                    card.quantity -= quantity
                    card.updated_at = datetime.utcnow()

                session.commit()

                # Clear relevant caches
                self._clear_collection_cache()

                return {"success": True, "message": "Card removed successfully"}

        except Exception as e:
            logger.error(f"Error removing card: {e}")
            return {"success": False, "error": str(e)}

    def update_prices(self, card_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update prices for cards."""
        try:
            if card_names:
                # Update specific cards
                results = self.scraper_manager.scrape_cards(card_names)
            else:
                # Update all cards in collection
                collection = self.get_collection()
                card_names = [card["name"] for card in collection]
                results = self.scraper_manager.scrape_cards(card_names)

            # Store prices in database
            self._store_prices(results)

            # Clear price-related caches
            self._clear_price_cache()

            return {
                "success": True,
                "cards_updated": len(results),
                "message": "Prices updated successfully",
            }

        except Exception as e:
            logger.error(f"Error updating prices: {e}")
            return {"success": False, "error": str(e)}

    def _store_prices(self, price_results: List[Dict[str, Any]]):
        """Store price results in the database."""
        try:
            with self.db_manager.get_session() as session:
                for result in price_results:
                    card_name = result["card_name"]
                    vendor_name = result["vendor"]
                    price_data = result["price_data"]

                    # Find or create card
                    card = session.query(Card).filter(Card.name == card_name).first()
                    if not card:
                        card = Card(name=card_name, set_name="Unknown")
                        session.add(card)
                        session.flush()

                    # Find or create vendor
                    vendor = (
                        session.query(Vendor).filter(Vendor.name == vendor_name).first()
                    )
                    if not vendor:
                        vendor = Vendor(name=vendor_name)
                        session.add(vendor)
                        session.flush()

                    # Store price
                    price = Price(
                        card_id=card.id,
                        vendor_id=vendor.id,
                        price=price_data.price,
                        condition=price_data.condition.value,
                        is_foil=price_data.foil_treatment != "nonfoil",
                        is_buy_price=True,
                        timestamp=datetime.utcnow(),
                    )
                    session.add(price)

                session.commit()

        except Exception as e:
            logger.error(f"Error storing prices: {e}")
            raise

    def _clear_collection_cache(self):
        """Clear collection-related caches."""
        cache_keys = ["collection", "dashboard"]
        for key in cache_keys:
            try:
                with self.db_manager.get_session() as session:
                    session.query(Cache).filter(Cache.key == key).delete()
                    session.commit()
            except Exception as e:
                logger.error(f"Error clearing cache key '{key}': {e}")

    def _clear_price_cache(self):
        """Clear price-related caches."""
        cache_keys = ["market_analysis", "hot_cards", "recommendations"]
        for key in cache_keys:
            try:
                with self.db_manager.get_session() as session:
                    session.query(Cache).filter(Cache.key == key).delete()
                    session.commit()
            except Exception as e:
                logger.error(f"Error clearing cache key '{key}': {e}")

    def clear_cache(self) -> Dict[str, Any]:
        """Clear all caches."""
        try:
            with self.db_manager.get_session() as session:
                session.query(Cache).delete()
                session.commit()

            return {"success": True, "message": "All caches cleared successfully"}
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return {"success": False, "error": str(e)}

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            db_health = self.db_manager.health_check()

            # Check cache status
            with self.db_manager.get_session() as session:
                cache_count = session.query(Cache).count()
                expired_cache_count = (
                    session.query(Cache)
                    .filter(Cache.expires_at <= datetime.utcnow())
                    .count()
                )

            return {
                "status": (
                    "healthy" if db_health["status"] == "healthy" else "unhealthy"
                ),
                "database": db_health,
                "cache": {
                    "total_entries": cache_count,
                    "expired_entries": expired_cache_count,
                    "valid_entries": cache_count - expired_cache_count,
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat(),
            }


# Global API service instance
_api_service: Optional[EnhancedAPIService] = None


def get_enhanced_api_service() -> EnhancedAPIService:
    """Get the global enhanced API service instance."""
    global _api_service
    if _api_service is None:
        _api_service = EnhancedAPIService()
    return _api_service
