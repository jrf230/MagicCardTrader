"""Scraper manager for coordinating multiple MTG buylist scrapers."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import os
import importlib
import pkgutil
from pathlib import Path

from mtg_buylist_aggregator.scrapers.base_scraper import BaseScraper
from mtg_buylist_aggregator.scrapers.starcitygames import StarCityGamesScraper
from mtg_buylist_aggregator.scrapers.cardkingdom import CardKingdomScraper
from mtg_buylist_aggregator.scrapers.beatthebuylist import BeatTheBuylistScraper
from mtg_buylist_aggregator.scrapers.ebay import EbayScraper
from mtg_buylist_aggregator.scrapers.tcgplayer import TCGPlayerScraper
from mtg_buylist_aggregator.scrapers.channelfireball import ChannelFireballScraper
from mtg_buylist_aggregator.scrapers.coolstuffinc import CoolStuffIncScraper
from mtg_buylist_aggregator.scrapers.scryfall import ScryfallScraper
from mtg_buylist_aggregator.scrapers.cardmarket import CardmarketScraper
from mtg_buylist_aggregator.scrapers.mtggoldfish import MTGGoldfishScraper
from mtg_buylist_aggregator.scrapers.mtgstocks import MTGStocksScraper
from mtg_buylist_aggregator.scrapers.magiccardprices import MagicCardPricesScraper
from mtg_buylist_aggregator.scrapers.cardshark import CardSharkScraper
from mtg_buylist_aggregator.scrapers.trollandtoad import TrollAndToadScraper
from mtg_buylist_aggregator.scrapers.cardconduit import CardConduitScraper
from mtg_buylist_aggregator.scrapers.marketplaces import GeneralMarketplaceScraper
from mtg_buylist_aggregator.scrapers.mtgmintcard import MTGMintCardScraper
from mtg_buylist_aggregator.scrapers.strikezone import StrikeZoneScraper
from mtg_buylist_aggregator.scrapers.trolltrader import TrollTraderScraper
from mtg_buylist_aggregator.scrapers.nerdragegaming import NerdRageGamingScraper
from mtg_buylist_aggregator.scrapers.harlequingames import HarlequinGamesScraper
from mtg_buylist_aggregator.models import Card, PriceData, CardPrices

logger = logging.getLogger(__name__)


class ScraperManager:
    """Manages multiple scrapers for price aggregation."""
    _SCRAPER_REGISTRY = {}
    _MOCK_SCRAPER_REGISTRY = {}

    @classmethod
    def discover_plugins(cls, plugins_dir: str = None) -> None:
        """Discover and register scraper plugins from a directory."""
        if plugins_dir is None:
            plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        
        if not os.path.exists(plugins_dir):
            return
        
        for _, name, is_pkg in pkgutil.iter_modules([plugins_dir]):
            if is_pkg:
                try:
                    module = importlib.import_module(f'mtg_buylist_aggregator.scrapers.plugins.{name}')
                    if hasattr(module, 'register_scrapers'):
                        module.register_scrapers(cls)
                except Exception as e:
                    logger.warning(f"Failed to load plugin {name}: {e}")

    @classmethod
    def register_scraper(cls, vendor: str, scraper_cls):
        cls._SCRAPER_REGISTRY[vendor] = scraper_cls

    @classmethod
    def register_mock_scraper(cls, vendor: str, mock_scraper_factory):
        cls._MOCK_SCRAPER_REGISTRY[vendor] = mock_scraper_factory

    def __init__(self, max_workers: int = 3, use_mock: bool = False, plugins_dir: str = None):
        """Initialize the scraper manager.
        
        Args:
            max_workers: Maximum number of concurrent scrapers
            use_mock: Whether to use mock scrapers
            plugins_dir: Directory to discover and load plugins
        """
        self.max_workers = max_workers
        self.use_mock = use_mock
        self.scrapers: Dict[str, BaseScraper] = {}
        self.discover_plugins(plugins_dir)
        self._initialize_scrapers()
    
    def _initialize_scrapers(self) -> None:
        """Initialize all available scrapers."""
        vendor_classes = self._get_vendor_classes()
        for vendor, scraper_cls in vendor_classes.items():
            try:
                self.scrapers[vendor] = scraper_cls()
                logger.info(f"Initialized {vendor} scraper ({'mock' if self.use_mock else 'real'})")
            except Exception as e:
                logger.error(f"Failed to initialize {vendor} scraper: {e}")
        logger.info(f"Initialized {len(self.scrapers)} scrapers")
    
    def _get_vendor_classes(self) -> Dict[str, type]:
        """Return a mapping of vendor names to scraper classes based on use_mock."""
        if self.use_mock:
            if not self._MOCK_SCRAPER_REGISTRY:
                from .mock_scraper import MockScraper
                self.register_mock_scraper("Star City Games", lambda: MockScraper("Star City Games"))
                self.register_mock_scraper("Card Kingdom", lambda: MockScraper("Card Kingdom"))
                self.register_mock_scraper("BeatTheBuylist", lambda: MockScraper("BeatTheBuylist"))
                self.register_mock_scraper("eBay Recent Sales", lambda: MockScraper("eBay Recent Sales"))
                self.register_mock_scraper("TCG Player", lambda: MockScraper("TCG Player"))
                self.register_mock_scraper("Channel Fireball", lambda: MockScraper("Channel Fireball"))
                self.register_mock_scraper("CoolStuffInc", lambda: MockScraper("CoolStuffInc"))
            return self._MOCK_SCRAPER_REGISTRY.copy()
        else:
            if not self._SCRAPER_REGISTRY:
                # Prioritize working scrapers
                from .scryfall import ScryfallScraper
                self.register_scraper("Scryfall", ScryfallScraper)
                
                # Add other scrapers that might work (but may be slower/unreliable)
                try:
                    from .cardkingdom import CardKingdomScraper
                    self.register_scraper("Card Kingdom", CardKingdomScraper)
                except:
                    pass
                
                try:
                    from .tcgplayer import TCGPlayerScraper
                    self.register_scraper("TCG Player", TCGPlayerScraper)
                except:
                    pass
                
                try:
                    from .mtggoldfish import MTGGoldfishScraper
                    self.register_scraper("MTGGoldfish", MTGGoldfishScraper)
                except:
                    pass
                
                try:
                    from .mtgstocks import MTGStocksScraper
                    self.register_scraper("MTGStocks", MTGStocksScraper)
                except:
                    pass
                
                try:
                    from .mtgmintcard import MTGMintCardScraper
                    self.register_scraper("MTGMintCard", MTGMintCardScraper)
                except:
                    pass
                
                try:
                    from .strikezone import StrikeZoneScraper
                    self.register_scraper("StrikeZoneOnline", StrikeZoneScraper)
                except:
                    pass
                
                try:
                    from .trolltrader import TrollTraderScraper
                    self.register_scraper("Troll Trader Cards", TrollTraderScraper)
                except:
                    pass
                
                try:
                    from .nerdragegaming import NerdRageGamingScraper
                    self.register_scraper("Nerd Rage Gaming", NerdRageGamingScraper)
                except:
                    pass
                
                try:
                    from .harlequingames import HarlequinGamesScraper
                    self.register_scraper("Harlequin Games", HarlequinGamesScraper)
                except:
                    pass
                
                try:
                    from .beatthebuylist import BeatTheBuylistScraper
                    self.register_scraper("BeatTheBuylist", BeatTheBuylistScraper)
                except:
                    pass
                
                # Disable problematic scrapers for now
                # from .starcitygames import StarCityGamesScraper
                # from .ebay import EbayScraper
                # from .channelfireball import ChannelFireballScraper
                # from .coolstuffinc import CoolStuffIncScraper
                # from .cardmarket import CardmarketScraper
                # from .magiccardprices import MagicCardPricesScraper
                # from .cardshark import CardSharkScraper
                # from .trollandtoad import TrollAndToadScraper
                # from .cardconduit import CardConduitScraper
                # from .marketplaces import GeneralMarketplaceScraper
            return self._SCRAPER_REGISTRY.copy()
    
    def get_card_prices(self, card: Card) -> CardPrices:
        """Get prices for a single card from all vendors, always including Scryfall."""
        card_prices = CardPrices(card=card)
        
        # Always fetch Scryfall data first for metadata and price links
        try:
            from .scryfall import ScryfallScraper
            scryfall_scraper = ScryfallScraper()
            scryfall_data = scryfall_scraper.search_card(card)
            if scryfall_data:
                card_prices.prices["Scryfall"] = scryfall_data
        except Exception as e:
            logger.warning(f"Scryfall lookup failed: {e}")
        
        # Use ThreadPoolExecutor for concurrent scraping (excluding Scryfall)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_scraper = {
                executor.submit(scraper.search_card, card): scraper_name
                for scraper_name, scraper in self.scrapers.items()
                if scraper_name != "Scryfall"
            }
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                try:
                    price_data_list = future.result()
                    if price_data_list:
                        card_prices.prices[scraper_name] = price_data_list
                        for price_data in price_data_list:
                            logger.debug(f"Got price from {scraper_name}: ${price_data.price} ({price_data.price_type})")
                    else:
                        logger.debug(f"No price found from {scraper_name}")
                except Exception as e:
                    logger.error(f"Error getting price from {scraper_name}: {e}")
        
        card_prices.update_best_prices()
        return card_prices
    
    def get_collection_prices(self, cards: List[Card]) -> List[CardPrices]:
        """Get prices for an entire collection.
        
        Args:
            cards: List of cards to search for
            
        Returns:
            List of CardPrices objects
        """
        logger.info(f"Getting prices for {len(cards)} cards from {len(self.scrapers)} vendors")
        
        card_prices_list = []
        total_cards = len(cards)
        error_log = []  # Collect errors for summary
        
        for i, card in enumerate(cards, 1):
            logger.info(f"Processing card {i}/{total_cards}: {card.name} ({card.set_name})")
            
            try:
                card_prices = CardPrices(card=card)
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_scraper = {
                        executor.submit(scraper.search_card, card): vendor
                        for vendor, scraper in self.scrapers.items()
                    }
                    for future in as_completed(future_to_scraper):
                        vendor = future_to_scraper[future]
                        try:
                            price_data_list = future.result()
                            if price_data_list:
                                card_prices.prices[vendor] = price_data_list
                                for price_data in price_data_list:
                                    logger.debug(f"Got price from {vendor} for {card.name}: ${price_data.price} ({price_data.price_type})")
                            else:
                                logger.warning(f"No price found for {card.name} from {vendor}")
                                error_log.append((card.name, vendor, "No price found"))
                        except Exception as e:
                            logger.error(f"Error getting price from {vendor} for {card.name}: {e}")
                            error_log.append((card.name, vendor, str(e)))
                card_prices.update_best_prices()
                card_prices_list.append(card_prices)
                if card_prices.best_bid:
                    best_price = card_prices.best_bid.price
                    best_vendor = card_prices.best_bid.vendor
                    logger.info(f"  Best buylist price: ${best_price} from {best_vendor}")
                else:
                    logger.warning(f"  No buylist prices found for {card.name}")
            except Exception as e:
                logger.error(f"Error processing {card.name}: {e}")
                error_log.append((card.name, "ALL", str(e)))
                card_prices_list.append(CardPrices(card=card))
        logger.info(f"Completed price lookup for {len(card_prices_list)} cards")
        if error_log:
            logger.warning("Completed scraping with the following errors:")
            for card_name, vendor, error_message in error_log:
                logger.warning(f"  {card_name} [{vendor}]: {error_message}")
            
        return card_prices_list
    
    def get_available_vendors(self) -> List[str]:
        """Get list of available vendor names.
        
        Returns:
            List of vendor names
        """
        return list(self.scrapers.keys())
    
    def test_scrapers(self) -> Dict[str, bool]:
        """Test all scrapers to ensure they're working.
        
        Returns:
            Dictionary mapping vendor names to test results
        """
        test_card = Card(
            name="Sol Ring",
            set_name="Commander 2021",
            quantity=1
        )
        
        results = {}
        for vendor_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Testing {vendor_name} scraper...")
                price_data = scraper.search_card(test_card)
                results[vendor_name] = price_data is not None
                status = "✓" if price_data else "✗"
                logger.info(f"  {status} {vendor_name}: {'Working' if price_data else 'No price found'}")
            except Exception as e:
                results[vendor_name] = False
                logger.error(f"  ✗ {vendor_name}: Error - {e}")
        
        return results
    
    def __str__(self) -> str:
        return f"ScraperManager with {len(self.scrapers)} scrapers"

    def list_vendors(self) -> List[str]:
        """List all available vendors (both registered and discovered)."""
        return list(self._SCRAPER_REGISTRY.keys()) + list(self._MOCK_SCRAPER_REGISTRY.keys()) 