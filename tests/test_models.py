"""Tests for data models."""

import pytest
from datetime import datetime

from mtg_buylist_aggregator.models import (
    Card, PriceData, CardPrices, CollectionSummary,
    Rarity, FoilTreatment, Condition, Language
)


class TestCard:
    """Test Card model."""
    
    def test_card_creation(self):
        """Test basic card creation."""
        card = Card(
            name="Sol Ring",
            set_name="Commander 2021",
            quantity=2
        )
        
        assert card.name == "Sol Ring"
        assert card.set_name == "Commander 2021"
        assert card.quantity == 2
        assert card.foil_treatment == FoilTreatment.NONFOIL
        assert card.condition == Condition.NM
        assert not card.is_foil()
    
    def test_foil_card(self):
        """Test foil card creation."""
        card = Card(
            name="Rhystic Study",
            set_name="Prophecy",
            quantity=1,
            foil_treatment=FoilTreatment.FOIL
        )
        
        assert card.is_foil()
        assert card.foil_treatment == FoilTreatment.FOIL
    
    def test_legacy_foil_support(self):
        """Test legacy foil field support."""
        card = Card(
            name="Test Card",
            set_name="Test Set",
            quantity=1,
            foil=True
        )
        
        assert card.is_foil()
        assert card.foil_treatment == FoilTreatment.FOIL
    
    def test_unique_key_generation(self):
        """Test unique key generation."""
        card1 = Card(
            name="Sol Ring",
            set_name="Commander 2021",
            quantity=1,
            set_code="C21"
        )
        
        card2 = Card(
            name="Sol Ring",
            set_name="Commander 2021",
            quantity=1,
            set_code="C21"
        )
        
        card3 = Card(
            name="Sol Ring",
            set_name="Commander 2021",
            quantity=1,
            set_code="C22"
        )
        
        assert card1.get_unique_key() == card2.get_unique_key()
        assert card1.get_unique_key() != card3.get_unique_key()
    
    def test_card_validation(self):
        """Test card validation."""
        # Test quantity validation
        with pytest.raises(ValueError):
            Card(
                name="Test Card",
                set_name="Test Set",
                quantity=0  # Should be >= 1
            )
        
        # Test valid card with all fields
        card = Card(
            name="Test Card",
            set_name="Test Set",
            quantity=1,
            rarity=Rarity.RARE,
            foil_treatment=FoilTreatment.FOIL,
            condition=Condition.LP,
            language=Language.JAPANESE
        )
        
        assert card.rarity == Rarity.RARE
        assert card.condition == Condition.LP
        assert card.language == Language.JAPANESE


class TestPriceData:
    """Test PriceData model."""
    
    def test_price_data_creation(self):
        """Test basic price data creation."""
        price_data = PriceData(
            vendor="Star City Games",
            price=15.50,
            condition="NM"
        )
        
        assert price_data.vendor == "Star City Games"
        assert price_data.price == 15.50
        assert price_data.condition == "NM"
        assert price_data.quantity_limit is None
    
    def test_price_data_with_optional_fields(self):
        """Test price data with optional fields."""
        now = datetime.now()
        price_data = PriceData(
            vendor="Card Kingdom",
            price=12.75,
            condition="LP",
            quantity_limit=10,
            last_price_update=now
        )
        
        assert price_data.quantity_limit == 10
        assert price_data.last_price_update == now
    
    def test_price_validation(self):
        """Test price validation."""
        with pytest.raises(ValueError):
            PriceData(
                vendor="Test Vendor",
                price=-5.0  # Should be >= 0
            )


class TestCardPrices:
    """Test CardPrices model."""
    
    def test_card_prices_creation(self):
        """Test basic card prices creation."""
        card = Card(name="Test Card", set_name="Test Set", quantity=1)
        card_prices = CardPrices(card=card)
        
        assert card_prices.card == card
        assert card_prices.prices == {}
        assert card_prices.best_vendor is None
        assert card_prices.best_price is None
    
    def test_update_best_price(self):
        """Test best price calculation."""
        card = Card(name="Test Card", set_name="Test Set", quantity=1)
        card_prices = CardPrices(card=card)
        
        # Add some prices
        card_prices.prices["Vendor A"] = PriceData(
            vendor="Vendor A",
            price=10.0,
            condition="NM"
        )
        card_prices.prices["Vendor B"] = PriceData(
            vendor="Vendor B",
            price=15.0,
            condition="NM"
        )
        card_prices.prices["Vendor C"] = PriceData(
            vendor="Vendor C",
            price=8.0,
            condition="NM"
        )
        
        card_prices.update_best_price()
        
        assert card_prices.best_vendor == "Vendor B"
        assert card_prices.best_price == 15.0
    
    def test_update_best_price_no_prices(self):
        """Test best price calculation with no prices."""
        card = Card(name="Test Card", set_name="Test Set", quantity=1)
        card_prices = CardPrices(card=card)
        
        card_prices.update_best_price()
        
        assert card_prices.best_vendor is None
        assert card_prices.best_price is None


class TestCollectionSummary:
    """Test CollectionSummary model."""
    
    def test_collection_summary_creation(self):
        """Test basic collection summary creation."""
        summary = CollectionSummary(
            total_cards=100,
            cards_with_prices=80,
            cards_without_prices=20
        )
        
        assert summary.total_cards == 100
        assert summary.cards_with_prices == 80
        assert summary.cards_without_prices == 20
        assert summary.total_value_by_vendor == {}
        assert summary.best_vendor is None
        assert summary.best_total_value is None
    
    def test_calculate_totals(self):
        """Test total calculation."""
        summary = CollectionSummary(
            total_cards=2,
            cards_with_prices=2,
            cards_without_prices=0
        )
        
        # Create test card prices
        card1 = Card(name="Card 1", set_name="Set 1", quantity=1)
        card2 = Card(name="Card 2", set_name="Set 2", quantity=2)
        
        card_prices1 = CardPrices(card=card1)
        card_prices1.prices["Vendor A"] = PriceData(vendor="Vendor A", price=10.0, condition="NM")
        card_prices1.prices["Vendor B"] = PriceData(vendor="Vendor B", price=12.0, condition="NM")
        
        card_prices2 = CardPrices(card=card2)
        card_prices2.prices["Vendor A"] = PriceData(vendor="Vendor A", price=5.0, condition="NM")
        card_prices2.prices["Vendor B"] = PriceData(vendor="Vendor B", price=4.0, condition="NM")
        
        card_prices_list = [card_prices1, card_prices2]
        summary.calculate_totals(card_prices_list)
        
        # Vendor A: 10 + (5 * 2) = 20
        # Vendor B: 12 + (4 * 2) = 20
        assert summary.total_value_by_vendor["Vendor A"] == 20.0
        assert summary.total_value_by_vendor["Vendor B"] == 20.0
        # Best vendor should be one of them (tie)
        assert summary.best_vendor in ["Vendor A", "Vendor B"]
        assert summary.best_total_value == 20.0


class TestEnums:
    """Test enum values."""
    
    def test_rarity_enum(self):
        """Test rarity enum values."""
        assert Rarity.COMMON.value == "Common"
        assert Rarity.RARE.value == "Rare"
        assert Rarity.MYTHIC.value == "Mythic Rare"
    
    def test_foil_treatment_enum(self):
        """Test foil treatment enum values."""
        assert FoilTreatment.NONFOIL.value == "Non-foil"
        assert FoilTreatment.FOIL.value == "Foil"
        assert FoilTreatment.ETCHED_FOIL.value == "Etched Foil"
    
    def test_condition_enum(self):
        """Test condition enum values."""
        assert Condition.NM.value == "Near Mint"
        assert Condition.LP.value == "Lightly Played"
        assert Condition.MP.value == "Moderately Played"
    
    def test_language_enum(self):
        """Test language enum values."""
        assert Language.ENGLISH.value == "English"
        assert Language.JAPANESE.value == "Japanese"
        assert Language.CHINESE_SIMPLIFIED.value == "Chinese Simplified" 