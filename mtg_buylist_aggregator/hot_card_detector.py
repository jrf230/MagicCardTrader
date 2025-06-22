"""Hot card detection and analysis module."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics

from .models import Card, CardPrices, PriceData
from .price_history import PriceHistory

logger = logging.getLogger(__name__)


class HotCardDetector:
    """Detects and analyzes hot cards with significant price movements."""
    
    def __init__(self, price_history: PriceHistory):
        """Initialize the hot card detector.
        
        Args:
            price_history: PriceHistory instance for accessing historical data
        """
        self.price_history = price_history
        self.config = {
            'spike_threshold_percent': 15.0,  # Minimum % increase to be considered a spike
            'sustained_threshold_days': 3,    # Days of sustained movement
            'volume_threshold': 5,            # Minimum data points for analysis
            'confidence_threshold': 0.7,      # Minimum confidence for hot card status
            'risk_factors': {
                'high_volatility': 0.3,      # Risk weight for high volatility
                'low_volume': 0.2,           # Risk weight for low data volume
                'recent_reprint': 0.4,       # Risk weight for recent reprints
                'format_rotation': 0.3,      # Risk weight for format rotation
                'seasonal_pattern': 0.1      # Risk weight for seasonal patterns
            }
        }
    
    def detect_hot_cards(self, card_prices_list: List[CardPrices], 
                        days: int = 7) -> List[Dict]:
        """Detect hot cards in the collection.
        
        Args:
            card_prices_list: Current price data for cards
            days: Number of days to analyze for price movements
            
        Returns:
            List of hot card analysis results
        """
        logger.info(f"Detecting hot cards for {len(card_prices_list)} cards over {days} days")
        
        hot_cards = []
        
        for card_prices in card_prices_list:
            card = card_prices.card
            analysis = self._analyze_card_movement(card, days)
            
            if analysis and analysis['hot_score'] >= self.config['confidence_threshold']:
                hot_cards.append(analysis)
        
        # Sort by hot score (descending)
        hot_cards.sort(key=lambda x: x['hot_score'], reverse=True)
        
        logger.info(f"Found {len(hot_cards)} hot cards")
        return hot_cards
    
    def _analyze_card_movement(self, card: Card, days: int) -> Optional[Dict]:
        """Analyze price movement for a specific card.
        
        Args:
            card: Card to analyze
            days: Number of days to analyze
            
        Returns:
            Analysis result or None if insufficient data
        """
        # Get price history for the card
        history = self.price_history.get_card_history(card.name, card.set_name, days)
        
        if len(history) < self.config['volume_threshold']:
            return None
        
        # Analyze price trends
        price_analysis = self._analyze_price_trends(history)
        if not price_analysis:
            return None
        
        # Calculate hot score
        hot_score = self._calculate_hot_score(price_analysis, card)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(price_analysis, hot_score)
        
        # Assess risk factors
        risk_factors = self._assess_risk_factors(card, price_analysis)
        
        return {
            'card': card,
            'price_change_percent': price_analysis['best_price_change_percent'],
            'price_change_amount': price_analysis['best_price_change_amount'],
            'hot_score': hot_score,
            'trend_direction': price_analysis['trend_direction'],
            'confidence_level': price_analysis['confidence'],
            'risk_factors': risk_factors,
            'recommendation': recommendation,
            'analysis_period': days,
            'data_points': len(history),
            'price_volatility': price_analysis['volatility'],
            'sustained_movement': price_analysis['sustained_movement']
        }
    
    def _analyze_price_trends(self, history: List[Dict]) -> Optional[Dict]:
        """Analyze price trends from historical data.
        
        Args:
            history: List of historical price entries
            
        Returns:
            Price trend analysis or None if insufficient data
        """
        if len(history) < 2:
            return None
        
        # Extract best prices over time
        best_prices = []
        timestamps = []
        
        for entry in history:
            if 'best_price' in entry and entry['best_price']:
                best_prices.append(entry['best_price'])
                timestamps.append(datetime.fromisoformat(entry['timestamp']))
        
        if len(best_prices) < 2:
            return None
        
        # Calculate price changes
        first_price = best_prices[0]
        last_price = best_prices[-1]
        price_change = last_price - first_price
        price_change_percent = (price_change / first_price) * 100 if first_price > 0 else 0
        
        # Calculate volatility (standard deviation of price changes)
        price_changes = []
        for i in range(1, len(best_prices)):
            change = best_prices[i] - best_prices[i-1]
            change_percent = (change / best_prices[i-1]) * 100 if best_prices[i-1] > 0 else 0
            price_changes.append(change_percent)
        
        volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
        
        # Determine trend direction
        if price_change_percent > self.config['spike_threshold_percent']:
            trend_direction = "strong_up"
        elif price_change_percent > 5:
            trend_direction = "up"
        elif price_change_percent < -self.config['spike_threshold_percent']:
            trend_direction = "strong_down"
        elif price_change_percent < -5:
            trend_direction = "down"
        else:
            trend_direction = "stable"
        
        # Check for sustained movement
        sustained_movement = self._check_sustained_movement(best_prices, trend_direction)
        
        # Calculate confidence based on data quality
        confidence = min(1.0, len(best_prices) / 10.0)  # More data = higher confidence
        
        return {
            'first_price': first_price,
            'last_price': last_price,
            'best_price_change_amount': price_change,
            'best_price_change_percent': price_change_percent,
            'volatility': volatility,
            'trend_direction': trend_direction,
            'sustained_movement': sustained_movement,
            'confidence': confidence,
            'data_points': len(best_prices)
        }
    
    def _check_sustained_movement(self, prices: List[float], direction: str) -> bool:
        """Check if price movement is sustained over multiple days.
        
        Args:
            prices: List of prices over time
            direction: Trend direction
            
        Returns:
            True if movement is sustained
        """
        if len(prices) < self.config['sustained_threshold_days']:
            return False
        
        # Check if the trend continues in the same direction
        if direction in ['strong_up', 'up']:
            # Check if prices are generally increasing
            increasing_count = sum(1 for i in range(1, len(prices)) 
                                 if prices[i] >= prices[i-1])
            return increasing_count >= len(prices) * 0.7
        elif direction in ['strong_down', 'down']:
            # Check if prices are generally decreasing
            decreasing_count = sum(1 for i in range(1, len(prices)) 
                                 if prices[i] <= prices[i-1])
            return decreasing_count >= len(prices) * 0.7
        
        return False
    
    def _calculate_hot_score(self, price_analysis: Dict, card: Card) -> float:
        """Calculate hot score for a card based on price movement and other factors.
        
        Args:
            price_analysis: Price trend analysis
            card: Card being analyzed
            
        Returns:
            Hot score between 0 and 1
        """
        base_score = 0.0
        
        # Price movement component (40% weight)
        price_change_percent = abs(price_analysis['best_price_change_percent'])
        if price_change_percent >= self.config['spike_threshold_percent']:
            price_score = min(1.0, price_change_percent / 50.0)  # Cap at 50% movement
        else:
            price_score = price_change_percent / self.config['spike_threshold_percent']
        
        base_score += price_score * 0.4
        
        # Sustained movement component (25% weight)
        if price_analysis['sustained_movement']:
            base_score += 0.25
        
        # Confidence component (20% weight)
        base_score += price_analysis['confidence'] * 0.2
        
        # Volatility component (15% weight) - moderate volatility is good
        volatility = price_analysis['volatility']
        if 5 <= volatility <= 20:  # Sweet spot for volatility
            volatility_score = 1.0
        elif volatility < 5:
            volatility_score = volatility / 5.0
        else:
            volatility_score = max(0, 1.0 - (volatility - 20) / 30.0)
        
        base_score += volatility_score * 0.15
        
        # Apply risk adjustments
        risk_adjustment = self._calculate_risk_adjustment(card, price_analysis)
        final_score = base_score * (1 - risk_adjustment)
        
        return max(0.0, min(1.0, final_score))
    
    def _calculate_risk_adjustment(self, card: Card, price_analysis: Dict) -> float:
        """Calculate risk adjustment factor for the hot score.
        
        Args:
            card: Card being analyzed
            price_analysis: Price trend analysis
            
        Returns:
            Risk adjustment factor between 0 and 1
        """
        risk_score = 0.0
        
        # High volatility risk
        if price_analysis['volatility'] > 25:
            risk_score += self.config['risk_factors']['high_volatility']
        
        # Low volume risk
        if price_analysis['data_points'] < 5:
            risk_score += self.config['risk_factors']['low_volume']
        
        # Recent reprint risk (simplified - would need set data)
        # This is a placeholder - in a real implementation, you'd check set release dates
        if card.set_name and any(keyword in card.set_name.lower() 
                               for keyword in ['reprint', 'remastered', 'anthology']):
            risk_score += self.config['risk_factors']['recent_reprint']
        
        # Format rotation risk (simplified)
        # This is a placeholder - would need format rotation data
        if card.set_name and any(keyword in card.set_name.lower() 
                               for keyword in ['core set', 'standard']):
            risk_score += self.config['risk_factors']['format_rotation']
        
        return min(1.0, risk_score)
    
    def _assess_risk_factors(self, card: Card, price_analysis: Dict) -> List[str]:
        """Assess specific risk factors for a card.
        
        Args:
            card: Card being analyzed
            price_analysis: Price trend analysis
            
        Returns:
            List of risk factor descriptions
        """
        risk_factors = []
        
        if price_analysis['volatility'] > 25:
            risk_factors.append("High price volatility")
        
        if price_analysis['data_points'] < 5:
            risk_factors.append("Limited price data")
        
        if not price_analysis['sustained_movement']:
            risk_factors.append("Unstable price movement")
        
        if price_analysis['confidence'] < 0.5:
            risk_factors.append("Low confidence in trend")
        
        # Add card-specific risks
        if card.is_foil():
            risk_factors.append("Foil cards have higher volatility")
        
        if card.condition.value != "Near Mint":
            risk_factors.append("Condition affects price stability")
        
        return risk_factors
    
    def _generate_recommendation(self, price_analysis: Dict, hot_score: float) -> str:
        """Generate recommendation based on analysis.
        
        Args:
            price_analysis: Price trend analysis
            hot_score: Calculated hot score
            
        Returns:
            Recommendation string
        """
        if hot_score >= 0.8:
            if price_analysis['trend_direction'] in ['strong_up', 'up']:
                return "Strong buy - significant upward momentum"
            else:
                return "Strong sell - significant downward momentum"
        elif hot_score >= 0.6:
            if price_analysis['trend_direction'] in ['strong_up', 'up']:
                return "Consider buying - positive trend"
            else:
                return "Consider selling - negative trend"
        elif hot_score >= 0.4:
            return "Monitor closely - moderate movement"
        else:
            return "Hold - minimal movement"
    
    def generate_hot_cards_report(self, hot_cards: List[Dict]) -> str:
        """Generate a formatted report of hot cards.
        
        Args:
            hot_cards: List of hot card analysis results
            
        Returns:
            Formatted report string
        """
        if not hot_cards:
            return "No hot cards detected in the current analysis period."
        
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("HOT CARDS ANALYSIS REPORT")
        report_lines.append("=" * 100)
        report_lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Hot Cards Found: {len(hot_cards)}")
        report_lines.append("")
        
        # Summary statistics
        total_value_change = sum(card['price_change_amount'] * card['card'].quantity 
                               for card in hot_cards)
        avg_change_percent = statistics.mean(card['price_change_percent'] for card in hot_cards)
        
        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Value Change: ${total_value_change:.2f}")
        report_lines.append(f"Average Price Change: {avg_change_percent:.1f}%")
        report_lines.append(f"Average Hot Score: {statistics.mean(card['hot_score'] for card in hot_cards):.2f}")
        report_lines.append("")
        
        # Individual hot cards
        report_lines.append("HOT CARDS DETAILS")
        report_lines.append("-" * 40)
        
        for i, card_analysis in enumerate(hot_cards[:10], 1):  # Top 10
            card = card_analysis['card']
            report_lines.append(f"\n{i}. {card.name} ({card.set_name})")
            report_lines.append(f"   Hot Score: {card_analysis['hot_score']:.2f}")
            report_lines.append(f"   Price Change: {card_analysis['price_change_percent']:+.1f}% (${card_analysis['price_change_amount']:+.2f})")
            report_lines.append(f"   Trend: {card_analysis['trend_direction'].replace('_', ' ').title()}")
            report_lines.append(f"   Recommendation: {card_analysis['recommendation']}")
            report_lines.append(f"   Risk Factors: {', '.join(card_analysis['risk_factors']) if card_analysis['risk_factors'] else 'None'}")
            report_lines.append(f"   Quantity: {card.quantity}")
            report_lines.append(f"   Total Value Impact: ${card_analysis['price_change_amount'] * card.quantity:+.2f}")
        
        if len(hot_cards) > 10:
            report_lines.append(f"\n... and {len(hot_cards) - 10} more hot cards")
        
        return "\n".join(report_lines)
    
    def update_config(self, **kwargs) -> None:
        """Update detector configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
            elif key == 'risk_factors':
                self.config['risk_factors'].update(value)
        
        logger.info(f"Updated hot card detector configuration: {kwargs}") 