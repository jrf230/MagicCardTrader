"""Optimized API service for MTG Trader Pro."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading

from .database import get_database
from .models import Card, CardPrices
from .scrapers.scraper_manager import ScraperManager
from .enhanced_price_analyzer import EnhancedPriceAnalyzer
from .hot_card_detector import HotCardDetector
from .recommendation_engine import RecommendationEngine
from .collection_analytics import CollectionAnalytics
from .price_history import PriceHistory

logger = logging.getLogger(__name__)


class APIService:
    """Centralized API service with intelligent caching and database integration."""
    
    def __init__(self):
        """Initialize the API service."""
        self.db = get_database()
        self._lock = threading.RLock()
    
    def get_collection_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get collection data with prices. Respects 24-hour cache rule."""
        with self._lock:
            # Get cards from database
            cards = self.db.get_cards()
            
            if not cards:
                return {
                    'cards': [],
                    'total_cards': 0,
                    'cache_status': 'no_data'
                }
            
            # Try to get cached prices first
            card_prices_list = self.db.get_price_cache(cards, force_refresh=force_refresh)
            
            # Check if we need to fetch fresh prices
            needs_refresh = force_refresh or self._needs_price_refresh(card_prices_list)
            
            if needs_refresh:
                logger.info("Fetching fresh prices from vendors")
                scraper_manager = ScraperManager(use_mock=False)
                card_prices_list = scraper_manager.get_collection_prices(cards)
                
                # Update database cache
                self.db.update_price_cache(card_prices_list)
                
                # Clear dashboard cache since prices changed
                self.db.clear_dashboard_cache()
            
            # Convert to frontend format
            cards_with_prices = []
            for card_prices in card_prices_list:
                card_data = card_prices.card.__dict__.copy()
                card_data['prices'] = {}
                
                for vendor, price_data_list in card_prices.prices.items():
                    if price_data_list:
                        card_data['prices'][vendor] = [
                            {
                                'price': price_data.price,
                                'price_type': price_data.price_type,
                                'vendor': price_data.vendor,
                                'condition': price_data.condition,
                                'quantity_limit': price_data.quantity_limit,
                                'last_price_update': price_data.last_price_update.isoformat() if price_data.last_price_update else None,
                                'notes': price_data.notes
                            }
                            for price_data in price_data_list
                        ]
                
                # Add best prices
                if card_prices.best_bid:
                    card_data['best_bid'] = {
                        'price': card_prices.best_bid.price,
                        'vendor': card_prices.best_bid.vendor,
                        'condition': card_prices.best_bid.condition,
                        'quantity_limit': card_prices.best_bid.quantity_limit,
                        'last_price_update': card_prices.best_bid.last_price_update.isoformat() if card_prices.best_bid.last_price_update else None,
                        'notes': card_prices.best_bid.notes
                    }
                else:
                    card_data['best_bid'] = None
                    
                if card_prices.best_offer:
                    card_data['best_offer'] = {
                        'price': card_prices.best_offer.price,
                        'vendor': card_prices.best_offer.vendor,
                        'condition': card_prices.best_offer.condition,
                        'quantity_limit': card_prices.best_offer.quantity_limit,
                        'last_price_update': card_prices.best_offer.last_price_update.isoformat() if card_prices.best_offer.last_price_update else None,
                        'notes': card_prices.best_offer.notes
                    }
                else:
                    card_data['best_offer'] = None
                
                cards_with_prices.append(card_data)
            
            return {
                'cards': cards_with_prices,
                'total_cards': len(cards),
                'cache_status': 'fresh' if not needs_refresh else 'updated'
            }
    
    def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get all dashboard data in a single optimized call."""
        with self._lock:
            # Check database cache first
            if not force_refresh:
                cached_data = self.db.get_dashboard_cache()
                if cached_data:
                    logger.info("Returning cached dashboard data")
                    return cached_data
            
            logger.info("Generating fresh dashboard data")
            
            # Get collection data
            collection_data = self.get_collection_data(force_refresh=force_refresh)
            cards = self.db.get_cards()
            
            if not cards:
                return {'error': 'No cards in collection'}
            
            # Get price data (already cached from get_collection_data)
            card_prices_list = self.db.get_price_cache(cards, force_refresh=force_refresh)
            
            # Generate analytics
            dashboard_data = self._generate_dashboard_analytics(card_prices_list, collection_data)
            
            # Cache the result
            self.db.set_dashboard_cache(dashboard_data)
            
            return dashboard_data
    
    def get_market_analysis(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get market analysis data."""
        with self._lock:
            # Check analytics cache
            if not force_refresh:
                cached_data = self.db.get_analytics_cache('market_analysis')
                if cached_data:
                    logger.info("Returning cached market analysis")
                    return cached_data
            
            # Get collection data
            cards = self.db.get_cards()
            if not cards:
                return {'error': 'No cards in collection'}
            
            card_prices_list = self.db.get_price_cache(cards, force_refresh=force_refresh)
            
            # Generate analysis
            analysis_data = self._generate_market_analysis(card_prices_list)
            
            # Cache the result
            self.db.set_analytics_cache('market_analysis', analysis_data, ttl_hours=6)
            
            return analysis_data
    
    def get_hot_cards(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get hot cards data."""
        with self._lock:
            # Check analytics cache
            if not force_refresh:
                cached_data = self.db.get_analytics_cache('hot_cards')
                if cached_data:
                    logger.info("Returning cached hot cards")
                    return cached_data
            
            # Get collection data
            cards = self.db.get_cards()
            if not cards:
                return {'error': 'No cards in collection'}
            
            card_prices_list = self.db.get_price_cache(cards, force_refresh=force_refresh)
            
            # Generate hot cards
            hot_detector = HotCardDetector(PriceHistory())
            hot_cards = hot_detector.detect_hot_cards(card_prices_list)
            
            hot_cards_data = {
                'hot_cards': hot_cards,
                'total_hot_cards': len(hot_cards)
            }
            
            # Cache the result
            self.db.set_analytics_cache('hot_cards', hot_cards_data, ttl_hours=6)
            
            return hot_cards_data
    
    def get_recommendations(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get recommendations data."""
        with self._lock:
            # Check analytics cache
            if not force_refresh:
                cached_data = self.db.get_analytics_cache('recommendations')
                if cached_data:
                    logger.info("Returning cached recommendations")
                    return cached_data
            
            # Get collection data
            cards = self.db.get_cards()
            if not cards:
                return {'error': 'No cards in collection'}
            
            # Generate recommendations
            recommendation_engine = RecommendationEngine(PriceHistory())
            recommendations = recommendation_engine.generate_recommendations(cards, use_mock=False)
            
            # Cache the result
            self.db.set_analytics_cache('recommendations', recommendations, ttl_hours=12)
            
            return recommendations
    
    def get_vendors_data(self) -> Dict[str, Any]:
        """Get vendor health data."""
        scraper_manager = ScraperManager(use_mock=True)
        vendors = scraper_manager.list_vendors()
        
        vendor_health = []
        for vendor in vendors:
            vendor_health.append({
                'name': vendor,
                'status': 'healthy',
                'response_time': 1.2,
                'success_rate': 95,
                'last_check': datetime.now().isoformat()
            })
        
        return {
            'vendors': vendor_health,
            'total_vendors': len(vendors),
            'healthy_count': len(vendor_health),
            'degraded_count': 0,
            'failed_count': 0
        }
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get comprehensive cache status."""
        return self.db.get_cache_status()
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear all caches."""
        with self._lock:
            self.db.clear_dashboard_cache()
            self.db.clear_dashboard_cache('analytics')
            
            return {
                'success': True,
                'message': 'All caches cleared successfully'
            }
    
    def force_price_update(self) -> Dict[str, Any]:
        """Force update all prices (called when user clicks 'Update Prices')."""
        with self._lock:
            logger.info("Force updating all prices")
            
            # Get collection data with force refresh
            collection_data = self.get_collection_data(force_refresh=True)
            
            # Clear all caches
            self.db.clear_dashboard_cache()
            self.db.clear_dashboard_cache('analytics')
            
            return {
                'success': True,
                'message': f'Updated prices for {collection_data["total_cards"]} cards',
                'timestamp': datetime.now().isoformat()
            }
    
    def add_card(self, card: Card) -> Dict[str, Any]:
        """Add a card to the collection."""
        with self._lock:
            success = self.db.add_card(card)
            
            if success:
                # Clear caches since collection changed
                self.db.clear_dashboard_cache()
                self.db.clear_dashboard_cache('analytics')
                
                return {
                    'success': True,
                    'message': f'Added {card.quantity}x {card.name} ({card.set_name}) to collection'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add card to collection'
                }
    
    def remove_card(self, name: str, set_name: str, foil: bool = False, quantity: Optional[int] = None) -> Dict[str, Any]:
        """Remove a card from the collection."""
        with self._lock:
            success = self.db.remove_card(name, set_name, foil, quantity)
            
            if success:
                # Clear caches since collection changed
                self.db.clear_dashboard_cache()
                self.db.clear_dashboard_cache('analytics')
                
                return {
                    'success': True,
                    'message': f'Removed {name} ({set_name}) from collection'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to remove card from collection'
                }
    
    # Private helper methods
    def _needs_price_refresh(self, card_prices_list: List[CardPrices]) -> bool:
        """Check if prices need to be refreshed based on 24-hour rule."""
        if not card_prices_list:
            return True
        
        # Check if any card has no prices or old prices
        current_time = datetime.now()
        for card_prices in card_prices_list:
            if not card_prices.prices:
                return True
            
            for vendor, price_data_list in card_prices.prices.items():
                for price_data in price_data_list:
                    if price_data.last_price_update:
                        age = current_time - price_data.last_price_update
                        if age > timedelta(hours=24):
                            return True
        
        return False
    
    def _generate_dashboard_analytics(self, card_prices_list: List[CardPrices], collection_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive dashboard analytics."""
        # Enhanced market analysis
        enhanced_analyzer = EnhancedPriceAnalyzer(use_mock=False)
        market_analysis = enhanced_analyzer.analyze_collection_market(card_prices_list)
        
        # Portfolio analytics
        collection_analytics = CollectionAnalytics(PriceHistory())
        diversification = collection_analytics._analyze_diversification(card_prices_list)
        risk = collection_analytics._assess_risk(card_prices_list)
        performance = collection_analytics._analyze_performance(card_prices_list)
        top_performers = collection_analytics._identify_top_performers(card_prices_list, limit=5)
        bottom_performers = collection_analytics._identify_underperformers(card_prices_list, limit=5)
        
        # Hot cards
        hot_detector = HotCardDetector(PriceHistory())
        hot_cards = hot_detector.detect_hot_cards(card_prices_list)
        
        # Vendors
        vendors_data = self.get_vendors_data()
        
        # Benchmarks (mocked for now)
        benchmarks = {
            'sp500': 0.05,  # 5% monthly
            'gold': 0.02,  # 2% monthly
            'market_average': 0.03
        }
        
        # Alerts (mocked for now)
        alerts = [
            {'type': 'reprint_risk', 'card': 'Sol Ring', 'message': 'High reprint risk this year.'},
            {'type': 'price_spike', 'card': 'Tarmogoyf', 'message': 'Unusual price movement detected.'}
        ]
        
        return {
            'collection': collection_data,
            'market': market_analysis,
            'diversification': diversification,
            'risk': risk,
            'performance': performance,
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,
            'hot_cards': hot_cards,
            'total_hot_cards': len(hot_cards),
            'vendors': vendors_data,
            'benchmarks': benchmarks,
            'alerts': alerts,
            'cache_timestamp': datetime.now().isoformat()
        }
    
    def _generate_market_analysis(self, card_prices_list: List[CardPrices]) -> Dict[str, Any]:
        """Generate market analysis data."""
        # Enhanced market analysis
        enhanced_analyzer = EnhancedPriceAnalyzer(use_mock=False)
        analysis = enhanced_analyzer.analyze_collection_market(card_prices_list)
        
        # Portfolio analytics
        collection_analytics = CollectionAnalytics(PriceHistory())
        diversification = collection_analytics._analyze_diversification(card_prices_list)
        risk = collection_analytics._assess_risk(card_prices_list)
        performance = collection_analytics._analyze_performance(card_prices_list)
        top_performers = collection_analytics._identify_top_performers(card_prices_list, limit=5)
        bottom_performers = collection_analytics._identify_underperformers(card_prices_list, limit=5)
        
        # Benchmarks (mocked for now)
        benchmarks = {
            'sp500': 0.05,  # 5% monthly
            'gold': 0.02,  # 2% monthly
            'market_average': 0.03
        }
        
        # Alerts (mocked for now)
        alerts = [
            {'type': 'reprint_risk', 'card': 'Sol Ring', 'message': 'High reprint risk this year.'},
            {'type': 'price_spike', 'card': 'Tarmogoyf', 'message': 'Unusual price movement detected.'}
        ]
        
        return {
            'market': analysis,
            'diversification': diversification,
            'risk': risk,
            'performance': performance,
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,
            'benchmarks': benchmarks,
            'alerts': alerts
        }


# Global API service instance
_api_service = None
_api_lock = threading.Lock()


def get_api_service() -> APIService:
    """Get the global API service instance."""
    global _api_service
    with _api_lock:
        if _api_service is None:
            _api_service = APIService()
        return _api_service 