#!/usr/bin/env python3
"""Test Star City Games comprehensive buylist scraper."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.starcitygames import StarCityGamesScraper
from mtg_buylist_aggregator.models import Card
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scg_comprehensive():
    """Test Star City Games comprehensive buylist scraper."""
    print("=== Testing Star City Games Comprehensive Buylist ===\n")
    
    scraper = StarCityGamesScraper()
    
    # Test cards that are commonly bought by vendors
    test_cards = [
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1),
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1),
        Card(name="Demonic Tutor", set_name="Revised Edition", quantity=1),
    ]
    
    for card in test_cards:
        print(f"Searching for {card.name} ({card.set_name})...")
        
        try:
            price_data = scraper.search_card(card)
            
            if price_data:
                print(f"✅ {card.name}: ${price_data.price:.2f}")
                print(f"   Price Type: {price_data.all_conditions.get('price_type', 'unknown')}")
                
                # Show comprehensive price breakdown
                usd_prices = price_data.all_conditions.get('usd_prices', {})
                credit_prices = price_data.all_conditions.get('credit_prices', {})
                all_prices = price_data.all_conditions.get('all_prices', {})
                
                if usd_prices:
                    print(f"   USD Prices: {usd_prices}")
                if credit_prices:
                    print(f"   Credit Prices: {credit_prices}")
                if all_prices:
                    print(f"   All Prices: {all_prices}")
                
                # Show specific condition prices if available
                if 'NM' in usd_prices:
                    print(f"   NM: ${usd_prices['NM']:.2f}")
                if 'PL' in usd_prices:
                    print(f"   PL: ${usd_prices['PL']:.2f}")
                if 'HP' in usd_prices:
                    print(f"   HP: ${usd_prices['HP']:.2f}")
                
                print(f"   Search URL: {price_data.all_conditions.get('search_url', 'N/A')}")
            else:
                print(f"❌ {card.name}: No buylist price found")
            
            print()
            
        except Exception as e:
            print(f"❌ {card.name}: Error - {e}")
            print()
    
    print("=== Comprehensive Buylist Test Complete ===")

if __name__ == "__main__":
    test_scg_comprehensive() 