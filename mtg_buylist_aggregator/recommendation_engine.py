"""Strategic recommendation engine for MTG collection optimization."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics

from .models import Card, CardPrices, CollectionSummary
from .price_history import PriceHistory
from .hot_card_detector import HotCardDetector

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Provides strategic recommendations for buying, selling, and holding cards."""
    
    def __init__(self, price_history: PriceHistory, hot_card_detector: HotCardDetector):
        """Initialize the recommendation engine.
        
        Args:
            price_history: PriceHistory instance for accessing historical data
            hot_card_detector: HotCardDetector instance for hot card analysis
        """
        self.price_history = price_history
        self.hot_card_detector = hot_card_detector
        self.config = {
            'sell_threshold_percent': 20.0,      # Minimum % gain to recommend selling
            'buy_threshold_percent': -15.0,      # Maximum % loss to recommend buying
            'hold_threshold_days': 30,           # Days to analyze for hold recommendations
            'confidence_threshold': 0.6,         # Minimum confidence for recommendations
            'max_recommendations': 20,           # Maximum recommendations per category
            'risk_tolerance': 'moderate',        # Risk tolerance level
            'investment_horizon': 'medium',      # Investment time horizon
            'portfolio_balance_weight': 0.3,     # Weight for portfolio balance in recommendations
            'price_momentum_weight': 0.4,        # Weight for price momentum
            'market_timing_weight': 0.3          # Weight for market timing
        }
    
    def generate_recommendations(self, card_prices_list: List[CardPrices], 
                               collection_summary: CollectionSummary) -> Dict[str, List[Dict]]:
        """Generate comprehensive recommendations for the collection.
        
        Args:
            card_prices_list: Current price data for cards
            collection_summary: Collection summary for context
            
        Returns:
            Dictionary with buy, sell, and hold recommendations
        """
        logger.info(f"Generating recommendations for {len(card_prices_list)} cards")
        
        # Get hot cards for context
        hot_cards = self.hot_card_detector.detect_hot_cards(card_prices_list, days=7)
        hot_card_names = {card['card'].name for card in hot_cards}
        
        # Generate recommendations by category
        sell_recommendations = self._generate_sell_recommendations(
            card_prices_list, collection_summary, hot_card_names)
        
        buy_recommendations = self._generate_buy_recommendations(
            card_prices_list, collection_summary, hot_card_names)
        
        hold_recommendations = self._generate_hold_recommendations(
            card_prices_list, collection_summary, hot_card_names)
        
        return {
            'sell': sell_recommendations,
            'buy': buy_recommendations,
            'hold': hold_recommendations,
            'summary': self._generate_recommendation_summary(
                sell_recommendations, buy_recommendations, hold_recommendations)
        }
    
    def _generate_sell_recommendations(self, card_prices_list: List[CardPrices],
                                     collection_summary: CollectionSummary,
                                     hot_card_names: set) -> List[Dict]:
        """Generate sell recommendations.
        
        Args:
            card_prices_list: Current price data
            collection_summary: Collection summary
            hot_card_names: Set of hot card names for context
            
        Returns:
            List of sell recommendations
        """
        recommendations = []
        
        for card_prices in card_prices_list:
            card = card_prices.card
            
            # Skip cards without price data
            if not card_prices.prices:
                continue
            
            # Analyze sell potential
            sell_analysis = self._analyze_sell_potential(card, card_prices, hot_card_names)
            
            if sell_analysis and sell_analysis['confidence'] >= self.config['confidence_threshold']:
                recommendations.append(sell_analysis)
        
        # Sort by confidence and expected value
        recommendations.sort(key=lambda x: (x['confidence'], x['expected_value']), reverse=True)
        
        return recommendations[:self.config['max_recommendations']]
    
    def _analyze_sell_potential(self, card: Card, card_prices: CardPrices, 
                              hot_card_names: set) -> Optional[Dict]:
        """Analyze sell potential for a card.
        
        Args:
            card: Card to analyze
            card_prices: Price data for the card
            hot_card_names: Set of hot card names
            
        Returns:
            Sell analysis or None if not recommended
        """
        # Get price history
        history = self.price_history.get_card_history(card.name, card.set_name, days=30)
        
        if len(history) < 3:
            return None
        
        # Calculate price metrics
        current_price = card_prices.best_price or 0
        if current_price == 0:
            return None
        
        # Calculate historical metrics
        historical_prices = [entry['best_price'] for entry in history if entry.get('best_price')]
        if len(historical_prices) < 2:
            return None
        
        avg_price = statistics.mean(historical_prices)
        max_price = max(historical_prices)
        min_price = min(historical_prices)
        
        # Calculate price change from average
        price_change_percent = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
        
        # Calculate momentum (recent vs older prices)
        recent_prices = historical_prices[-3:]  # Last 3 data points
        older_prices = historical_prices[:-3] if len(historical_prices) > 3 else historical_prices
        
        if older_prices:
            recent_avg = statistics.mean(recent_prices)
            older_avg = statistics.mean(older_prices)
            momentum = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
        else:
            momentum = 0
        
        # Assess sell signals
        sell_signals = []
        confidence = 0.0
        reasoning = []
        
        # High price relative to history
        if price_change_percent > self.config['sell_threshold_percent']:
            sell_signals.append('high_price')
            confidence += 0.3
            reasoning.append(f"Price is {price_change_percent:.1f}% above average")
        
        # Near historical high
        if current_price >= max_price * 0.95:
            sell_signals.append('near_peak')
            confidence += 0.2
            reasoning.append("Price near historical high")
        
        # Negative momentum
        if momentum < -5:
            sell_signals.append('negative_momentum')
            confidence += 0.2
            reasoning.append(f"Negative momentum: {momentum:.1f}%")
        
        # Hot card status (consider selling if overvalued)
        if card.name in hot_card_names:
            sell_signals.append('hot_card')
            confidence += 0.1
            reasoning.append("Currently a hot card - consider selling high")
        
        # High volatility (opportunity to sell)
        price_changes = [abs(historical_prices[i] - historical_prices[i-1]) / historical_prices[i-1] * 100
                        for i in range(1, len(historical_prices))]
        volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
        
        if volatility > 20:
            sell_signals.append('high_volatility')
            confidence += 0.1
            reasoning.append(f"High volatility ({volatility:.1f}%) - good selling opportunity")
        
        # Calculate expected value
        expected_value = current_price * card.quantity
        potential_profit = (current_price - avg_price) * card.quantity
        
        # Risk assessment
        risk_level = self._assess_sell_risk(card, price_change_percent, volatility)
        
        if confidence >= 0.3:  # Minimum threshold for sell recommendation
            return {
                'card': card,
                'action': 'sell',
                'confidence': min(1.0, confidence),
                'reasoning': reasoning,
                'expected_value': expected_value,
                'potential_profit': potential_profit,
                'risk_level': risk_level,
                'timeframe': 'immediate',
                'current_price': current_price,
                'avg_price': avg_price,
                'price_change_percent': price_change_percent,
                'momentum': momentum,
                'volatility': volatility,
                'sell_signals': sell_signals
            }
        
        return None
    
    def _generate_buy_recommendations(self, card_prices_list: List[CardPrices],
                                    collection_summary: CollectionSummary,
                                    hot_card_names: set) -> List[Dict]:
        """Generate buy recommendations.
        
        Args:
            card_prices_list: Current price data
            collection_summary: Collection summary
            hot_card_names: Set of hot card names for context
            
        Returns:
            List of buy recommendations
        """
        recommendations = []
        
        for card_prices in card_prices_list:
            card = card_prices.card
            
            # Skip cards without price data
            if not card_prices.prices:
                continue
            
            # Analyze buy potential
            buy_analysis = self._analyze_buy_potential(card, card_prices, hot_card_names)
            
            if buy_analysis and buy_analysis['confidence'] >= self.config['confidence_threshold']:
                recommendations.append(buy_analysis)
        
        # Sort by confidence and expected value
        recommendations.sort(key=lambda x: (x['confidence'], x['expected_value']), reverse=True)
        
        return recommendations[:self.config['max_recommendations']]
    
    def _analyze_buy_potential(self, card: Card, card_prices: CardPrices,
                             hot_card_names: set) -> Optional[Dict]:
        """Analyze buy potential for a card.
        
        Args:
            card: Card to analyze
            card_prices: Price data for the card
            hot_card_names: Set of hot card names
            
        Returns:
            Buy analysis or None if not recommended
        """
        # Get price history
        history = self.price_history.get_card_history(card.name, card.set_name, days=30)
        
        if len(history) < 3:
            return None
        
        # Calculate price metrics
        current_price = card_prices.best_price or 0
        if current_price == 0:
            return None
        
        # Calculate historical metrics
        historical_prices = [entry['best_price'] for entry in history if entry.get('best_price')]
        if len(historical_prices) < 2:
            return None
        
        avg_price = statistics.mean(historical_prices)
        max_price = max(historical_prices)
        min_price = min(historical_prices)
        
        # Calculate price change from average
        price_change_percent = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
        
        # Calculate momentum
        recent_prices = historical_prices[-3:]
        older_prices = historical_prices[:-3] if len(historical_prices) > 3 else historical_prices
        
        if older_prices:
            recent_avg = statistics.mean(recent_prices)
            older_avg = statistics.mean(older_prices)
            momentum = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
        else:
            momentum = 0
        
        # Assess buy signals
        buy_signals = []
        confidence = 0.0
        reasoning = []
        
        # Low price relative to history
        if price_change_percent < self.config['buy_threshold_percent']:
            buy_signals.append('low_price')
            confidence += 0.3
            reasoning.append(f"Price is {abs(price_change_percent):.1f}% below average")
        
        # Near historical low
        if current_price <= min_price * 1.05:
            buy_signals.append('near_bottom')
            confidence += 0.2
            reasoning.append("Price near historical low")
        
        # Positive momentum
        if momentum > 5:
            buy_signals.append('positive_momentum')
            confidence += 0.2
            reasoning.append(f"Positive momentum: {momentum:.1f}%")
        
        # Hot card status (consider buying if undervalued)
        if card.name in hot_card_names and price_change_percent < 0:
            buy_signals.append('hot_card_opportunity')
            confidence += 0.2
            reasoning.append("Hot card at discounted price")
        
        # Low volatility (stable investment)
        price_changes = [abs(historical_prices[i] - historical_prices[i-1]) / historical_prices[i-1] * 100
                        for i in range(1, len(historical_prices))]
        volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
        
        if volatility < 10:
            buy_signals.append('low_volatility')
            confidence += 0.1
            reasoning.append(f"Low volatility ({volatility:.1f}%) - stable investment")
        
        # Calculate expected value
        expected_value = current_price
        potential_savings = (avg_price - current_price) if current_price < avg_price else 0
        
        # Risk assessment
        risk_level = self._assess_buy_risk(card, price_change_percent, volatility)
        
        if confidence >= 0.3:  # Minimum threshold for buy recommendation
            return {
                'card': card,
                'action': 'buy',
                'confidence': min(1.0, confidence),
                'reasoning': reasoning,
                'expected_value': expected_value,
                'potential_savings': potential_savings,
                'risk_level': risk_level,
                'timeframe': '1-3 months',
                'current_price': current_price,
                'avg_price': avg_price,
                'price_change_percent': price_change_percent,
                'momentum': momentum,
                'volatility': volatility,
                'buy_signals': buy_signals
            }
        
        return None
    
    def _generate_hold_recommendations(self, card_prices_list: List[CardPrices],
                                     collection_summary: CollectionSummary,
                                     hot_card_names: set) -> List[Dict]:
        """Generate hold recommendations.
        
        Args:
            card_prices_list: Current price data
            collection_summary: Collection summary
            hot_card_names: Set of hot card names for context
            
        Returns:
            List of hold recommendations
        """
        recommendations = []
        
        for card_prices in card_prices_list:
            card = card_prices.card
            
            # Skip cards without price data
            if not card_prices.prices:
                continue
            
            # Analyze hold potential
            hold_analysis = self._analyze_hold_potential(card, card_prices, hot_card_names)
            
            if hold_analysis and hold_analysis['confidence'] >= self.config['confidence_threshold']:
                recommendations.append(hold_analysis)
        
        # Sort by confidence and expected value
        recommendations.sort(key=lambda x: (x['confidence'], x['expected_value']), reverse=True)
        
        return recommendations[:self.config['max_recommendations']]
    
    def _analyze_hold_potential(self, card: Card, card_prices: CardPrices,
                              hot_card_names: set) -> Optional[Dict]:
        """Analyze hold potential for a card.
        
        Args:
            card: Card to analyze
            card_prices: Price data for the card
            hot_card_names: Set of hot card names
            
        Returns:
            Hold analysis or None if not recommended
        """
        # Get price history
        history = self.price_history.get_card_history(card.name, card.set_name, 
                                                     days=self.config['hold_threshold_days'])
        
        if len(history) < 5:
            return None
        
        # Calculate price metrics
        current_price = card_prices.best_price or 0
        if current_price == 0:
            return None
        
        # Calculate historical metrics
        historical_prices = [entry['best_price'] for entry in history if entry.get('best_price')]
        if len(historical_prices) < 3:
            return None
        
        avg_price = statistics.mean(historical_prices)
        max_price = max(historical_prices)
        min_price = min(historical_prices)
        
        # Calculate price change from average
        price_change_percent = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
        
        # Calculate long-term trend
        if len(historical_prices) >= 7:
            recent_avg = statistics.mean(historical_prices[-7:])
            older_avg = statistics.mean(historical_prices[:-7])
            long_term_trend = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
        else:
            long_term_trend = 0
        
        # Assess hold signals
        hold_signals = []
        confidence = 0.0
        reasoning = []
        
        # Stable price near average
        if abs(price_change_percent) < 10:
            hold_signals.append('stable_price')
            confidence += 0.3
            reasoning.append("Price stable near historical average")
        
        # Positive long-term trend
        if long_term_trend > 5:
            hold_signals.append('positive_trend')
            confidence += 0.3
            reasoning.append(f"Positive long-term trend: {long_term_trend:.1f}%")
        
        # Hot card with strong fundamentals
        if card.name in hot_card_names and long_term_trend > 0:
            hold_signals.append('hot_card_hold')
            confidence += 0.2
            reasoning.append("Hot card with strong fundamentals - hold for growth")
        
        # Low volatility (stable investment)
        price_changes = [abs(historical_prices[i] - historical_prices[i-1]) / historical_prices[i-1] * 100
                        for i in range(1, len(historical_prices))]
        volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
        
        if volatility < 15:
            hold_signals.append('low_volatility')
            confidence += 0.2
            reasoning.append(f"Low volatility ({volatility:.1f}%) - stable hold")
        
        # Calculate expected value
        expected_value = current_price * card.quantity
        potential_growth = (long_term_trend / 100) * expected_value if long_term_trend > 0 else 0
        
        # Risk assessment
        risk_level = self._assess_hold_risk(card, price_change_percent, volatility)
        
        if confidence >= 0.4:  # Higher threshold for hold recommendations
            return {
                'card': card,
                'action': 'hold',
                'confidence': min(1.0, confidence),
                'reasoning': reasoning,
                'expected_value': expected_value,
                'potential_growth': potential_growth,
                'risk_level': risk_level,
                'timeframe': '3-12 months',
                'current_price': current_price,
                'avg_price': avg_price,
                'price_change_percent': price_change_percent,
                'long_term_trend': long_term_trend,
                'volatility': volatility,
                'hold_signals': hold_signals
            }
        
        return None
    
    def _assess_sell_risk(self, card: Card, price_change_percent: float, volatility: float) -> str:
        """Assess risk level for sell recommendation."""
        risk_score = 0
        
        if price_change_percent > 50:
            risk_score += 2  # Very high price - higher risk of missing further gains
        elif price_change_percent > 30:
            risk_score += 1
        
        if volatility > 30:
            risk_score += 2  # High volatility - price could swing either way
        elif volatility > 20:
            risk_score += 1
        
        if card.is_foil():
            risk_score += 1  # Foils are more volatile
        
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _assess_buy_risk(self, card: Card, price_change_percent: float, volatility: float) -> str:
        """Assess risk level for buy recommendation."""
        risk_score = 0
        
        if price_change_percent < -50:
            risk_score += 2  # Very low price - could indicate fundamental issues
        elif price_change_percent < -30:
            risk_score += 1
        
        if volatility > 30:
            risk_score += 2  # High volatility - price could continue falling
        elif volatility > 20:
            risk_score += 1
        
        if card.is_foil():
            risk_score += 1  # Foils are more volatile
        
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _assess_hold_risk(self, card: Card, price_change_percent: float, volatility: float) -> str:
        """Assess risk level for hold recommendation."""
        risk_score = 0
        
        if abs(price_change_percent) > 30:
            risk_score += 1  # Significant deviation from average
        
        if volatility > 25:
            risk_score += 2  # High volatility makes holding risky
        elif volatility > 15:
            risk_score += 1
        
        if card.is_foil():
            risk_score += 1  # Foils are more volatile
        
        if risk_score >= 3:
            return "high"
        elif risk_score >= 1:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation_summary(self, sell_recs: List[Dict], 
                                       buy_recs: List[Dict], 
                                       hold_recs: List[Dict]) -> Dict:
        """Generate summary of all recommendations."""
        total_sell_value = sum(rec['expected_value'] for rec in sell_recs)
        total_buy_value = sum(rec['expected_value'] for rec in buy_recs)
        total_hold_value = sum(rec['expected_value'] for rec in hold_recs)
        
        total_potential_profit = sum(rec['potential_profit'] for rec in sell_recs)
        total_potential_savings = sum(rec['potential_savings'] for rec in buy_recs)
        total_potential_growth = sum(rec['potential_growth'] for rec in hold_recs)
        
        return {
            'total_recommendations': len(sell_recs) + len(buy_recs) + len(hold_recs),
            'sell_count': len(sell_recs),
            'buy_count': len(buy_recs),
            'hold_count': len(hold_recs),
            'total_sell_value': total_sell_value,
            'total_buy_value': total_buy_value,
            'total_hold_value': total_hold_value,
            'total_potential_profit': total_potential_profit,
            'total_potential_savings': total_potential_savings,
            'total_potential_growth': total_potential_growth,
            'net_potential_value': total_potential_profit + total_potential_savings + total_potential_growth
        }
    
    def generate_recommendation_report(self, recommendations: Dict) -> str:
        """Generate a formatted recommendation report.
        
        Args:
            recommendations: Dictionary with buy, sell, and hold recommendations
            
        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("STRATEGIC RECOMMENDATIONS REPORT")
        report_lines.append("=" * 100)
        report_lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary
        summary = recommendations['summary']
        report_lines.append("RECOMMENDATION SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Recommendations: {summary['total_recommendations']}")
        report_lines.append(f"Sell: {summary['sell_count']} cards (${summary['total_sell_value']:.2f})")
        report_lines.append(f"Buy: {summary['buy_count']} cards (${summary['total_buy_value']:.2f})")
        report_lines.append(f"Hold: {summary['hold_count']} cards (${summary['total_hold_value']:.2f})")
        report_lines.append("")
        report_lines.append(f"Potential Profit from Selling: ${summary['total_potential_profit']:.2f}")
        report_lines.append(f"Potential Savings from Buying: ${summary['total_potential_savings']:.2f}")
        report_lines.append(f"Potential Growth from Holding: ${summary['total_potential_growth']:.2f}")
        report_lines.append(f"Net Potential Value: ${summary['net_potential_value']:.2f}")
        report_lines.append("")
        
        # Sell recommendations
        if recommendations['sell']:
            report_lines.append("SELL RECOMMENDATIONS")
            report_lines.append("-" * 40)
            for i, rec in enumerate(recommendations['sell'][:10], 1):
                card = rec['card']
                report_lines.append(f"\n{i}. {card.name} ({card.set_name})")
                report_lines.append(f"   Confidence: {rec['confidence']:.2f}")
                report_lines.append(f"   Current Price: ${rec['current_price']:.2f}")
                report_lines.append(f"   Potential Profit: ${rec['potential_profit']:.2f}")
                report_lines.append(f"   Risk Level: {rec['risk_level'].title()}")
                report_lines.append(f"   Reasoning: {'; '.join(rec['reasoning'])}")
        
        # Buy recommendations
        if recommendations['buy']:
            report_lines.append("\nBUY RECOMMENDATIONS")
            report_lines.append("-" * 40)
            for i, rec in enumerate(recommendations['buy'][:10], 1):
                card = rec['card']
                report_lines.append(f"\n{i}. {card.name} ({card.set_name})")
                report_lines.append(f"   Confidence: {rec['confidence']:.2f}")
                report_lines.append(f"   Current Price: ${rec['current_price']:.2f}")
                report_lines.append(f"   Potential Savings: ${rec['potential_savings']:.2f}")
                report_lines.append(f"   Risk Level: {rec['risk_level'].title()}")
                report_lines.append(f"   Reasoning: {'; '.join(rec['reasoning'])}")
        
        # Hold recommendations
        if recommendations['hold']:
            report_lines.append("\nHOLD RECOMMENDATIONS")
            report_lines.append("-" * 40)
            for i, rec in enumerate(recommendations['hold'][:10], 1):
                card = rec['card']
                report_lines.append(f"\n{i}. {card.name} ({card.set_name})")
                report_lines.append(f"   Confidence: {rec['confidence']:.2f}")
                report_lines.append(f"   Current Price: ${rec['current_price']:.2f}")
                report_lines.append(f"   Potential Growth: ${rec['potential_growth']:.2f}")
                report_lines.append(f"   Risk Level: {rec['risk_level'].title()}")
                report_lines.append(f"   Reasoning: {'; '.join(rec['reasoning'])}")
        
        return "\n".join(report_lines)
    
    def update_config(self, **kwargs) -> None:
        """Update recommendation engine configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
        
        logger.info(f"Updated recommendation engine configuration: {kwargs}") 