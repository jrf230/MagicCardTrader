#!/usr/bin/env python3
"""Migration script to move CSV data to SQLite database."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.database import get_database
from mtg_buylist_aggregator.card_manager import CardManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_collection_data():
    """Migrate collection data from CSV to database."""
    logger.info("Starting migration from CSV to database...")
    
    # Initialize database
    db = get_database()
    
    # Load existing collection from CSV
    csv_manager = CardManager()
    cards = csv_manager.load_collection()
    
    if not cards:
        logger.info("No cards found in CSV collection")
        return
    
    logger.info(f"Found {len(cards)} cards in CSV collection")
    
    # Add cards to database
    success_count = 0
    for card in cards:
        try:
            if db.add_card(card):
                success_count += 1
                logger.debug(f"Migrated: {card.name} ({card.set_name})")
            else:
                logger.warning(f"Failed to migrate: {card.name} ({card.set_name})")
        except Exception as e:
            logger.error(f"Error migrating {card.name} ({card.set_name}): {e}")
    
    logger.info(f"Migration complete: {success_count}/{len(cards)} cards migrated successfully")
    
    # Verify migration
    db_cards = db.get_cards()
    logger.info(f"Database now contains {len(db_cards)} cards")
    
    # Get collection stats
    stats = db.get_collection_stats()
    logger.info(f"Collection stats: {stats}")


if __name__ == "__main__":
    migrate_collection_data() 