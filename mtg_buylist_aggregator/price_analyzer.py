"""Price analysis and collection valuation module."""

import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .models import Card, CardPrices, CollectionSummary

logger = logging.getLogger(__name__)


class PriceAnalyzer:
    """Analyzes card prices and collection values."""

    def __init__(self):
        """Initialize the price analyzer."""
        pass

    def analyze_card_prices(self, card_prices: CardPrices) -> Dict[str, any]:
        """Analyze prices for a single card.

        Args:
            card_prices: CardPrices object with vendor prices

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "card_name": card_prices.card.name,
            "set_name": card_prices.card.set_name,
            "quantity": card_prices.card.quantity,
            "total_value": 0.0,
            "best_vendor": None,
            "best_price": 0.0,
            "price_spread": 0.0,
            "vendor_count": len(card_prices.prices),
            "prices_by_vendor": {},
        }

        if not card_prices.prices:
            return analysis

        # Calculate total value and collect prices
        prices = []
        for vendor, price_data_list in card_prices.prices.items():
            # price_data_list is now a list of PriceData objects
            for price_data in price_data_list:
                total_price = price_data.price * card_prices.card.quantity
                analysis["prices_by_vendor"][vendor] = {
                    "price_per_card": price_data.price,
                    "total_value": total_price,
                    "condition": price_data.condition,
                    "quantity_limit": price_data.quantity_limit,
                }
                prices.append(price_data.price)

        # Calculate statistics
        if prices:
            analysis["best_price"] = max(prices)
            analysis["worst_price"] = min(prices)
            analysis["price_spread"] = analysis["best_price"] - analysis["worst_price"]
            analysis["total_value"] = analysis["best_price"] * card_prices.card.quantity
            analysis["best_vendor"] = (
                card_prices.best_bid.vendor if card_prices.best_bid else None
            )

        return analysis

    def analyze_collection_prices(
        self, card_prices_list: List[CardPrices]
    ) -> CollectionSummary:
        """Analyze prices for an entire collection.

        Args:
            card_prices_list: List of CardPrices objects

        Returns:
            CollectionSummary with analysis results
        """
        logger.info(f"Analyzing prices for {len(card_prices_list)} cards")

        # Initialize summary
        summary = CollectionSummary(
            total_cards=len(card_prices_list),
            cards_with_prices=0,
            cards_without_prices=0,
        )

        # Track values by vendor
        vendor_totals = defaultdict(float)
        vendor_card_counts = defaultdict(int)

        # Analyze each card
        for card_prices in card_prices_list:
            if card_prices.prices:
                summary.cards_with_prices += 1

                # Add to vendor totals
                for vendor, price_data_list in card_prices.prices.items():
                    # price_data_list is now a list of PriceData objects
                    for price_data in price_data_list:
                        total_value = price_data.price * card_prices.card.quantity
                        vendor_totals[vendor] += total_value
                        vendor_card_counts[vendor] += 1
            else:
                summary.cards_without_prices += 1

        # Calculate summary statistics
        summary.total_value_by_vendor = dict(vendor_totals)

        if vendor_totals:
            summary.best_vendor = max(vendor_totals, key=vendor_totals.get)
            summary.best_total_value = vendor_totals[summary.best_vendor]

        logger.info(
            f"Analysis complete: {summary.cards_with_prices} cards with prices, "
            f"{summary.cards_without_prices} without prices"
        )

        return summary

    def find_best_vendor_per_card(
        self, card_prices_list: List[CardPrices]
    ) -> Dict[str, str]:
        """Find the best vendor for each card.

        Args:
            card_prices_list: List of CardPrices objects

        Returns:
            Dictionary mapping card names to best vendor names
        """
        best_vendors = {}

        for card_prices in card_prices_list:
            if card_prices.best_vendor:
                card_key = f"{card_prices.card.name} ({card_prices.card.set_name})"
                best_vendors[card_key] = card_prices.best_vendor

        return best_vendors

    def calculate_optimal_vendor_mix(
        self, card_prices_list: List[CardPrices]
    ) -> Dict[str, List[str]]:
        """Calculate the optimal mix of vendors to maximize total value.

        This is a simplified greedy algorithm. For more complex optimization,
        you might want to use linear programming.

        Args:
            card_prices_list: List of CardPrices objects

        Returns:
            Dictionary mapping vendor names to lists of card names
        """
        vendor_assignments = defaultdict(list)

        for card_prices in card_prices_list:
            if card_prices.best_vendor:
                card_key = f"{card_prices.card.name} ({card_prices.card.set_name})"
                vendor_assignments[card_prices.best_vendor].append(card_key)

        return dict(vendor_assignments)

    def generate_price_report(
        self, card_prices_list: List[CardPrices], summary: CollectionSummary
    ) -> str:
        """Generate a formatted price report.

        Args:
            card_prices_list: List of CardPrices objects
            summary: CollectionSummary object

        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("MTG BUYLIST PRICE REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Summary section
        report_lines.append("COLLECTION SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Cards: {summary.total_cards}")
        report_lines.append(f"Cards with Prices: {summary.cards_with_prices}")
        report_lines.append(f"Cards without Prices: {summary.cards_without_prices}")
        report_lines.append("")

        # Vendor totals
        report_lines.append("TOTAL VALUES BY VENDOR")
        report_lines.append("-" * 40)
        for vendor, total_value in sorted(
            summary.total_value_by_vendor.items(), key=lambda x: x[1], reverse=True
        ):
            report_lines.append(f"{vendor:<20} ${total_value:>10.2f}")
        report_lines.append("")

        if summary.best_vendor:
            report_lines.append(f"BEST OVERALL VENDOR: {summary.best_vendor}")
            report_lines.append(f"TOTAL VALUE: ${summary.best_total_value:.2f}")
            report_lines.append("")

        # Individual card details
        report_lines.append("INDIVIDUAL CARD PRICES")
        report_lines.append("-" * 40)

        for card_prices in card_prices_list:
            if card_prices.prices:
                card = card_prices.card
                report_lines.append(
                    f"\n{card.name} ({card.set_name}) - Qty: {card.quantity}"
                )

                # Sort vendors by price
                sorted_prices = sorted(
                    card_prices.prices.items(),
                    key=lambda x: max(pd.price for pd in x[1]) if x[1] else 0,
                    reverse=True,
                )

                for vendor, price_data_list in sorted_prices:
                    if price_data_list:
                        # Use the highest price from the list
                        price_data = max(price_data_list, key=lambda pd: pd.price)
                        total_value = price_data.price * card.quantity
                        report_lines.append(
                            f"  {vendor:<15} ${price_data.price:>6.2f} "
                            f"({price_data.condition}) = ${total_value:>8.2f}"
                        )
            else:
                card = card_prices.card
                report_lines.append(
                    f"\n{card.name} ({card.set_name}) - Qty: {card.quantity}"
                )
                report_lines.append("  No prices found")

        return "\n".join(report_lines)

    def export_to_csv(
        self, card_prices_list: List[CardPrices], filename: str = "price_report.csv"
    ) -> bool:
        """Export price data to CSV format.

        Args:
            card_prices_list: List of CardPrices objects
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        try:
            import csv

            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(
                    [
                        "Card Name",
                        "Set",
                        "Quantity",
                        "Vendor",
                        "Price",
                        "Condition",
                        "Total Value",
                        "Quantity Limit",
                    ]
                )

                # Write data
                for card_prices in card_prices_list:
                    card = card_prices.card

                    if card_prices.prices:
                        for vendor, price_data_list in card_prices.prices.items():
                            # price_data_list is now a list of PriceData objects
                            for price_data in price_data_list:
                                total_value = price_data.price * card.quantity
                                writer.writerow(
                                    [
                                        card.name,
                                        card.set_name,
                                        card.quantity,
                                        vendor,
                                        price_data.price,
                                        price_data.condition,
                                        total_value,
                                        price_data.quantity_limit or "",
                                    ]
                                )
                    else:
                        # Write row for cards without prices
                        writer.writerow(
                            [
                                card.name,
                                card.set_name,
                                card.quantity,
                                "No prices found",
                                "",
                                "",
                                "",
                                "",
                            ]
                        )

            logger.info(f"Price report exported to {filename}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
