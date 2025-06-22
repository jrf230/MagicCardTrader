"""
Tests for SQLAlchemy database layer.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from mtg_buylist_aggregator.database_sqlalchemy import (
    DatabaseManager, Card, Vendor, Price, Cache, Analytics, Base
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield f"sqlite:///{db_path}"
    
    # Cleanup
    os.unlink(db_path)


class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest.fixture
    def db_manager(self, temp_db):
        """Create a database manager with temporary database."""
        return DatabaseManager(temp_db)
    
    def test_database_initialization(self, db_manager):
        """Test database initialization."""
        assert db_manager.engine is not None
        assert db_manager.SessionLocal is not None
    
    def test_create_tables(self, db_manager):
        """Test table creation."""
        db_manager.create_tables()
        
        # Verify tables exist
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['cards', 'vendors', 'prices', 'cache', 'analytics']
        for table in expected_tables:
            assert table in tables
    
    def test_session_context_manager(self, db_manager):
        """Test session context manager."""
        db_manager.create_tables()
        
        with db_manager.get_session() as session:
            # Create a test card
            card = Card(name="Test Card", set_name="Test Set")
            session.add(card)
            session.flush()  # Get the ID
            
            # Verify card was added
            assert card.id is not None
            assert card.name == "Test Card"
    
    def test_health_check(self, db_manager):
        """Test database health check."""
        db_manager.create_tables()
        
        health = db_manager.health_check()
        assert health['status'] == 'healthy'
        assert 'card_count' in health
        assert 'vendor_count' in health
        assert 'price_count' in health


class TestCardModel:
    """Test Card model functionality."""
    
    @pytest.fixture
    def session(self, temp_db):
        """Create a database session."""
        db_manager = DatabaseManager(temp_db)
        db_manager.create_tables()
        
        with db_manager.get_session() as session:
            yield session
    
    def test_create_card(self, session):
        """Test creating a card."""
        card = Card(
            name="Lightning Bolt",
            set_name="Alpha",
            foil=False,
            condition="NM",
            quantity=4
        )
        session.add(card)
        session.flush()
        
        assert card.id is not None
        assert card.name == "Lightning Bolt"
        assert card.set_name == "Alpha"
        assert card.foil is False
        assert card.condition == "NM"
        assert card.quantity == 4
        assert card.created_at is not None
    
    def test_card_relationships(self, session):
        """Test card relationships with prices."""
        # Create card and vendor
        card = Card(name="Test Card", set_name="Test Set")
        vendor = Vendor(name="Test Vendor")
        session.add_all([card, vendor])
        session.flush()
        
        # Create price
        price = Price(
            card_id=card.id,
            vendor_id=vendor.id,
            price=10.50,
            condition="NM",
            is_foil=False
        )
        session.add(price)
        session.flush()
        
        # Test relationships
        assert len(card.prices) == 1
        assert card.prices[0].price == 10.50
        assert card.prices[0].vendor.name == "Test Vendor"


class TestVendorModel:
    """Test Vendor model functionality."""
    
    @pytest.fixture
    def session(self, temp_db):
        """Create a database session."""
        db_manager = DatabaseManager(temp_db)
        db_manager.create_tables()
        
        with db_manager.get_session() as session:
            yield session
    
    def test_create_vendor(self, session):
        """Test creating a vendor."""
        vendor = Vendor(
            name="Card Kingdom",
            url="https://www.cardkingdom.com",
            is_active=True
        )
        session.add(vendor)
        session.flush()
        
        assert vendor.id is not None
        assert vendor.name == "Card Kingdom"
        assert vendor.url == "https://www.cardkingdom.com"
        assert vendor.is_active is True
        assert vendor.success_rate == 0.0
    
    def test_vendor_uniqueness(self, session):
        """Test vendor name uniqueness."""
        vendor1 = Vendor(name="Test Vendor")
        vendor2 = Vendor(name="Test Vendor")  # Same name
        
        session.add(vendor1)
        session.flush()
        
        session.add(vendor2)
        with pytest.raises(Exception):  # Should raise integrity error
            session.flush()


class TestPriceModel:
    """Test Price model functionality."""
    
    @pytest.fixture
    def session(self, temp_db):
        """Create a database session."""
        db_manager = DatabaseManager(temp_db)
        db_manager.create_tables()
        
        with db_manager.get_session() as session:
            yield session
    
    def test_create_price(self, session):
        """Test creating a price."""
        # Create card and vendor first
        card = Card(name="Test Card", set_name="Test Set")
        vendor = Vendor(name="Test Vendor")
        session.add_all([card, vendor])
        session.flush()
        
        price = Price(
            card_id=card.id,
            vendor_id=vendor.id,
            price=15.75,
            condition="LP",
            is_foil=True,
            is_buy_price=True
        )
        session.add(price)
        session.flush()
        
        assert price.id is not None
        assert price.price == 15.75
        assert price.condition == "LP"
        assert price.is_foil is True
        assert price.is_buy_price is True
        assert price.timestamp is not None


class TestCacheModel:
    """Test Cache model functionality."""
    
    @pytest.fixture
    def session(self, temp_db):
        """Create a database session."""
        db_manager = DatabaseManager(temp_db)
        db_manager.create_tables()
        
        with db_manager.get_session() as session:
            yield session
    
    def test_create_cache(self, session):
        """Test creating a cache entry."""
        cache = Cache(
            key="test_key",
            data='{"test": "data"}',
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        session.add(cache)
        session.flush()
        
        assert cache.id is not None
        assert cache.key == "test_key"
        assert cache.data == '{"test": "data"}'
        assert cache.expires_at > datetime.now(timezone.utc)
    
    def test_cache_uniqueness(self, session):
        """Test cache key uniqueness."""
        cache1 = Cache(
            key="test_key",
            data="data1",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        cache2 = Cache(
            key="test_key",  # Same key
            data="data2",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        session.add(cache1)
        session.flush()
        
        session.add(cache2)
        with pytest.raises(Exception):  # Should raise integrity error
            session.flush()


class TestAnalyticsModel:
    """Test Analytics model functionality."""
    
    @pytest.fixture
    def session(self, temp_db):
        """Create a database session."""
        db_manager = DatabaseManager(temp_db)
        db_manager.create_tables()
        
        with db_manager.get_session() as session:
            yield session
    
    def test_create_analytics(self, session):
        """Test creating analytics entry."""
        card = Card(name="Test Card", set_name="Test Set")
        session.add(card)
        session.flush()
        
        analytics = Analytics(
            card_id=card.id,
            total_value=100.50,
            best_buy_price=10.25,
            best_buy_vendor="Test Vendor",
            price_spread=5.00,
            price_volatility=2.50
        )
        session.add(analytics)
        session.flush()
        
        assert analytics.id is not None
        assert analytics.total_value == 100.50
        assert analytics.best_buy_price == 10.25
        assert analytics.best_buy_vendor == "Test Vendor"
        assert analytics.price_spread == 5.00
        assert analytics.price_volatility == 2.50


class TestDatabaseMigration:
    """Test database migration functionality."""
    
    @pytest.fixture
    def old_db_path(self):
        """Create a temporary old database for migration testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create old database structure
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create old tables
        cursor.execute("""
            CREATE TABLE cards (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                set_name TEXT NOT NULL,
                foil BOOLEAN DEFAULT FALSE,
                condition TEXT DEFAULT 'NM',
                quantity INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE vendors (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                url TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE price_cache (
                id INTEGER PRIMARY KEY,
                card_name TEXT NOT NULL,
                vendor_name TEXT NOT NULL,
                price REAL NOT NULL,
                condition TEXT DEFAULT 'NM',
                foil BOOLEAN DEFAULT FALSE,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE dashboard_cache (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                expires_at TEXT
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO cards (name, set_name, foil, condition, quantity) VALUES (?, ?, ?, ?, ?)",
                      ("Test Card", "Test Set", False, "NM", 4))
        
        cursor.execute("INSERT INTO vendors (name, url, is_active) VALUES (?, ?, ?)",
                      ("Test Vendor", "https://test.com", True))
        
        cursor.execute("INSERT INTO price_cache (card_name, vendor_name, price, condition, foil, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                      ("Test Card", "Test Vendor", 10.50, "NM", False, datetime.now(timezone.utc).isoformat()))
        
        cursor.execute("INSERT INTO dashboard_cache (data, expires_at) VALUES (?, ?)",
                      ('{"test": "data"}', (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()))
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    def test_migration_from_sqlite(self, old_db_path, temp_db):
        """Test migration from old SQLite database."""
        db_manager = DatabaseManager(temp_db)
        db_manager.create_tables()
        
        # Perform migration
        db_manager.migrate_from_sqlite(old_db_path)
        
        # Verify migration
        with db_manager.get_session() as session:
            # Check cards
            cards = session.query(Card).all()
            assert len(cards) == 1
            assert cards[0].name == "Test Card"
            assert cards[0].set_name == "Test Set"
            
            # Check vendors
            vendors = session.query(Vendor).all()
            assert len(vendors) == 1
            assert vendors[0].name == "Test Vendor"
            
            # Check prices
            prices = session.query(Price).all()
            assert len(prices) == 1
            assert prices[0].price == 10.50
            
            # Check cache
            cache_entries = session.query(Cache).all()
            assert len(cache_entries) == 1
            assert cache_entries[0].key == "dashboard"


if __name__ == "__main__":
    pytest.main([__file__]) 