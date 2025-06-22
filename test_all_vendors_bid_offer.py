#!/usr/bin/env python3
"""Test all vendors for bid/offer prices."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.mtgstocks import MTGStocksScraper
from mtg_buylist_aggregator.scrapers.cardkingdom import CardKingdomScraper
from mtg_buylist_aggregator.scrapers.starcitygames import StarCityGamesScraper
from mtg_buylist_aggregator.scrapers.tcgplayer import TCGPlayerScraper
from mtg_buylist_aggregator.models import Card
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_vendors_bid_offer():
    """Test all vendors for bid/offer prices."""
    print("=== Testing All Vendors for Bid/Offer Prices ===\n")
    
    # Initialize scrapers
    scrapers = {
        "MTGStocks": MTGStocksScraper(),
        "Card Kingdom": CardKingdomScraper(),
        "Star City Games": StarCityGamesScraper(),
        "TCG Player": TCGPlayerScraper(),
    }
    
    # Test card
    test_card = Card(name="Rhystic Study", set_name="Prophecy", quantity=1)
    
    print(f"Testing card: {test_card.name} ({test_card.set_name})\n")
    
    for vendor_name, scraper in scrapers.items():
        print(f"--- {vendor_name} ---")
        
        try:
            if vendor_name == "MTGStocks":
                # MTGStocks shows bid/offer format
                price_data = scraper.search_card(test_card)
                
                if price_data:
                    print(f"✅ {vendor_name}: ${price_data.price:.2f}")
                    print(f"   Condition: {price_data.condition}")
                    
                    # Show bid/offer breakdown
                    bid_price = price_data.all_conditions.get('bid_price')
                    offer_price = price_data.all_conditions.get('offer_price')
                    market_price = price_data.all_conditions.get('market_price')
                    
                    if bid_price:
                        print(f"   Bid Price: ${bid_price:.2f}")
                    if offer_price:
                        print(f"   Offer Price: ${offer_price:.2f}")
                    if market_price:
                        print(f"   Market Price: ${market_price:.2f}")
                    
                    # Show additional data
                    data_source = price_data.all_conditions.get('data_source', 'scraped')
                    print(f"   Data Source: {data_source}")
                    
                else:
                    print(f"❌ {vendor_name}: No bid/offer prices found")
            
            elif vendor_name == "TCG Player":
                # TCG Player shows offer-only format (no bid prices)
                price_data = scraper.search_card(test_card)
                
                if price_data:
                    print(f"✅ {vendor_name}: ${price_data.price:.2f}")
                    print(f"   Condition: {price_data.condition}")
                    
                    # Show offer price details
                    offer_price = price_data.all_conditions.get('offer_price')
                    market_price = price_data.all_conditions.get('market_price')
                    lowest_offer = price_data.all_conditions.get('Lowest_Offer')
                    highest_offer = price_data.all_conditions.get('Highest_Offer')
                    offer_count = price_data.all_conditions.get('Offer_Count')
                    
                    if offer_price:
                        print(f"   Offer Price: ${offer_price:.2f}")
                    if market_price:
                        print(f"   Market Price: ${market_price:.2f}")
                    if lowest_offer:
                        print(f"   Lowest Offer: ${lowest_offer:.2f}")
                    if highest_offer:
                        print(f"   Highest Offer: ${highest_offer:.2f}")
                    if offer_count:
                        print(f"   Offer Count: {offer_count}")
                    
                    # Show note about no bid prices
                    note = price_data.all_conditions.get('note', '')
                    if note:
                        print(f"   Note: {note}")
                    
                    # Show additional data
                    data_source = price_data.all_conditions.get('data_source', 'scraped')
                    print(f"   Data Source: {data_source}")
                    
                else:
                    print(f"❌ {vendor_name}: No offer prices found")
            
            else:
                # Card Kingdom and Star City Games show cash/credit format
                if hasattr(scraper, 'search_card_with_credit'):
                    price_data = scraper.search_card_with_credit(test_card)
                    cash_data = price_data.get("cash")
                    credit_data = price_data.get("credit")
                else:
                    # Fallback to regular search
                    cash_data = scraper.search_card(test_card)
                    credit_data = None
                
                if cash_data:
                    print(f"✅ {vendor_name}: ${cash_data.price:.2f}")
                    print(f"   Condition: {cash_data.condition}")
                    print(f"   Data Source: {cash_data.all_conditions.get('data_source', 'scraped')}")
                    
                    # Show credit price if available
                    if credit_data:
                        print(f"✅ {vendor_name} (Credit): ${credit_data.price:.2f}")
                        print(f"   Condition: {credit_data.condition}")
                        print(f"   Credit Multiplier: {credit_data.all_conditions.get('credit_multiplier', 'N/A')}")
                    elif cash_data.all_conditions.get('credit_price'):
                        credit_price = cash_data.all_conditions['credit_price']
                        print(f"✅ {vendor_name} (Credit): ${credit_price:.2f}")
                        print(f"   Credit Multiplier: {cash_data.all_conditions.get('credit_multiplier', 'N/A')}")
                    else:
                        print(f"❌ {vendor_name} (Credit): No credit price available")
                    
                else:
                    print(f"❌ {vendor_name}: No price data found")
                    print(f"❌ {vendor_name} (Credit): No price data found")
            
            print()
            
        except Exception as e:
            print(f"❌ {vendor_name}: Error - {e}")
            print()
    
    print("=== All Vendors Test Complete ===")

if __name__ == "__main__":
    test_all_vendors_bid_offer() 