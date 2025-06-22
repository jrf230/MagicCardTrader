"""Collection analytics and performance tracking module."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics

from .models import Card, CardPrices, CollectionSummary
from .price_history import PriceHistory

logger = logging.getLogger(__name__)


class CollectionAnalytics:
    """Provides comprehensive analytics for MTG collections."""
    
    def __init__(self, price_history: PriceHistory):
        """Initialize the collection analytics engine.
        
        Args:
            price_history: PriceHistory instance for accessing historical data
        """
        self.price_history = price_history
        self.config = {
            'growth_period_days': 30,           # Days to analyze for growth
            'diversification_threshold': 0.1,   # Minimum % for set diversification
            'risk_categories': {
                'low_risk': 0.3,               # Risk weight for low-risk cards
                'medium_risk': 0.5,            # Risk weight for medium-risk cards
                'high_risk': 0.8               # Risk weight for high-risk cards
            },
            'performance_benchmarks': {
                'market_average': 0.05,        # 5% monthly growth benchmark
                'top_performer': 0.15,         # 15% monthly growth for top performers
                'underperformer': -0.05        # -5% monthly growth for underperformers
            }
        }
    
    def analyze_collection(self, card_prices_list: List[CardPrices], 
                          collection_summary: CollectionSummary) -> Dict:
        """Perform comprehensive collection analysis.
        
        Args:
            card_prices_list: Current price data for cards
            collection_summary: Collection summary
            
        Returns:
            Comprehensive analysis results
        """
        logger.info(f"Analyzing collection with {len(card_prices_list)} cards")
        
        analysis = {
            'collection_summary': collection_summary,
            'diversification': self._analyze_diversification(card_prices_list),
            'performance': self._analyze_performance(card_prices_list),
            'risk_assessment': self._assess_risk(card_prices_list),
            'growth_tracking': self._track_growth(card_prices_list),
            'top_performers': self._identify_top_performers(card_prices_list),
            'underperformers': self._identify_underperformers(card_prices_list),
            'set_analysis': self._analyze_set_performance(card_prices_list),
            'rarity_analysis': self._analyze_rarity_distribution(card_prices_list),
            'condition_analysis': self._analyze_condition_impact(card_prices_list),
            'foil_analysis': self._analyze_foil_performance(card_prices_list)
        }
        
        return analysis
    
    def _analyze_diversification(self, card_prices_list: List[CardPrices]) -> Dict:
        """Analyze collection diversification.
        
        Args:
            card_prices_list: Current price data for cards
            
        Returns:
            Diversification analysis
        """
        set_distribution = defaultdict(float)
        rarity_distribution = defaultdict(float)
        total_value = 0.0
        
        # Calculate value distribution
        for card_prices in card_prices_list:
            if card_prices.best_bid:
                card_value = card_prices.best_bid.price * card_prices.card.quantity
                set_distribution[card_prices.card.set_name] += card_value
                if card_prices.card.rarity:
                    rarity_distribution[card_prices.card.rarity.value] += card_value
                total_value += card_value
        
        # Calculate diversification metrics
        set_concentration = {}
        for set_name, value in set_distribution.items():
            set_concentration[set_name] = value / total_value if total_value > 0 else 0
        
        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum(concentration ** 2 for concentration in set_concentration.values())
        
        # Determine diversification level
        if hhi < 0.15:
            diversification_level = "excellent"
        elif hhi < 0.25:
            diversification_level = "good"
        elif hhi < 0.4:
            diversification_level = "moderate"
        else:
            diversification_level = "poor"
        
        return {
            'set_distribution': dict(set_distribution),
            'set_concentration': set_concentration,
            'rarity_distribution': dict(rarity_distribution),
            'total_value': total_value,
            'hhi_index': hhi,
            'diversification_level': diversification_level,
            'recommendations': self._generate_diversification_recommendations(set_concentration, hhi)
        }
    
    def _analyze_performance(self, card_prices_list: List[CardPrices]) -> Dict:
        """Analyze collection performance.
        
        Args:
            card_prices_list: Current price data for cards
            
        Returns:
            Performance analysis
        """
        performance_data = []
        total_current_value = 0.0
        total_historical_value = 0.0
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid:
                continue
            
            card = card_prices.card
            current_value = card_prices.best_bid.price * card.quantity
            total_current_value += current_value
            
            # Get historical value
            history = self.price_history.get_card_history(card.name, card.set_name, 
                                                         days=self.config['growth_period_days'])
            
            if history:
                historical_prices = [entry['best_bid'] for entry in history if entry.get('best_bid')]
                if historical_prices:
                    avg_historical_price = statistics.mean(historical_prices)
                    historical_value = avg_historical_price * card.quantity
                    total_historical_value += historical_value
                    
                    growth_rate = ((current_value - historical_value) / historical_value) * 100 if historical_value > 0 else 0
                    
                    performance_data.append({
                        'card': {
                            'name': card.name,
                            'set_name': card.set_name,
                            'quantity': card.quantity,
                            'foil': card.is_foil(),
                            'rarity': card.rarity.value if card.rarity else None
                        },
                        'current_value': current_value,
                        'historical_value': historical_value,
                        'growth_rate': growth_rate,
                        'growth_amount': current_value - historical_value
                    })
        
        # Calculate overall performance
        overall_growth_rate = ((total_current_value - total_historical_value) / total_historical_value) * 100 if total_historical_value > 0 else 0
        
        # Compare to benchmarks
        benchmark_comparison = self._compare_to_benchmarks(overall_growth_rate)
        
        return {
            'total_current_value': total_current_value,
            'total_historical_value': total_historical_value,
            'overall_growth_rate': overall_growth_rate,
            'overall_growth_amount': total_current_value - total_historical_value,
            'performance_data': performance_data,
            'benchmark_comparison': benchmark_comparison,
            'performance_level': self._categorize_performance(overall_growth_rate)
        }
    
    def _assess_risk(self, card_prices_list: List[CardPrices]) -> Dict:
        """Assess collection risk.
        
        Args:
            card_prices_list: Current price data for cards
            
        Returns:
            Risk assessment
        """
        risk_categories = {
            'low_risk': {'cards': [], 'value': 0.0, 'count': 0},
            'medium_risk': {'cards': [], 'value': 0.0, 'count': 0},
            'high_risk': {'cards': [], 'value': 0.0, 'count': 0}
        }
        
        total_value = 0.0
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid:
                continue
            
            card = card_prices.card
            card_value = card_prices.best_bid.price * card.quantity
            total_value += card_value
            
            # Assess individual card risk
            risk_level = self._assess_card_risk(card, card_prices)
            risk_categories[risk_level]['cards'].append({
                'name': card.name,
                'set_name': card.set_name,
                'quantity': card.quantity,
                'foil': card.is_foil(),
                'rarity': card.rarity.value if card.rarity else None
            })
            risk_categories[risk_level]['value'] += card_value
            risk_categories[risk_level]['count'] += 1
        
        # Calculate risk metrics
        risk_metrics = {}
        for risk_level, data in risk_categories.items():
            if total_value > 0:
                risk_metrics[risk_level] = {
                    'percentage': (data['value'] / total_value) * 100,
                    'value': data['value'],
                    'count': data['count'],
                    'weighted_risk': data['value'] * self.config['risk_categories'][risk_level]
                }
            else:
                risk_metrics[risk_level] = {
                    'percentage': 0.0,
                    'value': 0.0,
                    'count': 0,
                    'weighted_risk': 0.0
                }
        
        # Calculate overall risk score
        total_weighted_risk = sum(metrics['weighted_risk'] for metrics in risk_metrics.values())
        overall_risk_score = total_weighted_risk / total_value if total_value > 0 else 0
        
        return {
            'risk_categories': risk_metrics,
            'overall_risk_score': overall_risk_score,
            'risk_level': self._categorize_risk(overall_risk_score),
            'total_value': total_value,
            'recommendations': self._generate_risk_recommendations(risk_metrics, overall_risk_score)
        }
    
    def _track_growth(self, card_prices_list: List[CardPrices]) -> Dict:
        """Track collection growth over time.
        
        Args:
            card_prices_list: Current price data for cards
            
        Returns:
            Growth tracking data
        """
        growth_periods = [7, 30, 90, 365]  # Days
        growth_data = {}
        
        for period in growth_periods:
            period_growth = self._calculate_period_growth(card_prices_list, period)
            growth_data[f"{period}_days"] = period_growth
        
        # Calculate compound annual growth rate (CAGR)
        if len(growth_periods) >= 2:
            short_term = growth_data[f"{growth_periods[0]}_days"]['growth_rate']
            long_term = growth_data[f"{growth_periods[-1]}_days"]['growth_rate']
            
            # Simplified CAGR calculation
            if long_term > 0 and short_term > 0:
                cagr = ((1 + long_term/100) ** (365/growth_periods[-1]) - 1) * 100
            else:
                cagr = 0
        else:
            cagr = 0
        
        return {
            'period_growth': growth_data,
            'cagr': cagr,
            'growth_trend': self._analyze_growth_trend(growth_data)
        }
    
    def _identify_top_performers(self, card_prices_list: List[CardPrices], 
                               limit: int = 10) -> List[Dict]:
        """Identify top performing cards.
        
        Args:
            card_prices_list: Current price data for cards
            limit: Maximum number of top performers to return
            
        Returns:
            List of top performing cards
        """
        performers = []
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid:
                continue
            
            card = card_prices.card
            current_value = card_prices.best_bid.price * card.quantity
            
            # Get historical performance
            history = self.price_history.get_card_history(card.name, card.set_name, 
                                                         days=self.config['growth_period_days'])
            
            if history:
                historical_prices = [entry['best_bid'] for entry in history if entry.get('best_bid')]
                if historical_prices:
                    avg_historical_price = statistics.mean(historical_prices)
                    historical_value = avg_historical_price * card.quantity
                    
                    growth_rate = ((current_value - historical_value) / historical_value) * 100 if historical_value > 0 else 0
                    
                    if growth_rate > self.config['performance_benchmarks']['top_performer'] * 100:
                        performers.append({
                            'card': {
                                'name': card.name,
                                'set_name': card.set_name,
                                'quantity': card.quantity,
                                'foil': card.is_foil(),
                                'rarity': card.rarity.value if card.rarity else None
                            },
                            'current_value': current_value,
                            'historical_value': historical_value,
                            'growth_rate': growth_rate,
                            'growth_amount': current_value - historical_value
                        })
        
        # Sort by growth rate and return top performers
        performers.sort(key=lambda x: x['growth_rate'], reverse=True)
        return performers[:limit]
    
    def _identify_underperformers(self, card_prices_list: List[CardPrices], 
                                limit: int = 10) -> List[Dict]:
        """Identify underperforming cards.
        
        Args:
            card_prices_list: Current price data for cards
            limit: Maximum number of underperformers to return
            
        Returns:
            List of underperforming cards
        """
        underperformers = []
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid:
                continue
            
            card = card_prices.card
            current_value = card_prices.best_bid.price * card.quantity
            
            # Get historical performance
            history = self.price_history.get_card_history(card.name, card.set_name, 
                                                         days=self.config['growth_period_days'])
            
            if history:
                historical_prices = [entry['best_bid'] for entry in history if entry.get('best_bid')]
                if historical_prices:
                    avg_historical_price = statistics.mean(historical_prices)
                    historical_value = avg_historical_price * card.quantity
                    
                    growth_rate = ((current_value - historical_value) / historical_value) * 100 if historical_value > 0 else 0
                    
                    if growth_rate < self.config['performance_benchmarks']['underperformer'] * 100:
                        underperformers.append({
                            'card': {
                                'name': card.name,
                                'set_name': card.set_name,
                                'quantity': card.quantity,
                                'foil': card.is_foil(),
                                'rarity': card.rarity.value if card.rarity else None
                            },
                            'current_value': current_value,
                            'historical_value': historical_value,
                            'growth_rate': growth_rate,
                            'growth_amount': current_value - historical_value
                        })
        
        # Sort by growth rate (ascending) and return worst performers
        underperformers.sort(key=lambda x: x['growth_rate'])
        return underperformers[:limit]
    
    def _analyze_set_performance(self, card_prices_list: List[CardPrices]) -> Dict:
        """Analyze performance by set.
        
        Args:
            card_prices_list: Current price data for cards
            
        Returns:
            Set performance analysis
        """
        set_performance = defaultdict(lambda: {
            'cards': [],
            'current_value': 0.0,
            'historical_value': 0.0,
            'growth_rate': 0.0,
            'card_count': 0
        })
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid:
                continue
            
            card = card_prices.card
            current_value = card_prices.best_bid.price * card.quantity
            
            set_data = set_performance[card.set_name]
            set_data['cards'].append({
                'name': card.name,
                'set_name': card.set_name,
                'quantity': card.quantity,
                'foil': card.is_foil(),
                'rarity': card.rarity.value if card.rarity else None
            })
            set_data['current_value'] += current_value
            set_data['card_count'] += 1
            
            # Get historical performance
            history = self.price_history.get_card_history(card.name, card.set_name, 
                                                         days=self.config['growth_period_days'])
            
            if history:
                historical_prices = [entry['best_bid'] for entry in history if entry.get('best_bid')]
                if historical_prices:
                    avg_historical_price = statistics.mean(historical_prices)
                    historical_value = avg_historical_price * card.quantity
                    set_data['historical_value'] += historical_value
        
        # Calculate growth rates for each set
        for set_name, data in set_performance.items():
            if data['historical_value'] > 0:
                data['growth_rate'] = ((data['current_value'] - data['historical_value']) / data['historical_value']) * 100
        
        return dict(set_performance)
    
    def _analyze_rarity_distribution(self, card_prices_list: List[CardPrices]) -> Dict:
        """Analyze performance by rarity.
        
        Args:
            card_prices_list: Current price data for cards
            
        Returns:
            Rarity distribution analysis
        """
        rarity_data = defaultdict(lambda: {
            'cards': [],
            'current_value': 0.0,
            'historical_value': 0.0,
            'growth_rate': 0.0,
            'card_count': 0
        })
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid or not card_prices.card.rarity:
                continue
            
            card = card_prices.card
            rarity = card.rarity.value
            current_value = card_prices.best_bid.price * card.quantity
            
            rarity_info = rarity_data[rarity]
            rarity_info['cards'].append({
                'name': card.name,
                'set_name': card.set_name,
                'quantity': card.quantity,
                'foil': card.is_foil(),
                'rarity': card.rarity.value if card.rarity else None
            })
            rarity_info['current_value'] += current_value
            rarity_info['card_count'] += 1
            
            # Get historical performance
            history = self.price_history.get_card_history(card.name, card.set_name, 
                                                         days=self.config['growth_period_days'])
            
            if history:
                historical_prices = [entry['best_bid'] for entry in history if entry.get('best_bid')]
                if historical_prices:
                    avg_historical_price = statistics.mean(historical_prices)
                    historical_value = avg_historical_price * card.quantity
                    rarity_info['historical_value'] += historical_value
        
        # Calculate growth rates for each rarity
        for rarity, data in rarity_data.items():
            if data['historical_value'] > 0:
                data['growth_rate'] = ((data['current_value'] - data['historical_value']) / data['historical_value']) * 100
        
        return dict(rarity_data)
    
    def _analyze_condition_impact(self, card_prices_list: List[CardPrices]) -> Dict:
        """Analyze the impact of card condition on value.
        
        Args:
            card_prices_list: Current price data for cards
            
        Returns:
            Condition impact analysis
        """
        condition_data = defaultdict(lambda: {
            'cards': [],
            'total_value': 0.0,
            'card_count': 0,
            'avg_price': 0.0
        })
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid:
                continue
            
            card = card_prices.card
            condition = card.condition.value
            card_value = card_prices.best_bid.price * card.quantity
            
            condition_info = condition_data[condition]
            condition_info['cards'].append({
                'name': card.name,
                'set_name': card.set_name,
                'quantity': card.quantity,
                'foil': card.is_foil(),
                'rarity': card.rarity.value if card.rarity else None
            })
            condition_info['total_value'] += card_value
            condition_info['card_count'] += 1
        
        # Calculate average prices
        for condition, data in condition_data.items():
            if data['card_count'] > 0:
                data['avg_price'] = data['total_value'] / data['card_count']
        
        return dict(condition_data)
    
    def _analyze_foil_performance(self, card_prices_list: List[CardPrices]) -> Dict:
        """Analyze foil vs non-foil performance.
        
        Args:
            card_prices_list: Current price data for cards
            
        Returns:
            Foil performance analysis
        """
        foil_data = {
            'foil': {'cards': [], 'current_value': 0.0, 'historical_value': 0.0, 'growth_rate': 0.0, 'count': 0},
            'non_foil': {'cards': [], 'current_value': 0.0, 'historical_value': 0.0, 'growth_rate': 0.0, 'count': 0}
        }
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid:
                continue
            
            card = card_prices.card
            current_value = card_prices.best_bid.price * card.quantity
            category = 'foil' if card.is_foil() else 'non_foil'
            
            foil_data[category]['cards'].append({
                'name': card.name,
                'set_name': card.set_name,
                'quantity': card.quantity,
                'foil': card.is_foil(),
                'rarity': card.rarity.value if card.rarity else None
            })
            foil_data[category]['current_value'] += current_value
            foil_data[category]['count'] += 1
            
            # Get historical performance
            history = self.price_history.get_card_history(card.name, card.set_name, 
                                                         days=self.config['growth_period_days'])
            
            if history:
                historical_prices = [entry['best_bid'] for entry in history if entry.get('best_bid')]
                if historical_prices:
                    avg_historical_price = statistics.mean(historical_prices)
                    historical_value = avg_historical_price * card.quantity
                    foil_data[category]['historical_value'] += historical_value
        
        # Calculate growth rates
        for category, data in foil_data.items():
            if data['historical_value'] > 0:
                data['growth_rate'] = ((data['current_value'] - data['historical_value']) / data['historical_value']) * 100
        
        return foil_data
    
    def _assess_card_risk(self, card: Card, card_prices: CardPrices) -> str:
        """Assess risk level for an individual card."""
        risk_score = 0
        
        # Foil cards are higher risk
        if card.is_foil():
            risk_score += 2
        
        # High-value cards are higher risk
        if card_prices.best_bid and card_prices.best_bid.price > 50:
            risk_score += 2
        elif card_prices.best_bid and card_prices.best_bid.price > 20:
            risk_score += 1
        
        # Recent sets are higher risk (potential reprints)
        if card.set_name and any(keyword in card.set_name.lower() 
                               for keyword in ['2023', '2024', 'commander']):
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 4:
            return 'high_risk'
        elif risk_score >= 2:
            return 'medium_risk'
        else:
            return 'low_risk'
    
    def _calculate_period_growth(self, card_prices_list: List[CardPrices], days: int) -> Dict:
        """Calculate growth for a specific time period."""
        total_current_value = 0.0
        total_historical_value = 0.0
        
        for card_prices in card_prices_list:
            if not card_prices.best_bid:
                continue
            
            card = card_prices.card
            current_value = card_prices.best_bid.price * card.quantity
            total_current_value += current_value
            
            # Get historical value
            history = self.price_history.get_card_history(card.name, card.set_name, days=days)
            
            if history:
                historical_prices = [entry['best_bid'] for entry in history if entry.get('best_bid')]
                if historical_prices:
                    avg_historical_price = statistics.mean(historical_prices)
                    historical_value = avg_historical_price * card.quantity
                    total_historical_value += historical_value
        
        growth_rate = ((total_current_value - total_historical_value) / total_historical_value) * 100 if total_historical_value > 0 else 0
        
        return {
            'current_value': total_current_value,
            'historical_value': total_historical_value,
            'growth_rate': growth_rate,
            'growth_amount': total_current_value - total_historical_value
        }
    
    def _compare_to_benchmarks(self, growth_rate: float) -> Dict:
        """Compare performance to benchmarks."""
        benchmarks = self.config['performance_benchmarks']
        
        return {
            'market_average': growth_rate - (benchmarks['market_average'] * 100),
            'top_performer': growth_rate - (benchmarks['top_performer'] * 100),
            'underperformer': growth_rate - (benchmarks['underperformer'] * 100)
        }
    
    def _categorize_performance(self, growth_rate: float) -> str:
        """Categorize performance level."""
        if growth_rate >= 15:
            return "excellent"
        elif growth_rate >= 5:
            return "good"
        elif growth_rate >= -5:
            return "stable"
        else:
            return "poor"
    
    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk level."""
        if risk_score <= 0.4:
            return "low"
        elif risk_score <= 0.6:
            return "medium"
        else:
            return "high"
    
    def _analyze_growth_trend(self, growth_data: Dict) -> str:
        """Analyze growth trend across periods."""
        periods = list(growth_data.keys())
        if len(periods) < 2:
            return "insufficient_data"
        
        # Compare short-term vs long-term growth
        short_term = growth_data[periods[0]]['growth_rate']
        long_term = growth_data[periods[-1]]['growth_rate']
        
        if short_term > long_term * 1.5:
            return "accelerating"
        elif short_term < long_term * 0.5:
            return "decelerating"
        else:
            return "stable"
    
    def _generate_diversification_recommendations(self, set_concentration: Dict, hhi: float) -> List[str]:
        """Generate diversification recommendations."""
        recommendations = []
        
        if hhi > 0.4:
            recommendations.append("Consider diversifying across more sets to reduce concentration risk")
        
        # Find most concentrated sets
        top_sets = sorted(set_concentration.items(), key=lambda x: x[1], reverse=True)[:3]
        for set_name, concentration in top_sets:
            if concentration > 0.2:
                recommendations.append(f"Reduce exposure to {set_name} (currently {concentration:.1%} of collection)")
        
        if len(set_concentration) < 5:
            recommendations.append("Consider adding cards from more diverse sets")
        
        return recommendations
    
    def _generate_risk_recommendations(self, risk_metrics: Dict, overall_risk_score: float) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if overall_risk_score > 0.6:
            recommendations.append("Consider reducing high-risk card exposure")
        
        high_risk_pct = risk_metrics.get('high_risk', {}).get('percentage', 0)
        if high_risk_pct > 30:
            recommendations.append(f"High-risk cards represent {high_risk_pct:.1f}% of collection - consider rebalancing")
        
        low_risk_pct = risk_metrics.get('low_risk', {}).get('percentage', 0)
        if low_risk_pct < 20:
            recommendations.append("Consider adding more low-risk, stable cards")
        
        return recommendations
    
    def generate_analytics_report(self, analysis: Dict) -> str:
        """Generate a comprehensive analytics report.
        
        Args:
            analysis: Collection analysis results
            
        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("COLLECTION ANALYTICS REPORT")
        report_lines.append("=" * 100)
        report_lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Collection Summary
        summary = analysis['collection_summary']
        report_lines.append("COLLECTION SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Cards: {summary.total_cards}")
        report_lines.append(f"Cards with Prices: {summary.cards_with_prices}")
        report_lines.append(f"Total Value: ${summary.best_total_value:.2f}")
        report_lines.append(f"Best Vendor: {summary.best_vendor}")
        report_lines.append("")
        
        # Performance Analysis
        performance = analysis['performance']
        report_lines.append("PERFORMANCE ANALYSIS")
        report_lines.append("-" * 40)
        report_lines.append(f"Overall Growth Rate: {performance['overall_growth_rate']:+.1f}%")
        report_lines.append(f"Performance Level: {performance['performance_level'].title()}")
        report_lines.append(f"Growth Amount: ${performance['overall_growth_amount']:+.2f}")
        report_lines.append("")
        
        # Diversification Analysis
        diversification = analysis['diversification']
        report_lines.append("DIVERSIFICATION ANALYSIS")
        report_lines.append("-" * 40)
        report_lines.append(f"Diversification Level: {diversification['diversification_level'].title()}")
        report_lines.append(f"HHI Index: {diversification['hhi_index']:.3f}")
        report_lines.append(f"Number of Sets: {len(diversification['set_distribution'])}")
        report_lines.append("")
        
        # Risk Assessment
        risk = analysis['risk_assessment']
        report_lines.append("RISK ASSESSMENT")
        report_lines.append("-" * 40)
        report_lines.append(f"Overall Risk Level: {risk['risk_level'].title()}")
        report_lines.append(f"Risk Score: {risk['overall_risk_score']:.3f}")
        
        for risk_level, data in risk['risk_categories'].items():
            if data['percentage'] > 0:
                report_lines.append(f"{risk_level.replace('_', ' ').title()}: {data['percentage']:.1f}% (${data['value']:.2f})")
        report_lines.append("")
        
        # Top Performers
        top_performers = analysis['top_performers']
        if top_performers:
            report_lines.append("TOP PERFORMERS")
            report_lines.append("-" * 40)
            for i, performer in enumerate(top_performers[:5], 1):
                card = performer['card']
                report_lines.append(f"{i}. {card['name']} ({card['set_name']}): {performer['growth_rate']:+.1f}%")
        report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 40)
        
        # Diversification recommendations
        for rec in diversification['recommendations']:
            report_lines.append(f"• {rec}")
        
        # Risk recommendations
        for rec in risk['recommendations']:
            report_lines.append(f"• {rec}")
        
        return "\n".join(report_lines)

# TODO: Multi-user support - add user_id to all analytics and reporting
# TODO: Web dashboard - expose analytics and recommendations via Flask/FastAPI
# TODO: Advanced analytics - add clustering, outlier detection, and predictive modeling 