"""Card collection management module."""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Type
from enum import Enum

from .models import (
    Card,
    Rarity,
    FoilTreatment,
    PromoType,
    ArtworkVariant,
    BorderTreatment,
    CardSize,
    Language,
    Condition,
    Edition,
)

logger = logging.getLogger(__name__)


class CardManager:
    """Manages card collection data stored in CSV format."""

    def __init__(self, csv_path: str = "collection.csv"):
        """Initialize the card manager with a CSV file path."""
        self.csv_path = Path(csv_path)
        self._ensure_csv_exists()

    def _ensure_csv_exists(self) -> None:
        """Create the CSV file with headers if it doesn't exist."""
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "Card Name",
                        "Set",
                        "Set Code",
                        "Scryfall ID",
                        "Card Number",
                        "Rarity",
                        "Quantity",
                        "Foil Treatment",
                        "Condition",
                        "Promo Type",
                        "Artwork Variant",
                        "Border Treatment",
                        "Card Size",
                        "Language",
                        "Edition",
                        "Signed",
                        "Original Printing",
                        "Stamp",
                        "Serialized Number",
                        "Is Token",
                        "Is Emblem",
                        "Is Other",
                    ]
                )
            logger.info(f"Created new collection file: {self.csv_path}")

    def _parse_enum_field(self, value: str, enum_class: Type[Enum]) -> Optional[Enum]:
        """Parse an enum field from CSV string."""
        if not value or value.strip() == "":
            return None
        try:
            return enum_class(value.strip())
        except ValueError:
            logger.warning(f"Invalid {enum_class.__name__} value: {value}")
            return None

    def _parse_bool_field(self, value: str) -> bool:
        """Parse a boolean field from CSV string."""
        return value.lower().strip() in ("yes", "true", "1", "signed", "original")

    def load_collection(self) -> List[Card]:
        """Load the card collection from CSV file."""
        cards = []

        try:
            with open(self.csv_path, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                # Handle legacy CSV format (backward compatibility)
                is_legacy_format = (
                    "Foil" in reader.fieldnames
                    and "Foil Treatment" not in reader.fieldnames
                )

                for row in reader:
                    try:
                        if is_legacy_format:
                            # Legacy format: Card Name, Set, Quantity, Foil
                            card = Card(
                                name=row["Card Name"].strip(),
                                set_name=row["Set"].strip(),
                                quantity=int(row["Quantity"]),
                                foil=self._parse_bool_field(row["Foil"]),
                            )
                        else:
                            # New comprehensive format
                            card = Card(
                                name=row["Card Name"].strip(),
                                set_name=row["Set"].strip(),
                                set_code=row.get("Set Code", "").strip() or None,
                                scryfall_id=row.get("Scryfall ID", "").strip() or None,
                                card_number=row.get("Card Number", "").strip() or None,
                                rarity=self._parse_enum_field(
                                    row.get("Rarity", ""), Rarity
                                ),
                                quantity=int(row["Quantity"]),
                                foil_treatment=self._parse_enum_field(
                                    row.get("Foil Treatment", "Non-foil"), FoilTreatment
                                )
                                or FoilTreatment.NONFOIL,
                                condition=self._parse_enum_field(
                                    row.get("Condition", "Near Mint"), Condition
                                )
                                or Condition.NM,
                                promo_type=self._parse_enum_field(
                                    row.get("Promo Type", "Regular"), PromoType
                                )
                                or PromoType.REGULAR,
                                artwork_variant=self._parse_enum_field(
                                    row.get("Artwork Variant", "Normal"), ArtworkVariant
                                )
                                or ArtworkVariant.NORMAL,
                                border_treatment=self._parse_enum_field(
                                    row.get("Border Treatment", "Normal"),
                                    BorderTreatment,
                                )
                                or BorderTreatment.NORMAL,
                                card_size=self._parse_enum_field(
                                    row.get("Card Size", "Normal"), CardSize
                                )
                                or CardSize.NORMAL,
                                language=self._parse_enum_field(
                                    row.get("Language", "English"), Language
                                )
                                or Language.ENGLISH,
                                edition=self._parse_enum_field(
                                    row.get("Edition", ""), Edition
                                ),
                                signed=self._parse_bool_field(row.get("Signed", "No")),
                                original_printing=self._parse_bool_field(
                                    row.get("Original Printing", "Yes")
                                ),
                                stamp=row.get("Stamp", "").strip() or None,
                                serialized_number=row.get(
                                    "Serialized Number", ""
                                ).strip()
                                or None,
                                is_token=self._parse_bool_field(
                                    row.get("Is Token", "No")
                                ),
                                is_emblem=self._parse_bool_field(
                                    row.get("Is Emblem", "No")
                                ),
                                is_other=self._parse_bool_field(
                                    row.get("Is Other", "No")
                                ),
                            )
                        cards.append(card)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid row: {row} - {e}")
                        continue

            logger.info(f"Loaded {len(cards)} cards from collection")
            return cards

        except FileNotFoundError:
            logger.warning(f"Collection file not found: {self.csv_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading collection: {e}")
            return []

    def save_collection(self, cards: List[Card]) -> bool:
        """Save the card collection to CSV file."""
        try:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "Card Name",
                        "Set",
                        "Set Code",
                        "Scryfall ID",
                        "Card Number",
                        "Rarity",
                        "Quantity",
                        "Foil Treatment",
                        "Condition",
                        "Promo Type",
                        "Artwork Variant",
                        "Border Treatment",
                        "Card Size",
                        "Language",
                        "Edition",
                        "Signed",
                        "Original Printing",
                        "Stamp",
                        "Serialized Number",
                        "Is Token",
                        "Is Emblem",
                        "Is Other",
                    ]
                )

                for card in cards:
                    writer.writerow(
                        [
                            card.name,
                            card.set_name,
                            card.set_code or "",
                            card.scryfall_id or "",
                            card.card_number or "",
                            card.rarity.value if card.rarity else "",
                            card.quantity,
                            card.foil_treatment.value,
                            card.condition.value,
                            card.promo_type.value,
                            card.artwork_variant.value,
                            card.border_treatment.value,
                            card.card_size.value,
                            card.language.value,
                            card.edition.value if card.edition else "",
                            "Yes" if card.signed else "No",
                            "Yes" if card.original_printing else "No",
                            card.stamp or "",
                            card.serialized_number or "",
                            "Yes" if card.is_token else "No",
                            "Yes" if card.is_emblem else "No",
                            "Yes" if card.is_other else "No",
                        ]
                    )

            logger.info(f"Saved {len(cards)} cards to collection")
            return True

        except Exception as e:
            logger.error(f"Error saving collection: {e}")
            return False

    def add_card(self, card: Card) -> bool:
        """Add a card to the collection."""
        cards = self.load_collection()

        # Check if card already exists using unique key
        card_key = card.get_unique_key()
        for existing_card in cards:
            if existing_card.get_unique_key() == card_key:
                # Update quantity
                existing_card.quantity += card.quantity
                logger.info(
                    f"Updated quantity for {card.name} ({card.set_name}) to {existing_card.quantity}"
                )
                return self.save_collection(cards)

        # Add new card
        cards.append(card)
        logger.info(
            f"Added {card.quantity}x {card.name} ({card.set_name}) to collection"
        )
        return self.save_collection(cards)

    def remove_card(
        self,
        name: str,
        set_name: str,
        foil: bool = False,
        quantity: Optional[int] = None,
        **kwargs,
    ) -> bool:
        """Remove a card from the collection."""
        cards = self.load_collection()
        original_count = len(cards)

        # Build search criteria
        search_criteria = {
            "name": name,
            "set_name": set_name,
            "foil_treatment": FoilTreatment.FOIL if foil else FoilTreatment.NONFOIL,
        }

        # Add additional search criteria if provided
        for key, value in kwargs.items():
            if hasattr(Card, key):
                search_criteria[key] = value

        # Find and remove the card
        for i, card in enumerate(cards):
            if all(
                getattr(card, key) == value for key, value in search_criteria.items()
            ):

                if quantity is None or quantity >= card.quantity:
                    # Remove entire card
                    removed_card = cards.pop(i)
                    logger.info(
                        f"Removed {removed_card.quantity}x {removed_card.name} ({removed_card.set_name}) from collection"
                    )
                else:
                    # Reduce quantity
                    cards[i].quantity -= quantity
                    logger.info(
                        f"Reduced quantity for {card.name} ({card.set_name}) by {quantity}"
                    )

                return self.save_collection(cards)

        logger.warning(f"Card not found: {name} ({set_name})")
        return False

    def list_cards(self) -> List[Card]:
        """Get all cards in the collection."""
        return self.load_collection()

    def search_cards(self, name: str = "", set_name: str = "", **kwargs) -> List[Card]:
        """Search for cards by various criteria."""
        cards = self.load_collection()
        results = []

        name_lower = name.lower()
        set_lower = set_name.lower()

        for card in cards:
            # Check name and set name
            if name_lower and name_lower not in card.name.lower():
                continue
            if set_lower and set_lower not in card.set_name.lower():
                continue

            # Check additional criteria
            match = True
            for key, value in kwargs.items():
                if hasattr(card, key):
                    card_value = getattr(card, key)
                    if isinstance(value, str):
                        if value.lower() not in str(card_value).lower():
                            match = False
                            break
                    elif card_value != value:
                        match = False
                        break
                else:
                    match = False
                    break

            if match:
                results.append(card)

        return results

    def get_collection_stats(self) -> dict:
        """Get statistics about the collection."""
        cards = self.load_collection()

        total_cards = sum(card.quantity for card in cards)
        unique_cards = len(cards)
        foil_cards = sum(1 for card in cards if card.is_foil())
        non_foil_cards = unique_cards - foil_cards

        # Count by rarity
        rarity_counts = {}
        for card in cards:
            if card.rarity:
                rarity_counts[card.rarity.value] = (
                    rarity_counts.get(card.rarity.value, 0) + 1
                )

        # Count by set
        set_counts = {}
        for card in cards:
            set_counts[card.set_name] = set_counts.get(card.set_name, 0) + 1

        # Count by condition
        condition_counts = {}
        for card in cards:
            condition_counts[card.condition.value] = (
                condition_counts.get(card.condition.value, 0) + 1
            )

        return {
            "total_cards": total_cards,
            "unique_cards": unique_cards,
            "foil_cards": foil_cards,
            "non_foil_cards": non_foil_cards,
            "sets": len(set_counts),
            "rarity_breakdown": rarity_counts,
            "set_breakdown": set_counts,
            "condition_breakdown": condition_counts,
        }
