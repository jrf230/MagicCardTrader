"""Price history tracking and analysis module."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .models import Card, CardPrices, PriceData

logger = logging.getLogger(__name__)


class PriceHistory:
    """Tracks and analyzes price history over time."""
    
    def __init__(self, history_file: str = "price_history.json"):
        """Initialize price history tracker.
        
        Args:
            history_file: Path to JSON file storing price history
        """
        self.history_file = Path(history_file)
        self.history = self._load_history()
    
    def _load_history(self) -> Dict[str, List[Dict]]:
        """Load price history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load price history: {e}")
                return {}
        return {}
    
    def _save_history(self) -> None:
        """Save price history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
            logger.debug(f"Saved price history to {self.history_file}")
        except Exception as e:
            logger.error(f"Failed to save price history: {e}")
    
    def add_price_data(self, card_prices_list: List[CardPrices]) -> None:
        """Add new price data to history.
        
        Args:
            card_prices_list: List of CardPrices objects from current run
        """
        timestamp = datetime.now().isoformat()
        
        for card_prices in card_prices_list:
            card = card_prices.card
            card_key = f"{card.name} ({card.set_name})"
            
            if card_key not in self.history:
                self.history[card_key] = []
            
            # Create price entry
            price_entry = {
                "timestamp": timestamp,
                "card_name": card.name,
                "set_name": card.set_name,
                "quantity": card.quantity,
                "foil": card.is_foil(),
                "prices": {}
            }
            
            # Add prices from each vendor
            for vendor, price_data_list in card_prices.prices.items():
                # price_data_list is now a list of PriceData objects
                for price_data in price_data_list:
                    price_entry["prices"][vendor] = {
                        "price": price_data.price,
                        "condition": price_data.condition,
                        "quantity_limit": price_data.quantity_limit
                    }
            
            # Add best price info
            if card_prices.best_bid:
                price_entry["best_price"] = card_prices.best_bid.price
                price_entry["best_vendor"] = card_prices.best_bid.vendor
            
            self.history[card_key].append(price_entry)
        
        self._save_history()
        logger.info(f"Added price data for {len(card_prices_list)} cards to history")
    
    def get_card_history(self, card_name: str, set_name: str, days: int = 30) -> List[Dict]:
        """Get price history for a specific card.
        
        Args:
            card_name: Name of the card
            set_name: Set name
            days: Number of days to look back
            
        Returns:
            List of price entries for the card
        """
        card_key = f"{card_name} ({set_name})"
        if card_key not in self.history:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = []
        
        for entry in self.history[card_key]:
            entry_date = datetime.fromisoformat(entry["timestamp"])
            if entry_date >= cutoff_date:
                recent_entries.append(entry)
        
        return recent_entries
    
    def analyze_price_trends(self, card_name: str, set_name: str, days: int = 30) -> Dict:
        """Analyze price trends for a card.
        
        Args:
            card_name: Name of the card
            set_name: Set name
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        history = self.get_card_history(card_name, set_name, days)
        if not history:
            return {"error": "No price history available"}
        
        analysis = {
            "card_name": card_name,
            "set_name": set_name,
            "period_days": days,
            "data_points": len(history),
            "vendors": set(),
            "price_changes": {},
            "trends": {}
        }
        
        # Collect all vendors
        for entry in history:
            analysis["vendors"].update(entry["prices"].keys())
        
        analysis["vendors"] = list(analysis["vendors"])
        
        # Analyze price changes for each vendor
        for vendor in analysis["vendors"]:
            vendor_prices = []
            for entry in history:
                if vendor in entry["prices"]:
                    vendor_prices.append(entry["prices"][vendor]["price"])
            
            if len(vendor_prices) >= 2:
                first_price = vendor_prices[0]
                last_price = vendor_prices[-1]
                change = last_price - first_price
                change_percent = (change / first_price) * 100 if first_price > 0 else 0
                
                analysis["price_changes"][vendor] = {
                    "first_price": first_price,
                    "last_price": last_price,
                    "change": change,
                    "change_percent": change_percent,
                    "trend": "up" if change > 0 else "down" if change < 0 else "stable"
                }
        
        # Analyze best price trends
        best_prices = [entry["best_price"] for entry in history if "best_price" in entry]
        if len(best_prices) >= 2:
            first_best = best_prices[0]
            last_best = best_prices[-1]
            best_change = last_best - first_best
            best_change_percent = (best_change / first_best) * 100 if first_best > 0 else 0
            
            analysis["trends"]["best_price"] = {
                "first_price": first_best,
                "last_price": last_best,
                "change": best_change,
                "change_percent": best_change_percent,
                "trend": "up" if best_change > 0 else "down" if best_change < 0 else "stable"
            }
        
        return analysis
    
    def generate_trend_report(self, card_prices_list: List[CardPrices], days: int = 30) -> str:
        """Generate a trend report for all cards in the collection.
        
        Args:
            card_prices_list: Current price data
            days: Number of days to analyze
            
        Returns:
            Formatted trend report
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PRICE TREND ANALYSIS")
        report_lines.append("=" * 80)
        report_lines.append(f"Analysis period: Last {days} days")
        report_lines.append("")
        
        any_trends = False
        for card_prices in card_prices_list:
            card = card_prices.card
            analysis = self.analyze_price_trends(card.name, card.set_name, days)
            
            if "error" in analysis or not analysis["trends"]:
                continue
            any_trends = True
            report_lines.append(f"Card: {card.name} ({card.set_name})")
            report_lines.append("-" * 50)
            
            # Show best price trend
            if "best_price" in analysis["trends"]:
                trend = analysis["trends"]["best_price"]
                trend_symbol = "↗️" if trend["trend"] == "up" else "↘️" if trend["trend"] == "down" else "→"
                report_lines.append(f"Best Price: {trend_symbol} ${trend['change']:+.2f} ({trend['change_percent']:+.1f}%)")
                report_lines.append(f"  From: ${trend['first_price']:.2f} → To: ${trend['last_price']:.2f}")
                report_lines.append("")
            
            # Show vendor-specific trends
            for vendor, change in analysis["price_changes"].items():
                trend_symbol = "↗️" if change["trend"] == "up" else "↘️" if change["trend"] == "down" else "→"
                report_lines.append(f"  {vendor}: {trend_symbol} ${change['change']:+.2f} ({change['change_percent']:+.1f}%)")
                report_lines.append(f"    From: ${change['first_price']:.2f} → To: ${change['last_price']:.2f}")
            report_lines.append("")
        
        if not any_trends:
            report_lines.append("No trend data available for the selected period.")
        
        return "\n".join(report_lines)
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Remove price data older than specified days.
        
        Args:
            days_to_keep: Number of days of data to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        for card_key in list(self.history.keys()):
            original_count = len(self.history[card_key])
            self.history[card_key] = [
                entry for entry in self.history[card_key]
                if datetime.fromisoformat(entry["timestamp"]) >= cutoff_date
            ]
            removed_count += original_count - len(self.history[card_key])
            
            # Remove card if no entries remain
            if not self.history[card_key]:
                del self.history[card_key]
        
        if removed_count > 0:
            self._save_history()
            logger.info(f"Cleaned up {removed_count} old price entries")
    
    def get_statistics(self) -> Dict:
        """Get statistics about the price history database.
        
        Returns:
            Dictionary with statistics
        """
        total_cards = len(self.history)
        total_entries = sum(len(entries) for entries in self.history.values())
        
        if total_entries == 0:
            return {
                "total_cards": 0,
                "total_entries": 0,
                "oldest_entry": None,
                "newest_entry": None,
                "average_entries_per_card": 0
            }
        
        # Find oldest and newest entries
        all_timestamps = []
        for entries in self.history.values():
            all_timestamps.extend([entry["timestamp"] for entry in entries])
        
        oldest_entry = min(all_timestamps)
        newest_entry = max(all_timestamps)
        
        return {
            "total_cards": total_cards,
            "total_entries": total_entries,
            "oldest_entry": oldest_entry,
            "newest_entry": newest_entry,
            "average_entries_per_card": total_entries / total_cards if total_cards > 0 else 0
        } 