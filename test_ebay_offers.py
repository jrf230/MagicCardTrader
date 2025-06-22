#!/usr/bin/env python3
"""Test eBay scraper for offer prices and recent sales."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.ebay import EbayScraper
from mtg_buylist_aggregator.models import Card
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ebay_offers():
    """Test eBay scraper for offer prices and recent sales."""
    print("=== Testing eBay Offer Prices and Recent Sales ===\n")
    
    scraper = EbayScraper()
    
    # Test cards
    test_cards = [
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1),
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1),
        Card(name="Lightning Bolt", set_name="Revised Edition", quantity=1),
    ]
    
    for card in test_cards:
        print(f"Searching for {card.name} ({card.set_name})...")
        
        try:
            # Get offer prices
            offer_data = scraper.search_card(card)
            
            if offer_data:
                print(f"✅ {card.name}: ${offer_data.price:.2f}")
                print(f"   Vendor: {offer_data.vendor}")
                print(f"   Condition: {offer_data.condition}")
                
                # Show offer price details
                buy_it_now = offer_data.all_conditions.get('buy_it_now_price')
                best_offer = offer_data.all_conditions.get('best_offer_price')
                recent_sales_avg = offer_data.all_conditions.get('recent_sales_avg')
                lowest_offer = offer_data.all_conditions.get('Lowest_Offer')
                highest_offer = offer_data.all_conditions.get('Highest_Offer')
                avg_offer = offer_data.all_conditions.get('Avg_Offer')
                
                if buy_it_now:
                    print(f"   Buy It Now: ${buy_it_now:.2f}")
                if best_offer:
                    print(f"   Best Offer: ${best_offer:.2f}")
                if recent_sales_avg:
                    print(f"   Recent Sales Avg: ${recent_sales_avg:.2f}")
                if lowest_offer:
                    print(f"   Lowest Offer: ${lowest_offer:.2f}")
                if highest_offer:
                    print(f"   Highest Offer: ${highest_offer:.2f}")
                if avg_offer:
                    print(f"   Average Offer: ${avg_offer:.2f}")
                
                # Show note
                note = offer_data.all_conditions.get('note', '')
                if note:
                    print(f"   Note: {note}")
                
                # Show data source
                data_source = offer_data.all_conditions.get('data_source', 'scraped')
                print(f"   Data Source: {data_source}")
                
            else:
                print(f"❌ {card.name}: No offer prices found")
            
            print()
            
        except Exception as e:
            print(f"❌ {card.name}: Error - {e}")
            print()
    
    print("=== eBay Test Complete ===")

if __name__ == "__main__":
    test_ebay_offers() 