from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import hashlib


@dataclass
class Provenance:
    """Provenance metadata for audit and traceability per constitutional requirements."""

    source_url: str
    download_timestamp: str
    storage_key: str
    sha256_hash: str
    file_count: int
    material_count: int
    sheet_position: Optional[str] = None  # e.g., "Sheet1!A1:C10" for Excel files

    def __post_init__(self):
        """Generate storage key if not provided."""
        if not self.storage_key:
            # Generate from URL and timestamp
            content = f"{self.source_url}|{self.download_timestamp}".encode('utf-8')
            self.storage_key = hashlib.sha256(content).hexdigest()[:16]

    def validate(self) -> bool:
        """Validate required provenance fields per constitutional requirements."""
        required_fields = [
            self.source_url, self.download_timestamp, self.storage_key,
            self.sha256_hash
        ]
        return all(field is not None and field != "" for field in required_fields)

    @classmethod
    def create_from_post(cls, post_url: str, post_hash: str, file_count: int,
                        material_count: int) -> 'Provenance':
        """Create Provenance from post data."""
        return cls(
            source_url=post_url,
            download_timestamp=datetime.utcnow().isoformat() + "Z",
            storage_key=post_hash[:16],  # Use first 16 chars of post hash
            sha256_hash=post_hash,
            file_count=file_count,
            material_count=material_count
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_url": self.source_url,
            "download_timestamp": self.download_timestamp,
            "storage_key": self.storage_key,
            "sha256_hash": self.sha256_hash,
            "file_count": self.file_count,
            "material_count": self.material_count,
            "sheet_position": self.sheet_position
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Provenance':
        """Create from dictionary (for deserialization)."""
        return cls(
            source_url=data["source_url"],
            download_timestamp=data["download_timestamp"],
            storage_key=data["storage_key"],
            sha256_hash=data["sha256_hash"],
            file_count=data["file_count"],
            material_count=data["material_count"],
            sheet_position=data.get("sheet_position")
        )

    def __str__(self) -> str:
        return f"Provenance(source='{self.source_url}', key='{self.storage_key}', files={self.file_count}, materials={self.material_count})"
