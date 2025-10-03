from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum


class QualityRating(Enum):
    """Data quality classification per constitution requirements."""
    OK = "OK"      # Data successfully normalized with known units
    WARN = "WARN"  # Data extracted but units unknown or questionable
    RAW = "RAW"    # Data extracted as-is without normalization


@dataclass
class MaterialData:
    """Normalized information about a 3D printing material."""

    material_name: str
    brand: Optional[str]
    properties: Dict[str, Any]
    original_values: Dict[str, Any]
    normalized_values: Dict[str, Dict[str, Any]]  # {property: {value: X, unit: Y}}
    quality_rating: QualityRating
    source_file_hash: str
    sheet_position: Optional[str] = None  # e.g., "Sheet1!A1:C10"

    def __post_init__(self):
        """Convert string quality rating to enum if necessary."""
        if isinstance(self.quality_rating, str):
            self.quality_rating = QualityRating(self.quality_rating)

    def validate(self) -> bool:
        """Validate required fields per constitutional requirements."""
        required_fields = [
            self.material_name, self.properties, self.original_values,
            self.normalized_values, self.source_file_hash
        ]
        return all(field is not None for field in required_fields)

    def add_property(self, name: str, original_value: Any, normalized_value: Any = None,
                    unit: Optional[str] = None):
        """Add a material property with both original and normalized values."""
        self.properties[name] = normalized_value if normalized_value is not None else original_value
        self.original_values[name] = original_value

        if normalized_value is not None and unit is not None:
            self.normalized_values[name] = {
                "value": normalized_value,
                "unit": unit
            }

    def get_property_value(self, name: str, prefer_normalized: bool = True) -> Any:
        """Get property value, preferring normalized over original if available."""
        if prefer_normalized and name in self.normalized_values:
            return self.normalized_values[name]["value"]
        return self.properties.get(name) or self.original_values.get(name)

    def get_property_unit(self, name: str) -> Optional[str]:
        """Get the unit for a normalized property."""
        if name in self.normalized_values:
            return self.normalized_values[name].get("unit")
        return None

    def is_normalized_property(self, name: str) -> bool:
        """Check if a property has been successfully normalized."""
        return name in self.normalized_values

    @classmethod
    def create_raw(cls, material_name: str, source_file_hash: str,
                   properties: Dict[str, Any]) -> 'MaterialData':
        """Create MaterialData with RAW quality rating for failed normalization."""
        return cls(
            material_name=material_name,
            brand=None,
            properties=properties,
            original_values=properties.copy(),
            normalized_values={},
            quality_rating=QualityRating.RAW,
            source_file_hash=source_file_hash
        )

    @classmethod
    def create_normalized(cls, material_name: str, source_file_hash: str,
                         properties: Dict[str, Any], quality: QualityRating,
                         brand: Optional[str] = None) -> 'MaterialData':
        """Create MaterialData with normalized properties and specified quality rating."""
        # Separate normalized values from properties dict
        normalized_values = {}
        original_values = {}
        simple_properties = {}

        for prop_name, prop_data in properties.items():
            if isinstance(prop_data, dict) and "value" in prop_data:
                # This is a normalized property with value/unit structure
                normalized_values[prop_name] = prop_data
                simple_properties[prop_name] = prop_data["value"]
                original_values[prop_name] = prop_data.get("original_value", prop_data["value"])
            else:
                # Simple property value
                simple_properties[prop_name] = prop_data
                original_values[prop_name] = prop_data

        return cls(
            material_name=material_name,
            brand=brand,
            properties=simple_properties,
            original_values=original_values,
            normalized_values=normalized_values,
            quality_rating=quality,
            source_file_hash=source_file_hash
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert MaterialData to dictionary for JSON serialization."""
        return {
            "material_name": self.material_name,
            "brand": self.brand,
            "properties": self.properties,
            "original_values": self.original_values,
            "normalized_values": self.normalized_values,
            "quality_rating": self.quality_rating.value,
            "source_file_hash": self.source_file_hash,
            "sheet_position": self.sheet_position
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialData':
        """Create MaterialData from dictionary (for deserialization)."""
        return cls(
            material_name=data["material_name"],
            brand=data.get("brand"),
            properties=data["properties"],
            original_values=data["original_values"],
            normalized_values=data["normalized_values"],
            quality_rating=QualityRating(data["quality_rating"]),
            source_file_hash=data["source_file_hash"],
            sheet_position=data.get("sheet_position")
        )

    def __str__(self) -> str:
        return f"MaterialData(name='{self.material_name}', quality={self.quality_rating.value}, props={len(self.properties)})"
