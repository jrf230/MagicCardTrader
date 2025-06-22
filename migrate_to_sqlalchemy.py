#!/usr/bin/env python3
"""
Migration script to move from old database to new SQLAlchemy system.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mtg_buylist_aggregator.database_sqlalchemy import get_database_manager, initialize_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main migration function."""
    logger.info("Starting migration to SQLAlchemy database system...")
    
    # Check if old database exists
    old_db_path = "mtg_trader.db"
    if not os.path.exists(old_db_path):
        logger.info("No existing database found. Creating new SQLAlchemy database...")
        initialize_database()
        logger.info("Migration complete - new database created.")
        return
    
    # Initialize new database manager
    db_manager = get_database_manager()
    
    try:
        # Create tables
        logger.info("Creating new database tables...")
        db_manager.create_tables()
        
        # Migrate data
        logger.info("Migrating data from old database...")
        db_manager.migrate_from_sqlite(old_db_path)
        
        # Verify migration
        health = db_manager.health_check()
        logger.info(f"Migration verification: {health}")
        
        # Backup old database
        backup_path = f"{old_db_path}.backup"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(old_db_path, backup_path)
        logger.info(f"Old database backed up to: {backup_path}")
        
        logger.info("Migration completed successfully!")
        logger.info("The new SQLAlchemy database is now active.")
        logger.info(f"Old database backed up to: {backup_path}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.error("Please check the error and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 