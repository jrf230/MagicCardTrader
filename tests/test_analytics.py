"""
Tests for the analytics and recommendation features.
"""

import pytest
from unittest.mock import Mock, patch
from mtg_buylist_aggregator.models import Card, CardPrices, CollectionSummary, PriceData
from mtg_buylist_aggregator.hot_card_detector import HotCardDetector
from mtg_buylist_aggregator.recommendation_engine import RecommendationEngine
from mtg_buylist_aggregator.collection_analytics import CollectionAnalytics
from mtg_buylist_aggregator.price_history import PriceHistory
import subprocess
import sys


class TestHotCardDetector:
    """Test the HotCardDetector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_history = Mock(spec=PriceHistory)
        self.detector = HotCardDetector(self.mock_history)

        # Create sample cards
        self.sample_cards = [
            Card(name="Test Card 1", set_name="Test Set", quantity=2, foil=False),
            Card(name="Test Card 2", set_name="Test Set", quantity=1, foil=True),
        ]

        # Create sample card prices
        self.sample_prices = [
            CardPrices(
                card=self.sample_cards[0],
                prices={
                    "Star City Games": PriceData(
                        vendor="Star City Games", price=10.0, condition="NM"
                    ),
                    "Card Kingdom": PriceData(
                        vendor="Card Kingdom", price=12.0, condition="LP"
                    ),
                },
                best_price=12.0,
                best_vendor="Card Kingdom",
            ),
            CardPrices(
                card=self.sample_cards[1],
                prices={
                    "Star City Games": PriceData(
                        vendor="Star City Games", price=25.0, condition="NM"
                    ),
                    "Card Kingdom": PriceData(
                        vendor="Card Kingdom", price=30.0, condition="LP"
                    ),
                },
                best_price=30.0,
                best_vendor="Card Kingdom",
            ),
        ]

    def test_detect_hot_cards_no_history(self):
        """Test hot card detection when no history is available."""
        self.mock_history.get_card_history.return_value = []

        hot_cards = self.detector.detect_hot_cards(self.sample_prices, days=7)

        assert len(hot_cards) == 0
        self.mock_history.get_card_history.assert_called()

    def test_detect_hot_cards_with_history(self):
        """Test hot card detection with price history."""
        # Mock history data showing a price increase, with at least 5 data points
        mock_history_data = [
            {
                "timestamp": f"2025-06-1{i}T10:00:00",
                "prices": {
                    "Star City Games": {"price": 1.0 + i * 0.1, "condition": "NM"}
                },
                "best_price": 1.0 + i * 0.1,
                "best_vendor": "Star City Games",
            }
            for i in range(5)
        ]
        # Last entry is a spike
        mock_history_data[-1]["prices"]["Star City Games"]["price"] = 2.0
        mock_history_data[-1]["best_price"] = 2.0
        self.mock_history.get_card_history.return_value = mock_history_data

        hot_cards = self.detector.detect_hot_cards(self.sample_prices, days=7)

        # Should detect hot cards due to price increase
        assert len(hot_cards) > 0
        assert hot_cards[0]["card"].name == "Test Card 1"
        assert hot_cards[0]["price_change_percent"] > 0

    def test_generate_hot_cards_report(self):
        """Test hot cards report generation."""
        hot_cards = [
            {
                "card": self.sample_cards[0],
                "hot_score": 85.5,
                "price_change_percent": 20.0,
                "price_change_amount": 2.0,
                "trend_direction": "strong_up",
                "recommendation": "Consider selling",
                "risk_factors": ["High volatility"],
                "current_price": 12.0,
            }
        ]

        report = self.detector.generate_hot_cards_report(hot_cards)

        assert "HOT CARDS ANALYSIS REPORT" in report
        assert "Test Card 1" in report
        assert "20.0%" in report
        assert "Consider selling" in report


class TestRecommendationEngine:
    """Test the RecommendationEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_history = Mock(spec=PriceHistory)
        self.mock_hot_detector = Mock(spec=HotCardDetector)
        self.engine = RecommendationEngine(self.mock_history, self.mock_hot_detector)

        # Create sample data
        self.sample_cards = [
            Card(name="Test Card 1", set_name="Test Set", quantity=2, foil=False),
            Card(name="Test Card 2", set_name="Test Set", quantity=1, foil=True),
        ]

        self.sample_prices = [
            CardPrices(
                card=self.sample_cards[0],
                prices={
                    "Star City Games": PriceData(
                        vendor="Star City Games", price=10.0, condition="NM"
                    ),
                    "Card Kingdom": PriceData(
                        vendor="Card Kingdom", price=12.0, condition="LP"
                    ),
                },
                best_price=12.0,
                best_vendor="Card Kingdom",
            ),
            CardPrices(
                card=self.sample_cards[1],
                prices={
                    "Star City Games": PriceData(
                        vendor="Star City Games", price=25.0, condition="NM"
                    ),
                    "Card Kingdom": PriceData(
                        vendor="Card Kingdom", price=30.0, condition="LP"
                    ),
                },
                best_price=30.0,
                best_vendor="Card Kingdom",
            ),
        ]

        self.sample_summary = CollectionSummary(
            total_cards=2,
            cards_with_prices=2,
            cards_without_prices=0,
            best_total_value=42.0,
            best_vendor="Card Kingdom",
            average_price=21.0,
            price_range=(10.0, 30.0),
        )

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        # Mock hot card detection
        self.mock_hot_detector.detect_hot_cards.return_value = []

        # Mock price history
        self.mock_history.get_card_history.return_value = []

        recommendations = self.engine.generate_recommendations(
            self.sample_prices, self.sample_summary
        )

        assert "sell" in recommendations
        assert "buy" in recommendations
        assert "hold" in recommendations
        assert isinstance(recommendations["sell"], list)
        assert isinstance(recommendations["buy"], list)
        assert isinstance(recommendations["hold"], list)

    def test_generate_recommendation_report(self):
        """Test recommendation report generation."""
        recommendations = {
            "sell": [
                {
                    "card": self.sample_cards[0],
                    "confidence": 0.85,
                    "current_price": 12.0,
                    "potential_profit": 2.0,
                    "risk_level": "low",
                    "timeframe": "1-2 weeks",
                    "reasoning": ["Price spike detected", "Good profit margin"],
                }
            ],
            "buy": [],
            "hold": [],
            "summary": {
                "total_recommendations": 1,
                "sell_count": 1,
                "buy_count": 0,
                "hold_count": 0,
                "potential_profit": 2.0,
                "potential_savings": 0.0,
                "potential_growth": 0.0,
                "net_potential_value": 2.0,
                "total_sell_value": 12.0,
                "total_buy_value": 0.0,
                "total_hold_value": 0.0,
                "total_potential_profit": 2.0,
                "total_potential_savings": 0.0,
                "total_potential_growth": 0.0,
            },
        }

        report = self.engine.generate_recommendation_report(recommendations)

        assert "STRATEGIC RECOMMENDATIONS REPORT" in report
        assert "Test Card 1" in report
        assert "SELL" in report
        assert "Confidence: 0.85" in report  # Confidence level


class TestCollectionAnalytics:
    """Test the CollectionAnalytics class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_history = Mock(spec=PriceHistory)
        self.analytics = CollectionAnalytics(self.mock_history)

        # Create sample data
        self.sample_cards = [
            Card(name="Test Card 1", set_name="Test Set 1", quantity=2, foil=False),
            Card(name="Test Card 2", set_name="Test Set 2", quantity=1, foil=True),
            Card(name="Test Card 3", set_name="Test Set 1", quantity=3, foil=False),
        ]

        self.sample_prices = [
            CardPrices(
                card=self.sample_cards[0],
                prices={
                    "Star City Games": PriceData(
                        vendor="Star City Games", price=10.0, condition="NM"
                    ),
                    "Card Kingdom": PriceData(
                        vendor="Card Kingdom", price=12.0, condition="LP"
                    ),
                },
                best_price=12.0,
                best_vendor="Card Kingdom",
            ),
            CardPrices(
                card=self.sample_cards[1],
                prices={
                    "Star City Games": PriceData(
                        vendor="Star City Games", price=25.0, condition="NM"
                    ),
                    "Card Kingdom": PriceData(
                        vendor="Card Kingdom", price=30.0, condition="LP"
                    ),
                },
                best_price=30.0,
                best_vendor="Card Kingdom",
            ),
            CardPrices(
                card=self.sample_cards[2],
                prices={
                    "Star City Games": PriceData(
                        vendor="Star City Games", price=5.0, condition="NM"
                    ),
                    "Card Kingdom": PriceData(
                        vendor="Card Kingdom", price=6.0, condition="LP"
                    ),
                },
                best_price=6.0,
                best_vendor="Card Kingdom",
            ),
        ]

        self.sample_summary = CollectionSummary(
            total_cards=3,
            cards_with_prices=3,
            cards_without_prices=0,
            best_total_value=48.0,
            best_vendor="Card Kingdom",
            average_price=16.0,
            price_range=(5.0, 30.0),
        )

    def test_analyze_collection(self):
        """Test comprehensive collection analysis."""
        # Mock price history
        self.mock_history.get_card_history.return_value = []

        analysis = self.analytics.analyze_collection(
            self.sample_prices, self.sample_summary
        )

        assert "collection_summary" in analysis
        assert "performance" in analysis
        assert "diversification" in analysis
        assert "risk_assessment" in analysis
        assert "top_performers" in analysis
        assert "underperformers" in analysis

    def test_calculate_diversification(self):
        """Test diversification calculation."""
        diversification = self.analytics._analyze_diversification(self.sample_prices)

        assert "diversification_level" in diversification
        assert "hhi_index" in diversification
        assert "set_distribution" in diversification

    def test_assess_risk(self):
        """Test risk assessment."""
        risk = self.analytics._assess_risk(self.sample_prices)

        assert "risk_categories" in risk
        assert "overall_risk_score" in risk
        assert "risk_level" in risk

    def test_generate_analytics_report(self):
        """Test analytics report generation."""
        analysis = {
            "collection_summary": self.sample_summary,
            "performance": {
                "overall_growth_rate": 5.2,
                "performance_level": "growing",
                "overall_growth_amount": 2.4,
            },
            "diversification": {
                "diversification_level": "good",
                "hhi_index": 0.25,
                "number_of_sets": 2,
                "set_distribution": {"Test Set 1": 2, "Test Set 2": 1},
                "recommendations": ["Diversify more"],
            },
            "risk_assessment": {
                "risk_level": "medium",
                "overall_risk_score": 0.45,
                "risk_categories": {
                    "low_risk": {
                        "percentage": 60.0,
                        "value": 28.8,
                        "count": 2,
                        "weighted_risk": 12.6,
                    },
                    "medium_risk": {
                        "percentage": 25.0,
                        "value": 12.0,
                        "count": 1,
                        "weighted_risk": 15.0,
                    },
                    "high_risk": {
                        "percentage": 15.0,
                        "value": 7.2,
                        "count": 0,
                        "weighted_risk": 0.0,
                    },
                },
                "recommendations": ["Reduce risk exposure"],
            },
            "top_performers": [],
            "underperformers": [],
        }

        report = self.analytics.generate_analytics_report(analysis)

        assert "COLLECTION ANALYTICS REPORT" in report
        assert "Total Cards: 3" in report
        assert "5.2%" in report  # Growth rate
        assert "Good" in report  # Diversification level
        assert "Medium" in report  # Risk level


class TestIntegration:
    """Integration tests for the analytics features."""

    def test_full_workflow(self):
        """Test the complete analytics workflow."""
        # This would test the full integration of all components
        # For now, we'll just verify the imports work
        from mtg_buylist_aggregator.hot_card_detector import HotCardDetector
        from mtg_buylist_aggregator.recommendation_engine import RecommendationEngine
        from mtg_buylist_aggregator.collection_analytics import CollectionAnalytics

        assert HotCardDetector is not None
        assert RecommendationEngine is not None
        assert CollectionAnalytics is not None


class TestCLIIntegration:
    def test_cli_analytics_command(self):
        result = subprocess.run(
            [sys.executable, "main.py", "analytics", "--use-mock"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "COLLECTION ANALYTICS REPORT" in result.stdout

    def test_cli_hot_cards_command(self):
        result = subprocess.run(
            [sys.executable, "main.py", "hot-cards", "--use-mock"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (
            "HOT CARDS ANALYSIS REPORT" in result.stdout
            or "No hot cards detected" in result.stdout
        )

    def test_cli_recommendations_command(self):
        result = subprocess.run(
            [sys.executable, "main.py", "recommendations", "--use-mock"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "STRATEGIC RECOMMENDATIONS REPORT" in result.stdout

    def test_cli_vendor_health_command(self):
        result = subprocess.run(
            [sys.executable, "main.py", "vendor-health", "--use-mock"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0 or result.returncode == 1
        assert "VENDOR SCRAPER HEALTH SUMMARY" in result.stdout
