#!/usr/bin/env python3

import logging
from mtg_buylist_aggregator.models import Card
from mtg_buylist_aggregator.scrapers.cardkingdom import CardKingdomScraper
from mtg_buylist_aggregator.scrapers.scraper_manager import ScraperManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def test_card_kingdom():
    print("Testing Card Kingdom scraper...")
    card = Card(name='Cabal Ritual', set_name='Torment', quantity=1)
    scraper = CardKingdomScraper()
    
    try:
        prices = scraper.search_card(card)
        print(f"Found {len(prices)} prices for Cabal Ritual (Torment)")
        for price in prices:
            print(f"  {price.vendor}: ${price.price} ({price.price_type}) - {price.condition}")
    except Exception as e:
        print(f"Error: {e}")

def test_scraper_manager():
    print("\nTesting Scraper Manager...")
    card = Card(name='Cabal Ritual', set_name='Torment', quantity=1)
    manager = ScraperManager(use_mock=False, max_workers=1)
    
    try:
        card_prices = manager.get_card_prices(card)
        print(f"Found prices from {len(card_prices.prices)} vendors")
        
        for vendor, prices in card_prices.prices.items():
            print(f"  {vendor}: {len(prices)} prices")
            for price in prices:
                print(f"    ${price.price} ({price.price_type}) - {price.condition}")
        
        print(f"Best bid: {card_prices.best_bid.price if card_prices.best_bid else 'None'}")
        print(f"Best offer: {card_prices.best_offer.price if card_prices.best_offer else 'None'}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_card_kingdom()
    test_scraper_manager() 