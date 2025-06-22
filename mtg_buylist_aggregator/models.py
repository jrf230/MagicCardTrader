"""Data models for the MTG Buylist Aggregator."""

from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class Rarity(str, Enum):
    """Card rarity levels."""

    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    MYTHIC = "Mythic Rare"
    SPECIAL = "Special"
    BONUS = "Bonus"
    TIMESHIFTED = "Timeshifted"
    MASTERPIECE = "Masterpiece"


class FoilTreatment(str, Enum):
    """Foil treatment types."""

    NONFOIL = "Non-foil"
    FOIL = "Foil"
    ETCHED_FOIL = "Etched Foil"
    GALAXY_FOIL = "Galaxy Foil"
    RAINBOW_FOIL = "Rainbow Foil"
    PRISMARIC_FOIL = "Prismaric Foil"
    SURGE_FOIL = "Surge Foil"
    STEP_AND_COMPLEAT_FOIL = "Step and Compleat Foil"


class PromoType(str, Enum):
    """Promo card types."""

    REGULAR = "Regular"
    PROMO = "Promo"
    PRERELEASE = "Prerelease"
    RELEASE = "Release"
    BUY_A_BOX = "Buy-a-Box"
    CONVENTION = "Convention"
    GAME_DAY = "Game Day"
    FNM = "Friday Night Magic"
    JUDGE = "Judge"
    MEDIA_INSERTS = "Media Inserts"
    BUNDLE = "Bundle"
    BOX_TOPPER = "Box Topper"
    SECRET_LAIR = "Secret Lair"


class ArtworkVariant(str, Enum):
    """Artwork variant types."""

    NORMAL = "Normal"
    ALTERNATE_ART = "Alternate Art"
    SHOWCASE = "Showcase"
    STYLIZED = "Stylized"
    PHYREXIAN = "Phyrexian"
    PLANESWALKER_DECK = "Planeswalker Deck"
    BUNDLE = "Bundle"
    BOX_TOPPER = "Box Topper"
    SECRET_LAIR = "Secret Lair"
    CONVENTION = "Convention"
    JUDGE = "Judge"


class BorderTreatment(str, Enum):
    """Border treatment types."""

    NORMAL = "Normal"
    BORDERLESS = "Borderless"
    FULL_ART = "Full Art"
    TEXTURED = "Textured"
    EMBOSSED = "Embossed"


class CardSize(str, Enum):
    """Card size types."""

    NORMAL = "Normal"
    OVERSIZED = "Oversized"
    MINI = "Mini"


class Language(str, Enum):
    """Card language."""

    ENGLISH = "English"
    JAPANESE = "Japanese"
    CHINESE_SIMPLIFIED = "Chinese Simplified"
    CHINESE_TRADITIONAL = "Chinese Traditional"
    KOREAN = "Korean"
    RUSSIAN = "Russian"
    SPANISH = "Spanish"
    FRENCH = "French"
    GERMAN = "German"
    ITALIAN = "Italian"
    PORTUGUESE = "Portuguese"


class Condition(str, Enum):
    """Card condition."""

    NM = "Near Mint"
    EX = "Excellent"
    GD = "Good"
    LP = "Light Played"
    PL = "Played"
    PO = "Poor"


class Edition(str, Enum):
    """Card edition."""

    UNLIMITED = "Unlimited"
    FIRST_EDITION = "1st Edition"
    SECOND_EDITION = "2nd Edition"
    REVISED = "Revised"
    FOURTH_EDITION = "4th Edition"
    FIFTH_EDITION = "5th Edition"
    SIXTH_EDITION = "6th Edition"
    SEVENTH_EDITION = "7th Edition"
    EIGHTH_EDITION = "8th Edition"
    NINTH_EDITION = "9th Edition"
    TENTH_EDITION = "10th Edition"


class Card(BaseModel):
    """Represents a Magic: The Gathering card in a collection."""

    # Core identification
    name: str = Field(..., description="The name of the card")
    set_name: str = Field(..., description="The set the card is from")
    card_number: Optional[str] = Field(
        None, description="The collector number within the set"
    )
    rarity: Optional[Rarity] = Field(None, description="The rarity of the card")

    # Physical characteristics
    quantity: int = Field(..., ge=1, description="Number of copies owned")
    foil_treatment: FoilTreatment = Field(
        default=FoilTreatment.NONFOIL, description="Foil treatment type"
    )
    condition: Condition = Field(default=Condition.NM, description="Card condition")

    # Variant characteristics
    promo_type: PromoType = Field(
        default=PromoType.REGULAR, description="Promo card type"
    )
    artwork_variant: ArtworkVariant = Field(
        default=ArtworkVariant.NORMAL, description="Artwork variant type"
    )
    border_treatment: BorderTreatment = Field(
        default=BorderTreatment.NORMAL, description="Border treatment type"
    )
    card_size: CardSize = Field(default=CardSize.NORMAL, description="Card size type")

    # Additional characteristics
    language: Language = Field(default=Language.ENGLISH, description="Card language")
    edition: Optional[Edition] = Field(None, description="Card edition")
    signed: bool = Field(
        default=False, description="Whether the card is signed by the artist"
    )
    original_printing: bool = Field(
        default=True, description="Whether this is the original printing (vs reprint)"
    )
    stamp: Optional[str] = Field(
        None, description="Special stamp or mark (e.g., Planeswalker, Arena)"
    )
    serialized_number: Optional[str] = Field(
        None, description="Serialized number for special cards (e.g., 1/500)"
    )
    is_token: bool = Field(default=False, description="Is this a token?")
    is_emblem: bool = Field(default=False, description="Is this an emblem?")
    is_other: bool = Field(
        default=False, description="Is this a non-standard card (e.g., box topper)?"
    )

    # Legacy support - deprecated fields
    foil: bool = Field(
        default=False, description="Legacy foil field - use foil_treatment instead"
    )

    # New fields
    set_code: Optional[str] = Field(None, description="Short set code (e.g., C21)")
    scryfall_id: Optional[str] = Field(None, description="Scryfall UUID for the card")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sol Ring",
                "set_name": "Commander 2021",
                "set_code": "C21",
                "scryfall_id": "00000000-0000-0000-0000-000000000000",
                "card_number": "1",
                "rarity": "Uncommon",
                "quantity": 1,
                "foil_treatment": "Non-foil",
                "condition": "Near Mint",
                "promo_type": "Regular",
                "artwork_variant": "Normal",
                "border_treatment": "Normal",
                "card_size": "Normal",
                "language": "English",
                "signed": False,
                "original_printing": True,
                "stamp": None,
                "serialized_number": None,
                "is_token": False,
                "is_emblem": False,
                "is_other": False,
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        # Legacy support: sync foil field with foil_treatment
        if (
            "foil" in data
            and data["foil"]
            and self.foil_treatment == FoilTreatment.NONFOIL
        ):
            self.foil_treatment = FoilTreatment.FOIL
        elif self.foil_treatment != FoilTreatment.NONFOIL:
            self.foil = True

    def get_unique_key(self) -> str:
        """Generate a unique key for this card variant."""
        components = [
            self.name,
            self.set_name,
            self.set_code or "",
            self.scryfall_id or "",
            self.card_number or "",
            self.foil_treatment.value,
            self.promo_type.value,
            self.artwork_variant.value,
            self.border_treatment.value,
            self.card_size.value,
            self.language.value,
            self.edition.value if self.edition else "",
            "signed" if self.signed else "unsigned",
            "original" if self.original_printing else "reprint",
            self.stamp or "",
            self.serialized_number or "",
            "token" if self.is_token else "not_token",
            "emblem" if self.is_emblem else "not_emblem",
            "other" if self.is_other else "not_other",
        ]
        return "|".join(components)

    def is_foil(self) -> bool:
        """Check if the card has any foil treatment."""
        return self.foil_treatment != FoilTreatment.NONFOIL


class PriceData(BaseModel):
    """Represents a single price point for a card from a vendor."""

    vendor: str = Field(..., description="Name of the vendor")
    price: float = Field(..., ge=0, description="Price in USD")
    price_type: str = Field(
        ..., description="Type of price (e.g., 'bid_cash', 'offer_nm', 'offer_lp')"
    )
    condition: Condition = Field(
        default=Condition.NM, description="Card condition for this price"
    )
    quantity_limit: Optional[int] = Field(
        None, ge=0, description="Maximum quantity for this price point"
    )
    last_price_update: Optional[datetime] = Field(
        default_factory=datetime.now, description="When this price was last updated"
    )
    notes: Optional[str] = Field(None, description="Additional notes for this price")


class CardPrices(BaseModel):
    """Represents all price data for a single card, aggregating multiple vendors and price points."""

    card: Card = Field(..., description="The card")
    prices: Dict[str, List[PriceData]] = Field(
        default_factory=dict,
        description="Key: vendor name, Value: list of prices from that vendor",
    )
    best_bid: Optional[PriceData] = Field(
        None, description="The single best (highest) buylist/bid price"
    )
    best_offer: Optional[PriceData] = Field(
        None, description="The single best (lowest) retail/offer price"
    )

    def update_best_prices(self) -> None:
        """Iterate through all prices to find the best bid and best offer."""
        all_bids: List[PriceData] = []
        all_offers: List[PriceData] = []

        for vendor_prices in self.prices.values():
            for price_data in vendor_prices:
                if "bid" in price_data.price_type:
                    all_bids.append(price_data)
                elif "offer" in price_data.price_type:
                    all_offers.append(price_data)

        if all_bids:
            self.best_bid = max(all_bids, key=lambda p: p.price)
        else:
            self.best_bid = None

        if all_offers:
            self.best_offer = min(all_offers, key=lambda p: p.price)
        else:
            self.best_offer = None


class CollectionSummary(BaseModel):
    """Summary of a card collection with total values."""

    total_cards: int = Field(..., description="Total number of cards in collection")
    total_value_by_vendor: Dict[str, float] = Field(
        default_factory=dict, description="Total collection value by vendor"
    )
    best_total_value: Optional[float] = Field(None, description="Highest total value")
    best_vendor: Optional[str] = Field(
        None, description="Vendor with highest total value"
    )
    cards_with_prices: int = Field(..., description="Number of cards with price data")
    cards_without_prices: int = Field(
        ..., description="Number of cards without price data"
    )

    def calculate_totals(self, card_prices_list: list[CardPrices]) -> None:
        """Calculate total values from a list of card prices."""
        self.total_cards = len(card_prices_list)
        self.cards_with_prices = sum(1 for cp in card_prices_list if cp.prices)
        self.cards_without_prices = self.total_cards - self.cards_with_prices

        # Reset vendor totals
        self.total_value_by_vendor = {}

        # Calculate totals by vendor
        for card_prices in card_prices_list:
            for vendor, prices in card_prices.prices.items():
                if vendor not in self.total_value_by_vendor:
                    self.total_value_by_vendor[vendor] = 0.0
                for price_data in prices:
                    self.total_value_by_vendor[vendor] += (
                        price_data.price * card_prices.card.quantity
                    )

        # Find best vendor
        if self.total_value_by_vendor:
            self.best_vendor = max(
                self.total_value_by_vendor.keys(),
                key=lambda v: self.total_value_by_vendor[v],
            )
            self.best_total_value = self.total_value_by_vendor[self.best_vendor]
        else:
            self.best_vendor = None
            self.best_total_value = None
