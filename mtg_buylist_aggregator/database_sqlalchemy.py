"""
SQLAlchemy-based database layer for MTG Buylist Aggregator.
Supports both SQLite and PostgreSQL with proper ORM models.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging
import os
from typing import Optional, List, Dict, Any, Generator
from contextlib import contextmanager

logger = logging.getLogger(__name__)

Base = declarative_base()

class Card(Base):
    """Card model for storing Magic card information."""
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    set_name = Column(String(255), nullable=False)
    foil = Column(Boolean, default=False)
    condition = Column(String(50), default='NM')
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prices = relationship("Price", back_populates="card", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Card(name='{self.name}', set='{self.set_name}', foil={self.foil})>"

class Vendor(Base):
    """Vendor model for storing vendor information."""
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    url = Column(String(500))
    is_active = Column(Boolean, default=True)
    last_scrape = Column(DateTime)
    success_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    prices = relationship("Price", back_populates="vendor")
    
    def __repr__(self):
        return f"<Vendor(name='{self.name}', active={self.is_active})>"

class Price(Base):
    """Price model for storing card prices from vendors."""
    __tablename__ = 'prices'
    
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.id'), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False, index=True)
    price = Column(Float, nullable=False)
    condition = Column(String(50), default='NM')
    is_foil = Column(Boolean, default=False)
    is_buy_price = Column(Boolean, default=True)  # True for buy, False for sell
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    card = relationship("Card", back_populates="prices")
    vendor = relationship("Vendor", back_populates="prices")
    
    def __repr__(self):
        return f"<Price(card_id={self.card_id}, vendor_id={self.vendor_id}, price={self.price})>"

class Cache(Base):
    """Cache model for storing API responses and computed data."""
    __tablename__ = 'cache'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(255), nullable=False, unique=True, index=True)
    data = Column(Text, nullable=False)  # JSON string
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Cache(key='{self.key}', expires_at={self.expires_at})>"

class Analytics(Base):
    """Analytics model for storing computed analytics data."""
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.id'), nullable=False, index=True)
    total_value = Column(Float, default=0.0)
    best_buy_price = Column(Float)
    best_buy_vendor = Column(String(255))
    price_spread = Column(Float)  # Difference between highest and lowest prices
    price_volatility = Column(Float)  # Standard deviation of prices
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    card = relationship("Card")
    
    def __repr__(self):
        return f"<Analytics(card_id={self.card_id}, total_value={self.total_value})>"

# Indexes for better performance
Index('idx_cards_name_set', Card.name, Card.set_name)
Index('idx_prices_card_vendor', Price.card_id, Price.vendor_id)
Index('idx_prices_timestamp', Price.timestamp)
Index('idx_cache_expires', Cache.expires_at)

class DatabaseManager:
    """Manages database connections and operations using SQLAlchemy."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager with connection URL."""
        self.database_url = database_url or self._get_default_url()
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _get_default_url(self) -> str:
        """Get default database URL based on environment."""
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')
        
        # Default to SQLite
        db_path = os.path.join(os.getcwd(), 'mtg_trader.db')
        return f"sqlite:///{db_path}"
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with appropriate configuration."""
        try:
            if self.database_url.startswith('sqlite'):
                # SQLite configuration
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False
                )
            else:
                # PostgreSQL configuration
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False
                )
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info(f"Database engine initialized: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            with self.get_session() as session:
                # Test basic queries
                card_count = session.query(Card).count()
                vendor_count = session.query(Vendor).count()
                price_count = session.query(Price).count()
                
                return {
                    'status': 'healthy',
                    'card_count': card_count,
                    'vendor_count': vendor_count,
                    'price_count': price_count,
                    'database_url': self.database_url
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_url': self.database_url
            }
    
    def migrate_from_sqlite(self, old_db_path: str):
        """Migrate data from old SQLite database to new SQLAlchemy structure."""
        try:
            import sqlite3
            from json import loads
            
            logger.info(f"Starting migration from {old_db_path}")
            
            # Connect to old database
            old_conn = sqlite3.connect(old_db_path)
            old_cursor = old_conn.cursor()
            
            with self.get_session() as session:
                # Migrate cards
                old_cursor.execute("SELECT name, set_name, foil, condition, quantity FROM cards")
                for row in old_cursor.fetchall():
                    card = Card(
                        name=row[0],
                        set_name=row[1],
                        foil=bool(row[2]),
                        condition=row[3],
                        quantity=row[4]
                    )
                    session.add(card)
                
                # Migrate vendors
                old_cursor.execute("SELECT name, url, is_active FROM vendors")
                for row in old_cursor.fetchall():
                    vendor = Vendor(
                        name=row[0],
                        url=row[1],
                        is_active=bool(row[2])
                    )
                    session.add(vendor)
                
                # Migrate price cache
                old_cursor.execute("SELECT card_name, vendor_name, price, condition, foil, timestamp FROM price_cache")
                for row in old_cursor.fetchall():
                    # Find or create card
                    card = session.query(Card).filter_by(name=row[0]).first()
                    if not card:
                        card = Card(name=row[0], set_name="Unknown")
                        session.add(card)
                    
                    # Find or create vendor
                    vendor = session.query(Vendor).filter_by(name=row[1]).first()
                    if not vendor:
                        vendor = Vendor(name=row[1])
                        session.add(vendor)
                    
                    # Create price entry
                    price = Price(
                        card_id=card.id,
                        vendor_id=vendor.id,
                        price=row[2],
                        condition=row[3],
                        is_foil=bool(row[4]),
                        timestamp=datetime.fromisoformat(row[5]) if row[5] else datetime.utcnow()
                    )
                    session.add(price)
                
                # Migrate dashboard cache
                old_cursor.execute("SELECT data, expires_at FROM dashboard_cache")
                for row in old_cursor.fetchall():
                    cache = Cache(
                        key='dashboard',
                        data=row[0],
                        expires_at=datetime.fromisoformat(row[1]) if row[1] else datetime.utcnow() + timedelta(hours=24)
                    )
                    session.add(cache)
                
                session.commit()
                logger.info("Migration completed successfully")
            
            old_conn.close()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def initialize_database():
    """Initialize the database with tables."""
    manager = get_database_manager()
    manager.create_tables()
    return manager 