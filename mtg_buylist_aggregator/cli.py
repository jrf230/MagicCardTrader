"""Command-line interface for the MTG Buylist Aggregator."""

import argparse
import logging
import sys
from typing import Optional
from datetime import datetime

from mtg_buylist_aggregator.card_manager import CardManager
from mtg_buylist_aggregator.models import Card, Rarity, FoilTreatment, PromoType, ArtworkVariant, BorderTreatment, CardSize, Language, Condition, Edition
from mtg_buylist_aggregator.scraper_manager import ScraperManager
from mtg_buylist_aggregator.price_analyzer import PriceAnalyzer
from mtg_buylist_aggregator.enhanced_price_analyzer import EnhancedPriceAnalyzer
from mtg_buylist_aggregator.price_history import PriceHistory
from mtg_buylist_aggregator.hot_card_detector import HotCardDetector
from mtg_buylist_aggregator.recommendation_engine import RecommendationEngine
from mtg_buylist_aggregator.collection_analytics import CollectionAnalytics
from mtg_buylist_aggregator.config import Config
from mtg_buylist_aggregator.web_research import MTGWebResearch
from mtg_buylist_aggregator.price_cache import PriceCache

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def add_card_command(args: argparse.Namespace) -> int:
    """Handle the add-card command."""
    try:
        # Build card data dictionary
        card_data = {
            'name': args.name,
            'set_name': args.set,
            'quantity': args.quantity,
        }
        
        # Add optional fields if provided
        if hasattr(args, 'card_number') and args.card_number:
            card_data['card_number'] = args.card_number
        
        if hasattr(args, 'rarity') and args.rarity:
            card_data['rarity'] = Rarity(args.rarity)
        
        if hasattr(args, 'foil_treatment') and args.foil_treatment:
            card_data['foil_treatment'] = FoilTreatment(args.foil_treatment)
        elif args.foil:
            card_data['foil_treatment'] = FoilTreatment.FOIL
        
        if hasattr(args, 'condition') and args.condition:
            card_data['condition'] = Condition(args.condition)
        
        if hasattr(args, 'promo_type') and args.promo_type:
            card_data['promo_type'] = PromoType(args.promo_type)
        
        if hasattr(args, 'artwork_variant') and args.artwork_variant:
            card_data['artwork_variant'] = ArtworkVariant(args.artwork_variant)
        
        if hasattr(args, 'border_treatment') and args.border_treatment:
            card_data['border_treatment'] = BorderTreatment(args.border_treatment)
        
        if hasattr(args, 'card_size') and args.card_size:
            card_data['card_size'] = CardSize(args.card_size)
        
        if hasattr(args, 'language') and args.language:
            card_data['language'] = Language(args.language)
        
        if hasattr(args, 'edition') and args.edition:
            card_data['edition'] = Edition(args.edition)
        
        if hasattr(args, 'signed') and args.signed:
            card_data['signed'] = True
        
        if hasattr(args, 'original_printing') and args.original_printing:
            card_data['original_printing'] = True
        
        if hasattr(args, 'stamp') and args.stamp:
            card_data['stamp'] = args.stamp
        
        if hasattr(args, 'serialized_number') and args.serialized_number:
            card_data['serialized_number'] = args.serialized_number
        
        if hasattr(args, 'is_token') and args.is_token:
            card_data['is_token'] = True
        
        if hasattr(args, 'is_emblem') and args.is_emblem:
            card_data['is_emblem'] = True
        
        if hasattr(args, 'is_other') and args.is_other:
            card_data['is_other'] = True
        
        card = Card(**card_data)
        
        manager = CardManager(args.collection)
        if manager.add_card(card):
            print(f"✓ Added {card.quantity}x {card.name} ({card.set_name}) to collection")
            return 0
        else:
            print("✗ Failed to add card to collection")
            return 1
            
    except Exception as e:
        logger.error(f"Error adding card: {e}")
        print(f"✗ Error: {e}")
        return 1


def remove_card_command(args: argparse.Namespace) -> int:
    """Handle the remove-card command."""
    try:
        manager = CardManager(args.collection)
        
        # Build removal criteria
        removal_kwargs = {}
        if hasattr(args, 'card_number') and args.card_number:
            removal_kwargs['card_number'] = args.card_number
        if hasattr(args, 'rarity') and args.rarity:
            removal_kwargs['rarity'] = Rarity(args.rarity)
        if hasattr(args, 'condition') and args.condition:
            removal_kwargs['condition'] = Condition(args.condition)
        if hasattr(args, 'promo_type') and args.promo_type:
            removal_kwargs['promo_type'] = PromoType(args.promo_type)
        if hasattr(args, 'artwork_variant') and args.artwork_variant:
            removal_kwargs['artwork_variant'] = ArtworkVariant(args.artwork_variant)
        if hasattr(args, 'border_treatment') and args.border_treatment:
            removal_kwargs['border_treatment'] = BorderTreatment(args.border_treatment)
        if hasattr(args, 'card_size') and args.card_size:
            removal_kwargs['card_size'] = CardSize(args.card_size)
        if hasattr(args, 'language') and args.language:
            removal_kwargs['language'] = Language(args.language)
        if hasattr(args, 'edition') and args.edition:
            removal_kwargs['edition'] = Edition(args.edition)
        if hasattr(args, 'signed') and args.signed:
            removal_kwargs['signed'] = True
        if hasattr(args, 'original_printing') and args.original_printing:
            removal_kwargs['original_printing'] = True
        if hasattr(args, 'stamp') and args.stamp:
            removal_kwargs['stamp'] = args.stamp
        if hasattr(args, 'serialized_number') and args.serialized_number:
            removal_kwargs['serialized_number'] = args.serialized_number
        if hasattr(args, 'is_token') and args.is_token:
            removal_kwargs['is_token'] = True
        if hasattr(args, 'is_emblem') and args.is_emblem:
            removal_kwargs['is_emblem'] = True
        if hasattr(args, 'is_other') and args.is_other:
            removal_kwargs['is_other'] = True
        
        if manager.remove_card(
            name=args.name,
            set_name=args.set,
            foil=args.foil,
            quantity=args.quantity,
            **removal_kwargs
        ):
            print(f"✓ Removed {args.name} ({args.set}) from collection")
            return 0
        else:
            print("✗ Failed to remove card from collection")
            return 1
            
    except Exception as e:
        logger.error(f"Error removing card: {e}")
        print(f"✗ Error: {e}")
        return 1


def list_cards_command(args: argparse.Namespace) -> int:
    """Handle the list-cards command."""
    try:
        manager = CardManager(args.collection)
        cards = manager.list_cards()
        
        if not cards:
            print("No cards in collection")
            return 0
        
        # Determine display format based on verbosity
        if args.verbose:
            print(f"\nCollection ({len(cards)} unique cards):")
            print("-" * 120)
            print(f"{'Card Name':<25} {'Set':<20} {'#':<3} {'Rarity':<8} {'Foil':<6} {'Condition':<8} {'Variant':<12}")
            print("-" * 120)
            
            for card in cards:
                rarity_str = card.rarity.value[:8] if card.rarity else ""
                foil_str = "Yes" if card.is_foil() else "No"
                condition_str = card.condition.value[:8]
                variant_str = card.artwork_variant.value[:12]
                print(f"{card.name:<25} {card.set_name:<20} {card.card_number or '':<3} {rarity_str:<8} {foil_str:<6} {condition_str:<8} {variant_str:<12}")
        else:
            print(f"\nCollection ({len(cards)} unique cards):")
            print("-" * 80)
            print(f"{'Card Name':<30} {'Set':<25} {'Qty':<5} {'Foil':<5}")
            print("-" * 80)
            
            for card in cards:
                foil_str = "Yes" if card.is_foil() else "No"
                print(f"{card.name:<30} {card.set_name:<25} {card.quantity:<5} {foil_str:<5}")
        
        # Show stats
        stats = manager.get_collection_stats()
        print(f"\nStats:")
        print(f"  Total cards: {stats['total_cards']}")
        print(f"  Unique cards: {stats['unique_cards']}")
        print(f"  Foil cards: {stats['foil_cards']}")
        print(f"  Sets: {stats['sets']}")
        
        if args.verbose and stats['rarity_breakdown']:
            print(f"  Rarity breakdown:")
            for rarity, count in sorted(stats['rarity_breakdown'].items()):
                print(f"    {rarity}: {count}")
        
        if args.verbose and stats['condition_breakdown']:
            print(f"  Condition breakdown:")
            for condition, count in sorted(stats['condition_breakdown'].items()):
                print(f"    {condition}: {count}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error listing cards: {e}")
        print(f"✗ Error: {e}")
        return 1


def search_cards_command(args: argparse.Namespace) -> int:
    """Handle the search-cards command."""
    try:
        manager = CardManager(args.collection)
        
        # Build search criteria
        search_kwargs = {}
        if hasattr(args, 'card_number') and args.card_number:
            search_kwargs['card_number'] = args.card_number
        if hasattr(args, 'rarity') and args.rarity:
            search_kwargs['rarity'] = Rarity(args.rarity)
        if hasattr(args, 'condition') and args.condition:
            search_kwargs['condition'] = Condition(args.condition)
        if hasattr(args, 'promo_type') and args.promo_type:
            search_kwargs['promo_type'] = PromoType(args.promo_type)
        if hasattr(args, 'artwork_variant') and args.artwork_variant:
            search_kwargs['artwork_variant'] = ArtworkVariant(args.artwork_variant)
        if hasattr(args, 'border_treatment') and args.border_treatment:
            search_kwargs['border_treatment'] = BorderTreatment(args.border_treatment)
        if hasattr(args, 'card_size') and args.card_size:
            search_kwargs['card_size'] = CardSize(args.card_size)
        if hasattr(args, 'language') and args.language:
            search_kwargs['language'] = Language(args.language)
        if hasattr(args, 'edition') and args.edition:
            search_kwargs['edition'] = Edition(args.edition)
        if hasattr(args, 'signed') and args.signed:
            search_kwargs['signed'] = True
        if hasattr(args, 'original_printing') and args.original_printing:
            search_kwargs['original_printing'] = True
        if hasattr(args, 'stamp') and args.stamp:
            search_kwargs['stamp'] = args.stamp
        if hasattr(args, 'serialized_number') and args.serialized_number:
            search_kwargs['serialized_number'] = args.serialized_number
        if hasattr(args, 'is_token') and args.is_token:
            search_kwargs['is_token'] = True
        if hasattr(args, 'is_emblem') and args.is_emblem:
            search_kwargs['is_emblem'] = True
        if hasattr(args, 'is_other') and args.is_other:
            search_kwargs['is_other'] = True
        
        cards = manager.search_cards(name=args.name, set_name=args.set, **search_kwargs)
        
        if not cards:
            print("No cards found matching search criteria")
            return 0
        
        print(f"\nSearch results ({len(cards)} cards):")
        print("-" * 80)
        print(f"{'Card Name':<30} {'Set':<25} {'Qty':<5} {'Foil':<5}")
        print("-" * 80)
        
        for card in cards:
            foil_str = "Yes" if card.is_foil() else "No"
            print(f"{card.name:<30} {card.set_name:<25} {card.quantity:<5} {foil_str:<5}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error searching cards: {e}")
        print(f"✗ Error: {e}")
        return 1


def find_best_prices_command(args: argparse.Namespace) -> int:
    """Handle the find-best-prices command."""
    try:
        config = Config(config_path=args.config)
        config.merge_cli_args({
            'use_mock': getattr(args, 'use_mock', None),
            'collection_file': getattr(args, 'collection', None),
            'output_format': getattr(args, 'output_format', None)
        })
        
        collection_file = config.get_collection_file()
        use_mock = config.is_mock_mode()
        
        if args.dry_run:
            print("DRY RUN MODE - No actual price fetching will occur")
            print(f"Would analyze collection from: {collection_file}")
            print(f"Would use {'mock' if use_mock else 'real'} scrapers")
            print(f"Would export to: {args.export_csv if args.export_csv else 'No export'}")
            return 0
        
        manager = CardManager(collection_file)
        cards = manager.list_cards()
        
        if not cards:
            print("No cards in collection to analyze")
            return 0
        
        print(f"Analyzing prices for {len(cards)} cards...")
        print(f"Using {'mock' if use_mock else 'real'} scrapers")
        
        # Initialize scraper manager and price analyzer
        scraper_manager = ScraperManager(use_mock=use_mock)
        price_analyzer = PriceAnalyzer()
        
        # Test scrapers first
        print("Testing scrapers...")
        test_results = scraper_manager.test_scrapers()
        working_scrapers = [vendor for vendor, working in test_results.items() if working]
        
        if not working_scrapers:
            print("⚠️  No scrapers are working. Please check your internet connection.")
            return 1
        
        print(f"✓ Found {len(working_scrapers)} working scrapers: {', '.join(working_scrapers)}")
        
        # Get prices for all cards
        print("Getting prices from vendors...")
        card_prices_list = scraper_manager.get_collection_prices(cards)
        
        # Analyze the results
        print("Analyzing prices...")
        summary = price_analyzer.analyze_collection_prices(card_prices_list)
        
        # Track price history if enabled
        if config.get("track_history", True):
            history = PriceHistory()
            history.add_price_data(card_prices_list)
            print("✓ Price history updated")
        
        # Generate and display report
        output_format = config.get_output_format()
        if output_format == "json":
            import json
            report_data = {
                "summary": summary.dict(),
                "card_prices": [cp.dict() for cp in card_prices_list]
            }
            print(json.dumps(report_data, indent=2))
        else:
            report = price_analyzer.generate_price_report(card_prices_list, summary)
            print("\n" + report)
            
            # Add trend analysis if history is available
            if config.get("track_history", True) and config.get("show_trends", True):
                try:
                    history = PriceHistory()
                    trend_report = history.generate_trend_report(card_prices_list, days=30)
                    if trend_report:
                        print("\n" + trend_report)
                except Exception as e:
                    logger.warning(f"Could not generate trend report: {e}")
        
        # Export to CSV if requested
        if args.export_csv:
            filename = args.export_csv if args.export_csv != "auto" else "price_report.csv"
            if price_analyzer.export_to_csv(card_prices_list, filename):
                print(f"\n✓ Price report exported to {filename}")
            else:
                print("\n✗ Failed to export price report")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error finding best prices: {e}")
        print(f"✗ Error: {e}")
        return 1


def config_show_command(args: argparse.Namespace) -> int:
    """Handle the config-show command."""
    try:
        config = Config(config_path=args.config)
        print("Current Configuration:")
        print("=" * 50)
        for key, value in config.config.items():
            print(f"{key}: {value}")
        return 0
    except Exception as e:
        logger.error(f"Error showing config: {e}")
        print(f"✗ Error: {e}")
        return 1


def config_set_command(args: argparse.Namespace) -> int:
    """Handle the config-set command."""
    try:
        config = Config(config_path=args.config)
        config.set(args.key, args.value)
        config.save()
        print(f"✓ Set {args.key} = {args.value}")
        return 0
    except Exception as e:
        logger.error(f"Error setting config: {e}")
        print(f"✗ Error: {e}")
        return 1


def config_reset_command(args: argparse.Namespace) -> int:
    """Handle the config-reset command."""
    try:
        config = Config(config_path=args.config)
        config.config = config.DEFAULT_CONFIG.copy()
        config.save()
        print("✓ Configuration reset to defaults")
        return 0
    except Exception as e:
        logger.error(f"Error resetting config: {e}")
        print(f"✗ Error: {e}")
        return 1


def history_show_command(args: argparse.Namespace) -> int:
    """Handle the history-show command."""
    try:
        history = PriceHistory()
        
        if args.card_name and args.set_name:
            # Show history for specific card
            entries = history.get_card_history(args.card_name, args.set_name, args.days)
            if not entries:
                print(f"No price history found for {args.card_name} ({args.set_name})")
                return 0
            
            print(f"Price History for {args.card_name} ({args.set_name}) - Last {args.days} days")
            print("=" * 80)
            for entry in entries:
                timestamp = entry["timestamp"][:19]  # Remove microseconds
                print(f"\n{timestamp}")
                print(f"  Quantity: {entry['quantity']}, Foil: {entry['foil']}")
                for vendor, price_data in entry["prices"].items():
                    print(f"  {vendor}: ${price_data['price']:.2f} ({price_data['condition']})")
                if "best_price" in entry:
                    print(f"  Best: ${entry['best_price']:.2f} from {entry['best_vendor']}")
        else:
            # Show statistics
            stats = history.get_statistics()
            print("Price History Statistics")
            print("=" * 50)
            print(f"Total cards tracked: {stats['total_cards']}")
            print(f"Total price entries: {stats['total_entries']}")
            if stats['oldest_entry']:
                print(f"Oldest entry: {stats['oldest_entry'][:19]}")
                print(f"Newest entry: {stats['newest_entry'][:19]}")
            print(f"Average entries per card: {stats['average_entries_per_card']:.1f}")
        
        return 0
    except Exception as e:
        logger.error(f"Error showing history: {e}")
        print(f"✗ Error: {e}")
        return 1


def history_trends_command(args: argparse.Namespace) -> int:
    """Handle the history-trends command."""
    try:
        history = PriceHistory()
        
        if args.card_name and args.set_name:
            # Show trends for specific card
            analysis = history.analyze_price_trends(args.card_name, args.set_name, args.days)
            if "error" in analysis:
                print(f"No trend data available for {args.card_name} ({args.set_name})")
                return 0
            
            print(f"Price Trends for {args.card_name} ({args.set_name}) - Last {args.days} days")
            print("=" * 80)
            print(f"Data points: {analysis['data_points']}")
            print(f"Vendors: {', '.join(analysis['vendors'])}")
            print()
            
            # Show best price trend
            if "best_price" in analysis["trends"]:
                trend = analysis["trends"]["best_price"]
                trend_symbol = "↗️" if trend["trend"] == "up" else "↘️" if trend["trend"] == "down" else "→"
                print(f"Best Price: {trend_symbol} ${trend['change']:+.2f} ({trend['change_percent']:+.1f}%)")
                print(f"  From: ${trend['first_price']:.2f} → To: ${trend['last_price']:.2f}")
                print()
            
            # Show vendor trends
            for vendor, change in analysis["price_changes"].items():
                trend_symbol = "↗️" if change["trend"] == "up" else "↘️" if change["trend"] == "down" else "→"
                print(f"{vendor}: {trend_symbol} ${change['change']:+.2f} ({change['change_percent']:+.1f}%)")
                print(f"  From: ${change['first_price']:.2f} → To: ${change['last_price']:.2f}")
        else:
            print("Please specify both --card-name and --set-name for trend analysis")
            return 1
        
        return 0
    except Exception as e:
        logger.error(f"Error showing trends: {e}")
        print(f"✗ Error: {e}")
        return 1


def history_cleanup_command(args: argparse.Namespace) -> int:
    """Handle the history-cleanup command."""
    try:
        history = PriceHistory()
        
        # Show stats before cleanup
        stats_before = history.get_statistics()
        print(f"Before cleanup: {stats_before['total_entries']} entries for {stats_before['total_cards']} cards")
        
        # Perform cleanup
        history.cleanup_old_data(args.days)
        
        # Show stats after cleanup
        stats_after = history.get_statistics()
        print(f"After cleanup: {stats_after['total_entries']} entries for {stats_after['total_cards']} cards")
        
        removed_entries = stats_before['total_entries'] - stats_after['total_entries']
        removed_cards = stats_before['total_cards'] - stats_after['total_cards']
        
        print(f"✓ Removed {removed_entries} entries and {removed_cards} cards")
        
        return 0
    except Exception as e:
        logger.error(f"Error cleaning up history: {e}")
        print(f"✗ Error: {e}")
        return 1


def hot_cards_command(args: argparse.Namespace) -> int:
    """Handle the hot-cards command."""
    try:
        manager = CardManager(args.collection)
        cards = manager.list_cards()
        if not cards:
            print("No cards in collection")
            return 0
        config = Config(config_path=args.config)
        if args.use_mock is not None:
            use_mock = args.use_mock
        else:
            use_mock = config.is_mock_mode()
        if getattr(args, 'dry_run', False):
            print("DRY RUN MODE - No actual price fetching will occur")
            print(f"Would analyze {len(cards)} cards from: {args.collection}")
            print(f"Would use {'mock' if use_mock else 'real'} scrapers")
            print(f"Would analyze price movements over {args.days} days")
            print(f"Would export to: {args.export_csv if getattr(args, 'export_csv', None) else 'No export'}")
            return 0
        scraper_manager = ScraperManager(use_mock=use_mock)
        
        print(f"Fetching prices for {len(cards)} cards...")
        card_prices_list = scraper_manager.get_collection_prices(cards)
        
        # Initialize hot card detector
        price_history = PriceHistory()
        hot_card_detector = HotCardDetector(price_history)
        
        # Detect hot cards
        print(f"Analyzing price movements over {args.days} days...")
        hot_cards = hot_card_detector.detect_hot_cards(card_prices_list, days=args.days)
        
        if not hot_cards:
            print("No hot cards detected in the current analysis period.")
            return 0
        
        # Generate and display report
        report = hot_card_detector.generate_hot_cards_report(hot_cards)
        print(report)
        
        # Export to CSV if requested
        if args.export_csv:
            import csv
            with open(args.export_csv, 'w', newline='') as csvfile:
                fieldnames = ['Card Name', 'Set', 'Hot Score', 'Price Change %', 'Price Change $', 
                             'Trend', 'Recommendation', 'Risk Level', 'Quantity', 'Total Value Impact']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for card_analysis in hot_cards:
                    card = card_analysis['card']
                    writer.writerow({
                        'Card Name': card.name,
                        'Set': card.set_name,
                        'Hot Score': f"{card_analysis['hot_score']:.2f}",
                        'Price Change %': f"{card_analysis['price_change_percent']:+.1f}",
                        'Price Change $': f"{card_analysis['price_change_amount']:+.2f}",
                        'Trend': card_analysis['trend_direction'].replace('_', ' ').title(),
                        'Recommendation': card_analysis['recommendation'],
                        'Risk Level': card_analysis['risk_factors'][0] if card_analysis['risk_factors'] else 'None',
                        'Quantity': card.quantity,
                        'Total Value Impact': f"{card_analysis['price_change_amount'] * card.quantity:+.2f}"
                    })
            
            print(f"\n✓ Hot cards report exported to {args.export_csv}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error detecting hot cards: {e}")
        print(f"✗ Error: {e}")
        return 1


def recommendations_command(args: argparse.Namespace) -> int:
    """Handle the recommendations command."""
    try:
        manager = CardManager(args.collection)
        cards = manager.list_cards()
        if not cards:
            print("No cards in collection")
            return 0
        config = Config(config_path=args.config)
        if args.use_mock is not None:
            use_mock = args.use_mock
        else:
            use_mock = config.is_mock_mode()
        if getattr(args, 'dry_run', False):
            print("DRY RUN MODE - No actual price fetching will occur")
            print(f"Would analyze {len(cards)} cards from: {args.collection}")
            print(f"Would use {'mock' if use_mock else 'real'} scrapers")
            print(f"Would generate recommendations")
            print(f"Would export to: {args.export_csv if getattr(args, 'export_csv', None) else 'No export'}")
            return 0
        scraper_manager = ScraperManager(use_mock=use_mock)
        
        print(f"Fetching prices for {len(cards)} cards...")
        card_prices_list = scraper_manager.get_collection_prices(cards)
        
        # Initialize recommendation engine
        price_history = PriceHistory()
        hot_card_detector = HotCardDetector(price_history)
        recommendation_engine = RecommendationEngine(price_history, hot_card_detector)
        
        # Generate collection summary
        price_analyzer = PriceAnalyzer()
        collection_summary = price_analyzer.analyze_collection_prices(card_prices_list)
        
        # Generate recommendations
        print("Generating strategic recommendations...")
        recommendations = recommendation_engine.generate_recommendations(card_prices_list, collection_summary)
        
        # Generate and display report
        report = recommendation_engine.generate_recommendation_report(recommendations)
        print(report)
        
        # Export to CSV if requested
        if args.export_csv:
            import csv
            with open(args.export_csv, 'w', newline='') as csvfile:
                fieldnames = ['Action', 'Card Name', 'Set', 'Confidence', 'Current Price', 
                             'Potential Value', 'Risk Level', 'Timeframe', 'Reasoning']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write sell recommendations
                for rec in recommendations['sell']:
                    card = rec['card']
                    writer.writerow({
                        'Action': 'SELL',
                        'Card Name': card.name,
                        'Set': card.set_name,
                        'Confidence': f"{rec['confidence']:.2f}",
                        'Current Price': f"${rec['current_price']:.2f}",
                        'Potential Value': f"${rec['potential_profit']:.2f}",
                        'Risk Level': rec['risk_level'].title(),
                        'Timeframe': rec['timeframe'],
                        'Reasoning': '; '.join(rec['reasoning'])
                    })
                
                # Write buy recommendations
                for rec in recommendations['buy']:
                    card = rec['card']
                    writer.writerow({
                        'Action': 'BUY',
                        'Card Name': card.name,
                        'Set': card.set_name,
                        'Confidence': f"{rec['confidence']:.2f}",
                        'Current Price': f"${rec['current_price']:.2f}",
                        'Potential Value': f"${rec['potential_savings']:.2f}",
                        'Risk Level': rec['risk_level'].title(),
                        'Timeframe': rec['timeframe'],
                        'Reasoning': '; '.join(rec['reasoning'])
                    })
                
                # Write hold recommendations
                for rec in recommendations['hold']:
                    card = rec['card']
                    writer.writerow({
                        'Action': 'HOLD',
                        'Card Name': card.name,
                        'Set': card.set_name,
                        'Confidence': f"{rec['confidence']:.2f}",
                        'Current Price': f"${rec['current_price']:.2f}",
                        'Potential Value': f"${rec['potential_growth']:.2f}",
                        'Risk Level': rec['risk_level'].title(),
                        'Timeframe': rec['timeframe'],
                        'Reasoning': '; '.join(rec['reasoning'])
                    })
            
            print(f"\n✓ Recommendations report exported to {args.export_csv}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        print(f"✗ Error: {e}")
        return 1


def analytics_command(args: argparse.Namespace) -> int:
    """Handle the analytics command."""
    try:
        manager = CardManager(args.collection)
        cards = manager.list_cards()
        if not cards:
            print("No cards in collection")
            return 0
        config = Config(config_path=args.config)
        if args.use_mock is not None:
            use_mock = args.use_mock
        else:
            use_mock = config.is_mock_mode()
        if getattr(args, 'dry_run', False):
            print("DRY RUN MODE - No actual price fetching will occur")
            print(f"Would analyze {len(cards)} cards from: {args.collection}")
            print(f"Would use {'mock' if use_mock else 'real'} scrapers")
            print(f"Would perform comprehensive collection analysis")
            print(f"Would export to: {args.export_csv if getattr(args, 'export_csv', None) else 'No export'}")
            return 0
        scraper_manager = ScraperManager(use_mock=use_mock)
        
        print(f"Fetching prices for {len(cards)} cards...")
        card_prices_list = scraper_manager.get_collection_prices(cards)
        
        # Initialize analytics engine
        price_history = PriceHistory()
        collection_analytics = CollectionAnalytics(price_history)
        
        # Generate collection summary
        price_analyzer = PriceAnalyzer()
        collection_summary = price_analyzer.analyze_collection_prices(card_prices_list)
        
        # Perform comprehensive analysis
        print("Performing comprehensive collection analysis...")
        analysis = collection_analytics.analyze_collection(card_prices_list, collection_summary)
        
        # Generate and display report
        report = collection_analytics.generate_analytics_report(analysis)
        print(report)
        
        # Export to CSV if requested
        if args.export_csv:
            import csv
            with open(args.export_csv, 'w', newline='') as csvfile:
                fieldnames = ['Analysis Type', 'Metric', 'Value', 'Details']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write collection summary
                summary = analysis['collection_summary']
                writer.writerow({
                    'Analysis Type': 'Collection Summary',
                    'Metric': 'Total Cards',
                    'Value': summary.total_cards,
                    'Details': ''
                })
                writer.writerow({
                    'Analysis Type': 'Collection Summary',
                    'Metric': 'Total Value',
                    'Value': f"${summary.best_total_value:.2f}",
                    'Details': summary.best_vendor or 'N/A'
                })
                
                # Write performance data
                performance = analysis['performance']
                writer.writerow({
                    'Analysis Type': 'Performance',
                    'Metric': 'Growth Rate',
                    'Value': f"{performance['overall_growth_rate']:+.1f}%",
                    'Details': performance['performance_level'].title()
                })
                
                # Write diversification data
                diversification = analysis['diversification']
                writer.writerow({
                    'Analysis Type': 'Diversification',
                    'Metric': 'Diversification Level',
                    'Value': diversification['diversification_level'].title(),
                    'Details': f"HHI: {diversification['hhi_index']:.3f}"
                })
                
                # Write risk assessment
                risk = analysis['risk_assessment']
                writer.writerow({
                    'Analysis Type': 'Risk Assessment',
                    'Metric': 'Risk Level',
                    'Value': risk['risk_level'].title(),
                    'Details': f"Score: {risk['overall_risk_score']:.3f}"
                })
                
                # Write top performers
                for i, performer in enumerate(analysis['top_performers'][:5], 1):
                    card = performer['card']
                    writer.writerow({
                        'Analysis Type': 'Top Performers',
                        'Metric': f"#{i}",
                        'Value': card.name,
                        'Details': f"{performer['growth_rate']:+.1f}% ({card.set_name})"
                    })
            
            print(f"\n✓ Analytics report exported to {args.export_csv}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error performing analytics: {e}")
        print(f"✗ Error: {e}")
        return 1


def vendor_health_command(args: argparse.Namespace) -> int:
    """Handle the vendor-health command."""
    try:
        config = Config(config_path=args.config)
        use_mock = getattr(args, 'use_mock', None)
        if use_mock is None:
            use_mock = config.is_mock_mode()
        scraper_manager = ScraperManager(use_mock=use_mock)
        print("Checking vendor scraper health...")
        test_results = scraper_manager.test_scrapers()
        print("\nVENDOR SCRAPER HEALTH SUMMARY")
        print("=" * 40)
        print(f"{'Vendor':<20}Status")
        print("-" * 40)
        for vendor, working in test_results.items():
            status = '✓ OK' if working else '✗ FAIL'
            print(f"{vendor:<20}{status}")
        print("=" * 40)
        if all(test_results.values()):
            print("All vendor scrapers are working!")
            return 0
        else:
            print("Some vendor scrapers are not working. Check logs for details.")
            return 1
    except Exception as e:
        logger.error(f"Error checking vendor health: {e}")
        print(f"✗ Error: {e}")
        return 1


def list_vendors_command(args: argparse.Namespace) -> int:
    """Handle the list-vendors command."""
    try:
        config = Config(config_path=args.config)
        use_mock = getattr(args, 'use_mock', None)
        if use_mock is None:
            use_mock = config.is_mock_mode()
        scraper_manager = ScraperManager(use_mock=use_mock)
        vendors = scraper_manager.list_vendors()
        print("AVAILABLE VENDOR SCRAPERS")
        print("=" * 30)
        for vendor in sorted(vendors):
            print(f"• {vendor}")
        print(f"\nTotal: {len(vendors)} vendors")
        return 0
    except Exception as e:
        logger.error(f"Error listing vendors: {e}")
        print(f"✗ Error: {e}")
        return 1


def market_analysis_command(args: argparse.Namespace) -> int:
    """Handle the market-analysis command."""
    try:
        # Load collection
        manager = CardManager(args.collection)
        cards = manager.list_cards()
        
        if not cards:
            print("No cards in collection to analyze")
            return 0
        
        print(f"Analyzing market data for {len(cards)} cards...")
        
        # Initialize scrapers and analyzer
        scraper_manager = ScraperManager(
            max_workers=args.max_workers,
            use_mock=args.use_mock
        )
        
        enhanced_analyzer = EnhancedPriceAnalyzer()
        
        # Get prices for all cards
        if args.dry_run:
            print("DRY RUN: Would fetch prices from vendors...")
            return 0
        
        card_prices_list = scraper_manager.get_collection_prices(cards)
        
        # Perform enhanced market analysis
        analysis = enhanced_analyzer.analyze_collection_market(card_prices_list)
        
        if not analysis['insights']:
            print("No market insights available")
            return 0
        
        # Display results
        print(f"\n=== MARKET ANALYSIS REPORT ===")
        print(f"Analysis Date: {analysis['analysis_date'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Cards Analyzed: {len(analysis['insights'])}")
        print(f"Total Market Value: ${analysis['total_market_value']:.2f}")
        print(f"Total Buylist Value: ${analysis['total_buylist_value']:.2f}")
        print(f"Average Price Spread: ${analysis['avg_price_spread']:.2f}")
        print(f"Average Volatility: ${analysis['avg_volatility']:.2f}")
        print(f"Average Risk Score: {analysis['avg_risk_score']:.2f}")
        
        # Display recommendations summary
        print(f"\n=== RECOMMENDATIONS SUMMARY ===")
        for rec_type, cards in analysis['recommendations'].items():
            print(f"{rec_type}: {len(cards)} cards")
            if args.verbose and cards:
                for card_name in cards[:5]:  # Show first 5
                    print(f"  - {card_name}")
                if len(cards) > 5:
                    print(f"  ... and {len(cards) - 5} more")
        
        # Display top insights
        if args.verbose:
            print(f"\n=== DETAILED INSIGHTS ===")
            insights = sorted(analysis['insights'], 
                            key=lambda x: abs(x.price_spread), reverse=True)
            
            print(f"{'Card':<25} {'Market':<8} {'Buylist':<8} {'Spread':<8} {'Trend':<8} {'Risk':<6} {'Rec':<12}")
            print("-" * 85)
            
            for insight in insights[:20]:  # Show top 20
                trend_str = f"{insight.trend_percentage:+.1f}%" if insight.trend_percentage != 0 else "0%"
                print(f"{insight.card.name:<25} "
                      f"${insight.current_market_price:<7.2f} "
                      f"${insight.buylist_avg:<7.2f} "
                      f"${insight.price_spread:<7.2f} "
                      f"{trend_str:<8} "
                      f"{insight.risk_score:<6.2f} "
                      f"{insight.recommendation:<12}")
                # Show Scryfall price links if available
                if insight.scryfall_links:
                    print("    Scryfall Links:")
                    for vendor, url in insight.scryfall_links.items():
                        print(f"      {vendor}: {url}")
        
        # Export to CSV if requested
        if args.export_csv:
            import csv
            from datetime import datetime as dt
            
            filename = f"market_analysis_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['Card Name', 'Set', 'Market Price', 'Buylist Avg', 'eBay Avg',
                             'Price Spread', 'Volatility', 'Trend %', 'Volume Score',
                             'Risk Score', 'Recommendation', 'Confidence']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for insight in analysis['insights']:
                    writer.writerow({
                        'Card Name': insight.card.name,
                        'Set': insight.card.set_name,
                        'Market Price': insight.current_market_price,
                        'Buylist Avg': insight.buylist_avg,
                        'eBay Avg': insight.ebay_avg,
                        'Price Spread': insight.price_spread,
                        'Volatility': insight.market_volatility,
                        'Trend %': insight.trend_percentage,
                        'Volume Score': insight.volume_score,
                        'Risk Score': insight.risk_score,
                        'Recommendation': insight.recommendation,
                        'Confidence': insight.confidence
                    })
            
            print(f"\nExported detailed analysis to {filename}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in market analysis: {e}")
        print(f"✗ Error: {e}")
        return 1


def research_command(args: argparse.Namespace) -> int:
    """Handle the research command."""
    try:
        research = MTGWebResearch()
        
        if args.vendor_report:
            print("Generating vendor analysis report...")
            report = research.generate_vendor_report()
            print(report)
            
            if args.export_csv:
                import csv
                from datetime import datetime as dt
                
                filename = f"vendor_research_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                with open(filename, 'w', newline='') as csvfile:
                    fieldnames = ['Vendor Name', 'URL', 'Description', 'Features']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    vendors = research.discover_buylist_vendors()
                    for vendor in vendors:
                        writer.writerow({
                            'Vendor Name': vendor['name'],
                            'URL': vendor['url'],
                            'Description': vendor['description'],
                            'Features': ', '.join(vendor['features'])
                        })
                
                print(f"\nExported vendor data to {filename}")
        
        elif args.pricing_sources:
            print("=== MTG PRICING DATA SOURCES ===")
            sources = research.get_pricing_sources()
            
            for source in sources:
                print(f"\n• {source['name']} ({source['type']})")
                print(f"  URL: {source['url']}")
                print(f"  Description: {source['description']}")
                print(f"  Features: {', '.join(source['features'])}")
        
        elif args.market_insights:
            print("=== MARKET INSIGHTS ===")
            insights = research.get_market_insights()
            
            print(f"Analysis Date: {insights['analysis_date'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("\nFormat Trends:")
            for format_name, trend in insights['market_trends'].items():
                print(f"  {format_name.title()}: {trend}")
            
            print("\nHot Cards:")
            for card in insights['hot_cards']:
                print(f"  • {card}")
            
            print("\nFormat Metagame:")
            for format_name, description in insights['format_metagame'].items():
                print(f"  {format_name.title()}: {description}")
            
            print("\nInvestment Opportunities:")
            for opportunity in insights['investment_opportunities']:
                print(f"  • {opportunity}")
        
        else:
            # Default: show all research
            print("=== MTG MARKET RESEARCH ===")
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("")
            
            # Show vendors
            print("=== BULYLIST VENDORS ===")
            vendors = research.discover_buylist_vendors()
            for vendor in vendors[:10]:  # Show first 10
                print(f"• {vendor['name']} - {vendor['description']}")
            if len(vendors) > 10:
                print(f"... and {len(vendors) - 10} more vendors")
            
            print("\n=== PRICING SOURCES ===")
            sources = research.get_pricing_sources()
            for source in sources:
                print(f"• {source['name']} ({source['type']}) - {source['description']}")
            
            print("\n=== MARKET TRENDS ===")
            insights = research.get_market_insights()
            for format_name, trend in insights['market_trends'].items():
                print(f"• {format_name.title()}: {trend}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in research: {e}")
        print(f"✗ Error: {e}")
        return 1


def update_prices_command():
    """Update price cache for all cards in collection (daily update)."""
    try:
        from .card_manager import CardManager
        from .price_cache import PriceCache
        from .price_history import PriceHistory
        from .scraper_manager import ScraperManager
        
        print("🔄 Updating price cache...")
        
        # Load collection
        manager = CardManager()
        cards = manager.list_cards()
        
        if not cards:
            print("❌ No cards in collection to update")
            return
        
        print(f"📊 Found {len(cards)} cards in collection")
        
        # Update price cache
        price_cache = PriceCache()
        price_cache.update_cache(cards, force_update=True)
        
        # Update price history
        scraper_manager = ScraperManager(use_mock=False)
        card_prices_list = scraper_manager.get_collection_prices(cards)
        
        history = PriceHistory()
        history.add_price_data(card_prices_list)
        
        # Get cache status
        status = price_cache.get_cache_status()
        
        print("✅ Price cache updated successfully!")
        print(f"📈 Updated {status['total_cards']} cards")
        print(f"🕒 Last update: {status['last_update']}")
        print(f"🔄 Next update: {status['next_update']}")
        
        # Clean up old cache entries
        price_cache.cleanup_old_cache(days_to_keep=7)
        history.cleanup_old_data(days_to_keep=90)
        
        print("🧹 Cleaned up old cache and history data")
        
    except Exception as e:
        print(f"❌ Error updating prices: {e}")
        sys.exit(1)


def create_parent_parser() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument('--version', action='version', version='MagicCardTrader 1.0.0')
    parent.add_argument('--verbose', action='store_true', help='Enable verbose debug output')
    parent.add_argument('--config', type=str, default=None, help='Path to alternate config file')
    parent.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    return parent


def create_parser() -> argparse.ArgumentParser:
    parent = create_parent_parser()
    parser = argparse.ArgumentParser(
        description="Magic: The Gathering Buylist Aggregator & Collection Optimizer",
        parents=[parent]
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add card command
    add_parser = subparsers.add_parser('add-card', help='Add a card to your collection')
    add_parser.add_argument('name', help='Card name')
    add_parser.add_argument('--set', '-s', required=True, help='Set name')
    add_parser.add_argument('--quantity', '-q', type=int, default=1, help='Quantity (default: 1)')
    add_parser.add_argument('--foil', '-f', action='store_true', help='Foil version')
    add_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    
    # Remove card command
    remove_parser = subparsers.add_parser('remove-card', help='Remove a card from your collection')
    remove_parser.add_argument('name', help='Card name')
    remove_parser.add_argument('--set', '-s', required=True, help='Set name')
    remove_parser.add_argument('--foil', '-f', action='store_true', help='Foil version')
    remove_parser.add_argument('--quantity', '-q', type=int, help='Quantity to remove (default: all)')
    remove_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    
    # List cards command
    list_parser = subparsers.add_parser('list-cards', help='List all cards in your collection')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    list_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    
    # Search cards command
    search_parser = subparsers.add_parser('search-cards', help='Search for cards in your collection')
    search_parser.add_argument('--name', '-n', help='Search by card name')
    search_parser.add_argument('--set', '-s', help='Search by set name')
    search_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    
    # Find best prices command
    find_best_prices_parser = subparsers.add_parser('find-best-prices', parents=[parent], help='Find best buylist prices for collection')
    find_best_prices_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    find_best_prices_parser.add_argument('--use-mock', action='store_true', help='Use mock scrapers for testing')
    find_best_prices_parser.add_argument('--output-format', choices=['table', 'json', 'csv'], default='table', help='Output format')
    find_best_prices_parser.add_argument('--export-csv', nargs='?', const='auto', help='Export results to CSV file')
    find_best_prices_parser.set_defaults(func=find_best_prices_command)
    
    # Hot cards command
    hot_cards_parser = subparsers.add_parser('hot-cards', help='Detect hot cards with price spikes')
    hot_cards_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    hot_cards_parser.add_argument('--use-mock', action='store_true', help='Use mock scrapers for testing')
    hot_cards_parser.add_argument('--days', '-d', type=int, default=7, help='Days to analyze for price spikes')
    hot_cards_parser.add_argument('--export-csv', nargs='?', const='auto', help='Export results to CSV file')
    hot_cards_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    hot_cards_parser.set_defaults(func=hot_cards_command)
    
    # Recommendations command
    recommendations_parser = subparsers.add_parser('recommendations', help='Get buy/sell/hold recommendations')
    recommendations_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    recommendations_parser.add_argument('--use-mock', action='store_true', help='Use mock scrapers for testing')
    recommendations_parser.add_argument('--export-csv', nargs='?', const='auto', help='Export results to CSV file')
    recommendations_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    recommendations_parser.set_defaults(func=recommendations_command)
    
    # Analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Analyze your collection in depth')
    analytics_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    analytics_parser.add_argument('--use-mock', action='store_true', help='Use mock scrapers for testing')
    analytics_parser.add_argument('--export-csv', nargs='?', const='auto', help='Export results to CSV file')
    analytics_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    analytics_parser.set_defaults(func=analytics_command)
    
    # Configuration commands
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Config commands')
    
    # Config show
    config_show_parser = config_subparsers.add_parser('show', help='Show current configuration')
    
    # Config set
    config_set_parser = config_subparsers.add_parser('set', help='Set a configuration value')
    config_set_parser.add_argument('key', help='Configuration key')
    config_set_parser.add_argument('value', help='Configuration value')
    
    # Config reset
    config_reset_parser = config_subparsers.add_parser('reset', help='Reset configuration to defaults')
    
    # History commands
    history_parser = subparsers.add_parser('history', help='Price history management')
    history_subparsers = history_parser.add_subparsers(dest='history_command', help='History commands')
    
    # History show
    history_show_parser = history_subparsers.add_parser('show', help='Show price history')
    history_show_parser.add_argument('--card-name', '-n', help='Card name')
    history_show_parser.add_argument('--set-name', '-s', help='Set name')
    history_show_parser.add_argument('--days', '-d', type=int, default=30, help='Number of days to show')
    
    # History trends
    history_trends_parser = history_subparsers.add_parser('trends', help='Show price trends')
    history_trends_parser.add_argument('--card-name', '-n', help='Card name')
    history_trends_parser.add_argument('--set-name', '-s', help='Set name')
    history_trends_parser.add_argument('--days', '-d', type=int, default=30, help='Number of days to show')
    
    # History cleanup
    history_cleanup_parser = history_subparsers.add_parser('cleanup', help='Clean up price history')
    history_cleanup_parser.add_argument('--days', '-d', type=int, default=30, help='Number of days to clean up')
    
    # Vendor health command
    vendor_health_parser = subparsers.add_parser('vendor-health', help='Check health of all vendor scrapers')
    vendor_health_parser.add_argument('--use-mock', action='store_true', help='Use mock scrapers for testing')
    vendor_health_parser.set_defaults(func=vendor_health_command)
    
    # List vendors command
    list_vendors_parser = subparsers.add_parser('list-vendors', help='List all available vendor scrapers')
    list_vendors_parser.add_argument('--use-mock', action='store_true', help='Use mock scrapers for testing')
    list_vendors_parser.set_defaults(func=list_vendors_command)
    
    # Market analysis command
    market_analysis_parser = subparsers.add_parser('market-analysis', help='Perform market analysis on your collection')
    market_analysis_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    market_analysis_parser.add_argument('--use-mock', action='store_true', help='Use mock scrapers for testing')
    market_analysis_parser.add_argument('--max-workers', type=int, default=5, help='Maximum number of worker threads')
    market_analysis_parser.add_argument('--export-csv', nargs='?', const='auto', help='Export results to CSV file')
    market_analysis_parser.set_defaults(func=market_analysis_command)
    
    # Research command
    research_parser = subparsers.add_parser('research', help='Research MTG vendors and market data')
    research_parser.add_argument('--vendor-report', action='store_true', help='Generate detailed vendor analysis report')
    research_parser.add_argument('--pricing-sources', action='store_true', help='Show pricing data sources')
    research_parser.add_argument('--market-insights', action='store_true', help='Show market insights and trends')
    research_parser.add_argument('--export-csv', nargs='?', const='auto', help='Export vendor data to CSV')
    research_parser.set_defaults(func=research_command)
    
    # Update prices command
    update_prices_parser = subparsers.add_parser('update-prices', help='Update price cache for all cards in collection (daily update)')
    update_prices_parser.add_argument('--collection', '-c', default='collection.csv', help='Collection file path')
    update_prices_parser.add_argument('--force', '-f', action='store_true', help='Force update even if cache is recent')
    
    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if getattr(args, 'verbose', False):
        setup_logging(verbose=True)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    if args.command == 'add-card':
        return add_card_command(args)
    elif args.command == 'remove-card':
        return remove_card_command(args)
    elif args.command == 'list-cards':
        return list_cards_command(args)
    elif args.command == 'search-cards':
        return search_cards_command(args)
    elif args.command == 'find-best-prices':
        return find_best_prices_command(args)
    elif args.command == 'hot-cards':
        return hot_cards_command(args)
    elif args.command == 'recommendations':
        return recommendations_command(args)
    elif args.command == 'analytics':
        return analytics_command(args)
    elif args.command == 'config':
        if args.config_command == 'show':
            return config_show_command(args)
        elif args.config_command == 'set':
            return config_set_command(args)
        elif args.config_command == 'reset':
            return config_reset_command(args)
        else:
            print("Unknown config command. Use 'config show', 'config set', or 'config reset'")
            return 1
    elif args.command == 'history':
        if args.history_command == 'show':
            return history_show_command(args)
        elif args.history_command == 'trends':
            return history_trends_command(args)
        elif args.history_command == 'cleanup':
            return history_cleanup_command(args)
        else:
            print("Unknown history command. Use 'history show', 'history trends', or 'history cleanup'")
            return 1
    elif args.command == 'market-analysis':
        return market_analysis_command(args)
    elif args.command == 'research':
        return research_command(args)
    elif args.command == 'update-prices':
        update_prices_command()
    elif hasattr(args, 'func'):
        return args.func(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 