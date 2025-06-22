"""Database management for MTG Trader Pro."""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from contextlib import contextmanager
import threading

from .models import Card, CardPrices, PriceData

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database manager for all MTG Trader data."""

    def __init__(self, db_path: str = "mtg_trader.db"):
        """Initialize database manager."""
        self.db_path = Path(db_path)
        self._lock = threading.RLock()
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def _init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Cards table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    set_name TEXT NOT NULL,
                    set_code TEXT,
                    scryfall_id TEXT,
                    card_number TEXT,
                    rarity TEXT,
                    quantity INTEGER DEFAULT 1,
                    foil_treatment TEXT DEFAULT 'Non-foil',
                    condition TEXT DEFAULT 'Near Mint',
                    promo_type TEXT DEFAULT 'Regular',
                    artwork_variant TEXT DEFAULT 'Normal',
                    border_treatment TEXT DEFAULT 'Normal',
                    card_size TEXT DEFAULT 'Normal',
                    language TEXT DEFAULT 'English',
                    edition TEXT,
                    signed BOOLEAN DEFAULT 0,
                    original_printing BOOLEAN DEFAULT 1,
                    stamp TEXT,
                    serialized_number TEXT,
                    is_token BOOLEAN DEFAULT 0,
                    is_emblem BOOLEAN DEFAULT 0,
                    is_other BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, set_name, foil_treatment, condition)
                )
            """
            )

            # Price cache table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS price_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER NOT NULL,
                    vendor TEXT NOT NULL,
                    price REAL NOT NULL,
                    price_type TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    quantity_limit INTEGER,
                    last_price_update TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (card_id) REFERENCES cards (id),
                    UNIQUE(card_id, vendor, price_type, condition)
                )
            """
            )

            # Price history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER NOT NULL,
                    vendor TEXT NOT NULL,
                    price REAL NOT NULL,
                    price_type TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (card_id) REFERENCES cards (id)
                )
            """
            )

            # Dashboard cache table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboard_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """
            )

            # Analytics cache table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    UNIQUE(analysis_type)
                )
            """
            )

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cards_set ON cards(set_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_price_cache_card ON price_cache(card_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_price_cache_vendor ON price_cache(vendor)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_price_history_card ON price_history(card_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(recorded_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_dashboard_cache_expires ON dashboard_cache(expires_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires ON analytics_cache(expires_at)"
            )

            conn.commit()
            logger.info("Database initialized successfully")

    # Card Management Methods
    def add_card(self, card: Card) -> bool:
        """Add or update a card in the database."""
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check if card exists
                cursor.execute(
                    """
                    SELECT id, quantity FROM cards 
                    WHERE name = ? AND set_name = ? AND foil_treatment = ? AND condition = ?
                """,
                    (
                        card.name,
                        card.set_name,
                        card.foil_treatment.value,
                        card.condition.value,
                    ),
                )

                existing = cursor.fetchone()

                if existing:
                    # Update quantity
                    new_quantity = existing["quantity"] + card.quantity
                    cursor.execute(
                        """
                        UPDATE cards SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """,
                        (new_quantity, existing["id"]),
                    )
                    logger.info(
                        f"Updated quantity for {card.name} ({card.set_name}) to {new_quantity}"
                    )
                else:
                    # Insert new card
                    cursor.execute(
                        """
                        INSERT INTO cards (
                            name, set_name, set_code, scryfall_id, card_number, rarity,
                            quantity, foil_treatment, condition, promo_type, artwork_variant,
                            border_treatment, card_size, language, edition, signed,
                            original_printing, stamp, serialized_number, is_token, is_emblem, is_other
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            card.name,
                            card.set_name,
                            card.set_code,
                            card.scryfall_id,
                            card.card_number,
                            card.rarity.value if card.rarity else None,
                            card.quantity,
                            card.foil_treatment.value,
                            card.condition.value,
                            card.promo_type.value,
                            card.artwork_variant.value,
                            card.border_treatment.value,
                            card.card_size.value,
                            card.language.value,
                            card.edition.value if card.edition else None,
                            card.signed,
                            card.original_printing,
                            card.stamp,
                            card.serialized_number,
                            card.is_token,
                            card.is_emblem,
                            card.is_other,
                        ),
                    )
                    logger.info(
                        f"Added {card.quantity}x {card.name} ({card.set_name}) to database"
                    )

                conn.commit()
                return True

    def get_cards(self, limit: Optional[int] = None) -> List[Card]:
        """Get all cards from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM cards ORDER BY name, set_name"
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            rows = cursor.fetchall()

            cards = []
            for row in rows:
                card = Card(
                    name=row["name"],
                    set_name=row["set_name"],
                    set_code=row["set_code"],
                    scryfall_id=row["scryfall_id"],
                    card_number=row["card_number"],
                    rarity=row["rarity"],
                    quantity=row["quantity"],
                    foil_treatment=row["foil_treatment"],
                    condition=row["condition"],
                    promo_type=row["promo_type"],
                    artwork_variant=row["artwork_variant"],
                    border_treatment=row["border_treatment"],
                    card_size=row["card_size"],
                    language=row["language"],
                    edition=row["edition"],
                    signed=bool(row["signed"]),
                    original_printing=bool(row["original_printing"]),
                    stamp=row["stamp"],
                    serialized_number=row["serialized_number"],
                    is_token=bool(row["is_token"]),
                    is_emblem=bool(row["is_emblem"]),
                    is_other=bool(row["is_other"]),
                )
                cards.append(card)

            return cards

    def remove_card(
        self,
        name: str,
        set_name: str,
        foil: bool = False,
        quantity: Optional[int] = None,
    ) -> bool:
        """Remove a card from the database."""
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                foil_treatment = "Foil" if foil else "Non-foil"

                if quantity is None:
                    # Remove entire card
                    cursor.execute(
                        """
                        DELETE FROM cards 
                        WHERE name = ? AND set_name = ? AND foil_treatment = ?
                    """,
                        (name, set_name, foil_treatment),
                    )
                else:
                    # Update quantity
                    cursor.execute(
                        """
                        UPDATE cards SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP
                        WHERE name = ? AND set_name = ? AND foil_treatment = ? AND quantity >= ?
                    """,
                        (quantity, name, set_name, foil_treatment, quantity),
                    )

                conn.commit()
                return cursor.rowcount > 0

    # Price Cache Methods with 24-hour rule
    def get_price_cache(
        self, cards: List[Card], force_refresh: bool = False
    ) -> List[CardPrices]:
        """Get cached prices for cards. Respects 24-hour cache rule unless force_refresh=True."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            card_prices_list = []

            for card in cards:
                # Check if we have fresh cache data (less than 24 hours old)
                if not force_refresh:
                    cursor.execute(
                        """
                        SELECT pc.* FROM price_cache pc
                        JOIN cards c ON pc.card_id = c.id
                        WHERE c.name = ? AND c.set_name = ? AND c.foil_treatment = ?
                        AND pc.last_price_update > datetime('now', '-24 hours')
                    """,
                        (card.name, card.set_name, card.foil_treatment.value),
                    )
                else:
                    # Force refresh: get any cached data regardless of age
                    cursor.execute(
                        """
                        SELECT pc.* FROM price_cache pc
                        JOIN cards c ON pc.card_id = c.id
                        WHERE c.name = ? AND c.set_name = ? AND c.foil_treatment = ?
                    """,
                        (card.name, card.set_name, card.foil_treatment.value),
                    )

                price_rows = cursor.fetchall()

                if price_rows:
                    # Reconstruct CardPrices object
                    prices = {}
                    for row in price_rows:
                        vendor = row["vendor"]
                        if vendor not in prices:
                            prices[vendor] = []

                        price_data = PriceData(
                            price=row["price"],
                            price_type=row["price_type"],
                            vendor=vendor,
                            condition=row["condition"],
                            quantity_limit=row["quantity_limit"],
                            last_price_update=(
                                datetime.fromisoformat(row["last_price_update"])
                                if row["last_price_update"]
                                else None
                            ),
                            notes=row["notes"],
                        )
                        prices[vendor].append(price_data)

                    card_prices = CardPrices(card=card)
                    card_prices.prices = prices
                    card_prices.update_best_prices()
                    card_prices_list.append(card_prices)
                else:
                    # No cached data, create empty CardPrices
                    card_prices_list.append(CardPrices(card=card))

            return card_prices_list

    def update_price_cache(self, card_prices_list: List[CardPrices]) -> None:
        """Update price cache for multiple cards."""
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                for card_prices in card_prices_list:
                    # Get card ID
                    cursor.execute(
                        """
                        SELECT id FROM cards 
                        WHERE name = ? AND set_name = ? AND foil_treatment = ?
                    """,
                        (
                            card_prices.card.name,
                            card_prices.card.set_name,
                            card_prices.card.foil_treatment.value,
                        ),
                    )

                    card_row = cursor.fetchone()
                    if not card_row:
                        continue

                    card_id = card_row["id"]

                    # Clear existing prices for this card
                    cursor.execute(
                        "DELETE FROM price_cache WHERE card_id = ?", (card_id,)
                    )

                    # Insert new prices
                    for vendor, price_data_list in card_prices.prices.items():
                        for price_data in price_data_list:
                            cursor.execute(
                                """
                                INSERT INTO price_cache (
                                    card_id, vendor, price, price_type, condition,
                                    quantity_limit, last_price_update, notes
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    card_id,
                                    vendor,
                                    price_data.price,
                                    price_data.price_type,
                                    price_data.condition,
                                    price_data.quantity_limit,
                                    (
                                        price_data.last_price_update.isoformat()
                                        if price_data.last_price_update
                                        else None
                                    ),
                                    price_data.notes,
                                ),
                            )

                conn.commit()
                logger.info(f"Updated price cache for {len(card_prices_list)} cards")

    def get_cache_status(self) -> Dict:
        """Get detailed cache status information."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get total cards
            cursor.execute("SELECT COUNT(*) as total_cards FROM cards")
            total_cards = cursor.fetchone()["total_cards"]

            # Get cached cards count
            cursor.execute(
                "SELECT COUNT(DISTINCT card_id) as cached_cards FROM price_cache"
            )
            cached_cards = cursor.fetchone()["cached_cards"]

            # Get fresh cache count (less than 24 hours)
            cursor.execute(
                """
                SELECT COUNT(DISTINCT card_id) as fresh_cache 
                FROM price_cache 
                WHERE last_price_update > datetime('now', '-24 hours')
            """
            )
            fresh_cache = cursor.fetchone()["fresh_cache"]

            # Get stale cache count
            stale_cache = cached_cards - fresh_cache

            # Get last update time
            cursor.execute(
                """
                SELECT MAX(last_price_update) as last_update 
                FROM price_cache
            """
            )
            last_update_row = cursor.fetchone()
            last_update = (
                last_update_row["last_update"]
                if last_update_row["last_update"]
                else None
            )

            return {
                "total_cards": total_cards,
                "cached_cards": cached_cards,
                "fresh_cache": fresh_cache,
                "stale_cache": stale_cache,
                "last_update": last_update,
                "cache_coverage": (
                    (cached_cards / total_cards * 100) if total_cards > 0 else 0
                ),
            }

    # Dashboard Cache Methods
    def get_dashboard_cache(self, cache_key: str = "main") -> Optional[Dict]:
        """Get cached dashboard data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT data FROM dashboard_cache 
                WHERE cache_key = ? AND expires_at > datetime('now')
            """,
                (cache_key,),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row["data"])
            return None

    def set_dashboard_cache(
        self, data: Dict, cache_key: str = "main", ttl_hours: int = 24
    ) -> None:
        """Set dashboard cache data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            expires_at = datetime.now() + timedelta(hours=ttl_hours)

            cursor.execute(
                """
                INSERT OR REPLACE INTO dashboard_cache (cache_key, data, expires_at)
                VALUES (?, ?, ?)
            """,
                (cache_key, json.dumps(data), expires_at.isoformat()),
            )

            conn.commit()

    def clear_dashboard_cache(self, cache_key: str = "main") -> None:
        """Clear dashboard cache."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM dashboard_cache WHERE cache_key = ?", (cache_key,)
            )
            conn.commit()

    # Analytics Cache Methods
    def get_analytics_cache(self, analysis_type: str) -> Optional[Dict]:
        """Get cached analytics data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT data FROM analytics_cache 
                WHERE analysis_type = ? AND expires_at > datetime('now')
            """,
                (analysis_type,),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row["data"])
            return None

    def set_analytics_cache(
        self, analysis_type: str, data: Dict, ttl_hours: int = 6
    ) -> None:
        """Set analytics cache data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            expires_at = datetime.now() + timedelta(hours=ttl_hours)

            cursor.execute(
                """
                INSERT OR REPLACE INTO analytics_cache (analysis_type, data, expires_at)
                VALUES (?, ?, ?)
            """,
                (analysis_type, json.dumps(data), expires_at.isoformat()),
            )

            conn.commit()

    # Utility Methods
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) as total_cards, SUM(quantity) as total_quantity FROM cards"
            )
            stats = cursor.fetchone()

            cursor.execute("SELECT COUNT(DISTINCT set_name) as unique_sets FROM cards")
            sets = cursor.fetchone()

            cursor.execute(
                "SELECT COUNT(*) as foils FROM cards WHERE foil_treatment = 'Foil'"
            )
            foils = cursor.fetchone()

            return {
                "total_cards": stats["total_cards"],
                "total_quantity": stats["total_quantity"],
                "unique_sets": sets["unique_sets"],
                "foil_cards": foils["foils"],
            }

    def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Clean up old price history and expired cache data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Clean up old price history
            cursor.execute(
                """
                DELETE FROM price_history 
                WHERE recorded_at < datetime('now', '-{} days')
            """.format(
                    days_to_keep
                )
            )

            # Clean up expired cache data
            cursor.execute(
                "DELETE FROM dashboard_cache WHERE expires_at < datetime('now')"
            )
            cursor.execute(
                "DELETE FROM analytics_cache WHERE expires_at < datetime('now')"
            )

            conn.commit()
            logger.info("Cleaned up old data")


# Global database instance
_db_instance = None
_db_lock = threading.Lock()


def get_database() -> DatabaseManager:
    """Get the global database instance."""
    global _db_instance
    with _db_lock:
        if _db_instance is None:
            _db_instance = DatabaseManager()
        return _db_instance
