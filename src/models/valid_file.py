from dataclasses import dataclass
from typing import Optional
import hashlib
import os
from datetime import datetime


@dataclass
class ValidFile:
    """Represents a downloaded spreadsheet file from a post."""

    filename: str
    file_type: str  # .xlsx, .xls, or .csv
    sha256_hash: Optional[str]
    file_path: str
    download_timestamp: str
    source_post_url: str
    file_size: int  # Changed from file_size_bytes to match ParserService
    url: str  # Added original download URL

    def __post_init__(self):
        """Validate file type and calculate hash if not provided."""
        self._validate_file_type()
        if self.sha256_hash is None and os.path.exists(self.file_path):
            self.sha256_hash = self._calculate_file_hash()

    def _validate_file_type(self):
        """Validate that file type is one of the allowed spreadsheet formats."""
        valid_types = {'.xlsx', '.xls', '.csv'}
        if self.file_type not in valid_types:
            raise ValueError(f"Invalid file type '{self.file_type}'. Must be one of: {valid_types}")

    def _calculate_file_hash(self) -> str:
        """Calculate SHA-256 hash of file content for deduplication."""
        hash_obj = hashlib.sha256()
        try:
            with open(self.file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except (FileNotFoundError, IOError):
            return ""

    @classmethod
    def from_download(cls, url: str, filename: str, content: bytes, source_post_url: str) -> 'ValidFile':
        """Create ValidFile from downloaded content."""
        # Determine file type from filename
        file_type = os.path.splitext(filename)[1].lower()

        # Calculate hash from content
        file_hash = hashlib.sha256(content).hexdigest()

        # Generate storage path in data/raw directory
        storage_dir = "data/raw"
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, f"{file_hash}_{filename}")

        # Save file to disk
        with open(file_path, 'wb') as f:
            f.write(content)

        return cls(
            filename=filename,
            file_type=file_type,
            sha256_hash=file_hash,
            file_path=file_path,
            download_timestamp=datetime.utcnow().isoformat() + "Z",
            source_post_url=source_post_url,
            file_size=len(content),
            url=url
        )

    def validate(self) -> bool:
        """Validate required fields and file existence."""
        required_fields = [
            self.filename, self.file_type, self.file_path,
            self.download_timestamp, self.source_post_url
        ]
        fields_valid = all(field is not None and field != "" for field in required_fields)
        file_exists = os.path.exists(self.file_path) if self.file_path else False
        return fields_valid and file_exists and self.file_size > 0

    def is_duplicate(self, other: 'ValidFile') -> bool:
        """Check if this file is a duplicate of another based on hash."""
        return (self.sha256_hash is not None and
                other.sha256_hash is not None and
                self.sha256_hash == other.sha256_hash)

    def __str__(self) -> str:
        return f"ValidFile(filename='{self.filename}', type='{self.file_type}', hash='{self.sha256_hash[:8]}...')"
