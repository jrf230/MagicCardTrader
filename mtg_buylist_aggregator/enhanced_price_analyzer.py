"""Enhanced price analyzer combining multiple data sources."""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass

from .models import Card, CardPrices, PriceData
from .scrapers.ebay import EbayScraper
from .scrapers.tcgplayer import TCGPlayerScraper

logger = logging.getLogger(__name__)


@dataclass
class MarketInsight:
    """Market insight data for a card."""
    card: Card
    current_market_price: float
    buylist_avg: float
    ebay_avg: float
    price_spread: float
    market_volatility: float
    trend_direction: str
    trend_percentage: float
    volume_score: int
    risk_score: float
    recommendation: str
    confidence: float
    scryfall_links: dict = None  # Add Scryfall price links


class EnhancedPriceAnalyzer:
    """Analyzes prices across multiple data sources for comprehensive insights."""
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        # Only initialize scrapers if using mock data to avoid timeouts
        if use_mock:
            self.ebay_scraper = EbayScraper()
            self.tcg_scraper = TCGPlayerScraper()
        else:
            self.ebay_scraper = None
            self.tcg_scraper = None
    
    def analyze_card_market(self, card: Card, card_prices: CardPrices) -> Optional[MarketInsight]:
        """Analyze market data for a single card."""
        try:
            # Extract price data from different sources
            buylist_prices = self._extract_buylist_prices(card_prices)
            market_prices = self._extract_market_prices(card_prices)
            
            # Add all available prices to market prices
            for vendor, price_data in card_prices.prices.items():
                if price_data.price and price_data.price > 0:
                    market_prices.append(price_data.price)
            
            # Get additional data from scrapers only if available
            ebay_data = None
            tcg_insights = None
            
            if self.ebay_scraper:
                try:
                    ebay_data = self.ebay_scraper.get_market_trends(card)
                except:
                    pass
            
            if self.tcg_scraper:
                try:
                    tcg_insights = self.tcg_scraper.get_market_insights(card)
                except:
                    pass
            
            # Scryfall price links (if present)
            scryfall_links = None
            if "Scryfall" in card_prices.prices:
                scryfall_links = card_prices.prices["Scryfall"].all_conditions.get("price_links")
            
            # Determine trend based on available data
            trend_direction, trend_percentage = self._determine_trend(ebay_data, tcg_insights)
            
            # Calculate market metrics
            current_market_price = self._calculate_market_price(market_prices, tcg_insights)
            buylist_avg = statistics.mean(buylist_prices) if buylist_prices else 0
            ebay_avg = ebay_data.get('recent_avg', 0) if ebay_data else 0
            
            # Calculate spread and volatility
            price_spread = current_market_price - buylist_avg if buylist_avg > 0 else 0
            market_volatility = self._calculate_volatility(market_prices, tcg_insights)
            
            # Calculate scores
            volume_score = self._calculate_volume_score(ebay_data, tcg_insights)
            risk_score = self._calculate_risk_score(market_volatility, price_spread, trend_percentage)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                price_spread, trend_percentage, risk_score, volume_score
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(card_prices, ebay_data, tcg_insights)
            
            return MarketInsight(
                card=card,
                current_market_price=current_market_price,
                buylist_avg=buylist_avg,
                ebay_avg=ebay_avg,
                price_spread=price_spread,
                market_volatility=market_volatility,
                trend_direction=trend_direction,
                trend_percentage=trend_percentage,
                volume_score=volume_score,
                risk_score=risk_score,
                recommendation=recommendation,
                confidence=confidence,
                scryfall_links=scryfall_links
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market for {card.name}: {e}")
            return None
    
    def _extract_buylist_prices(self, card_prices: CardPrices) -> List[float]:
        """Extract buylist prices from card prices."""
        buylist_prices = []
        buylist_vendors = ["Star City Games", "Card Kingdom", "BeatTheBuylist", 
                          "Channel Fireball", "CoolStuffInc"]
        
        for vendor in buylist_vendors:
            if vendor in card_prices.prices:
                price_data = card_prices.prices[vendor]
                if price_data.price and price_data.price > 0:
                    buylist_prices.append(price_data.price)
        
        return buylist_prices
    
    def _extract_market_prices(self, card_prices: CardPrices) -> List[float]:
        """Extract market prices from card prices."""
        market_prices = []
        market_vendors = ["TCG Player", "eBay Recent Sales"]
        
        for vendor in market_vendors:
            if vendor in card_prices.prices:
                price_data = card_prices.prices[vendor]
                if price_data.price and price_data.price > 0:
                    market_prices.append(price_data.price)
        
        return market_prices
    
    def _calculate_market_price(self, market_prices: List[float], tcg_insights: Optional[Dict]) -> float:
        """Calculate current market price."""
        if market_prices:
            return statistics.mean(market_prices)
        elif tcg_insights and tcg_insights.get('current_market_price'):
            return tcg_insights['current_market_price']
        return 0
    
    def _calculate_volatility(self, market_prices: List[float], tcg_insights: Optional[Dict]) -> float:
        """Calculate market volatility."""
        if market_prices and len(market_prices) > 1:
            return statistics.stdev(market_prices)
        elif tcg_insights and tcg_insights.get('price_volatility'):
            return tcg_insights['price_volatility']
        return 0
    
    def _determine_trend(self, ebay_data: Optional[Dict], tcg_insights: Optional[Dict]) -> Tuple[str, float]:
        """Determine price trend direction and percentage."""
        trend_percentage = 0
        trend_direction = "stable"
        
        # Use eBay trend data if available
        if ebay_data and ebay_data.get('trend_percent'):
            trend_percentage = ebay_data['trend_percent']
            trend_direction = ebay_data.get('trend_direction', 'stable')
        # Fall back to TCG Player trend
        elif tcg_insights and tcg_insights.get('trend_direction'):
            trend_direction = tcg_insights['trend_direction']
            # Estimate percentage based on direction
            trend_percentage = 5.0 if trend_direction == 'up' else -5.0
        
        return trend_direction, trend_percentage
    
    def _calculate_volume_score(self, ebay_data: Optional[Dict], tcg_insights: Optional[Dict]) -> int:
        """Calculate volume score (1-10) based on trading activity."""
        volume_score = 5  # Default medium volume
        
        if ebay_data and ebay_data.get('volume'):
            volume = ebay_data['volume']
            if volume >= 20:
                volume_score = 10
            elif volume >= 15:
                volume_score = 8
            elif volume >= 10:
                volume_score = 6
            elif volume >= 5:
                volume_score = 4
            else:
                volume_score = 2
        
        return volume_score
    
    def _calculate_risk_score(self, volatility: float, spread: float, trend_percentage: float) -> float:
        """Calculate risk score (0-1, higher = more risky)."""
        risk_factors = []
        
        # Volatility risk (0-0.4)
        if volatility > 0:
            vol_risk = min(volatility / 10.0, 0.4)  # Normalize volatility
            risk_factors.append(vol_risk)
        
        # Spread risk (0-0.3)
        if spread > 0:
            spread_risk = min(spread / 50.0, 0.3)  # Normalize spread
            risk_factors.append(spread_risk)
        
        # Trend risk (0-0.3)
        trend_risk = abs(trend_percentage) / 100.0 * 0.3
        risk_factors.append(trend_risk)
        
        return min(sum(risk_factors), 1.0)
    
    def _generate_recommendation(self, spread: float, trend: float, risk: float, volume: int) -> str:
        """Generate trading recommendation."""
        if risk > 0.7:
            return "HIGH_RISK"
        elif spread > 20 and trend > 10 and volume >= 6:
            return "STRONG_BUY"
        elif spread > 15 and trend > 5 and volume >= 5:
            return "BUY"
        elif spread < -10 and trend < -5 and volume >= 5:
            return "SELL"
        elif spread < -15 and trend < -10 and volume >= 6:
            return "STRONG_SELL"
        elif abs(trend) < 5 and abs(spread) < 10:
            return "HOLD"
        else:
            return "MONITOR"
    
    def _calculate_confidence(self, card_prices: CardPrices, ebay_data: Optional[Dict], 
                            tcg_insights: Optional[Dict]) -> float:
        """Calculate confidence score (0-1) in the analysis."""
        confidence_factors = []
        
        # Data source coverage
        sources = len(card_prices.prices)
        if sources >= 5:
            confidence_factors.append(0.4)
        elif sources >= 3:
            confidence_factors.append(0.3)
        elif sources >= 1:
            confidence_factors.append(0.2)
        
        # Additional data sources
        if ebay_data:
            confidence_factors.append(0.3)
        if tcg_insights:
            confidence_factors.append(0.3)
        
        return min(sum(confidence_factors), 1.0)
    
    def analyze_collection_market(self, card_prices_list: List[CardPrices]) -> Dict:
        """Analyze market data for an entire collection."""
        insights = []
        total_value = 0
        total_buylist_value = 0
        
        for card_prices in card_prices_list:
            insight = self.analyze_card_market(card_prices.card, card_prices)
            if insight:
                insights.append(insight)
                total_value += insight.current_market_price
                total_buylist_value += insight.buylist_avg
        
        # Calculate collection-level metrics
        if insights:
            avg_spread = statistics.mean([i.price_spread for i in insights])
            avg_volatility = statistics.mean([i.market_volatility for i in insights])
            avg_risk = statistics.mean([i.risk_score for i in insights])
            
            # Categorize recommendations
            recommendations = {}
            for insight in insights:
                rec = insight.recommendation
                if rec not in recommendations:
                    recommendations[rec] = []
                recommendations[rec].append(insight.card.name)
            
            # Convert insights to serializable format
            serializable_insights = []
            for insight in insights:
                serializable_insights.append({
                    'card': {
                        'name': insight.card.name,
                        'set_name': insight.card.set_name,
                        'quantity': insight.card.quantity,
                        'foil': insight.card.is_foil(),
                        'rarity': insight.card.rarity.value if insight.card.rarity else None
                    },
                    'current_market_price': insight.current_market_price,
                    'buylist_avg': insight.buylist_avg,
                    'ebay_avg': insight.ebay_avg,
                    'price_spread': insight.price_spread,
                    'market_volatility': insight.market_volatility,
                    'trend_direction': insight.trend_direction,
                    'trend_percentage': insight.trend_percentage,
                    'volume_score': insight.volume_score,
                    'risk_score': insight.risk_score,
                    'recommendation': insight.recommendation,
                    'confidence': insight.confidence,
                    'scryfall_links': insight.scryfall_links
                })
            
            return {
                'insights': serializable_insights,
                'total_market_value': total_value,
                'total_buylist_value': total_buylist_value,
                'avg_price_spread': avg_spread,
                'avg_volatility': avg_volatility,
                'avg_risk_score': avg_risk,
                'recommendations': recommendations,
                'analysis_date': datetime.now().isoformat()
            }
        
        return {'insights': [], 'analysis_date': datetime.now().isoformat()} 