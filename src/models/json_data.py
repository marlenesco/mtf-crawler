from dataclasses import dataclass
from typing import List, Dict, Any
from .post import Post
from .valid_file import ValidFile
from .material_data import MaterialData
from .provenance import Provenance


@dataclass
class JSONData:
    """Final structured output for each post containing all relevant and normalized information."""

    post: Post
    files: List[ValidFile]
    materials: List[MaterialData]
    provenance: Provenance

    def validate(self) -> bool:
        """Validate complete JSONData structure per constitutional requirements."""
        # Validate core components
        if not self.post.validate():
            return False

        if not self.provenance.validate():
            return False

        # Validate all files
        for file in self.files:
            if not file.validate():
                return False

        # Validate all materials
        for material in self.materials:
            if not material.validate():
                return False

        # Check consistency between components
        if self.provenance.file_count != len(self.files):
            return False

        if self.provenance.material_count != len(self.materials):
            return False

        return True

    @classmethod
    def create_complete(cls, post: Post, files: List[ValidFile], materials: List[MaterialData]) -> 'JSONData':
        """Create complete JSONData from all components with provenance."""
        # Create provenance from post data
        provenance = Provenance.create_from_post(
            post_url=post.url,
            post_hash=post.post_hash,
            file_count=len(files),
            material_count=len(materials)
        )

        return cls(
            post=post,
            files=files,
            materials=materials,
            provenance=provenance
        )

    def get_materials_by_quality(self, quality: str) -> List[MaterialData]:
        """Get materials filtered by quality rating."""
        return [m for m in self.materials if m.quality_rating.value == quality]

    def get_files_by_type(self, file_type: str) -> List[ValidFile]:
        """Get files filtered by file type."""
        return [f for f in self.files if f.file_type == file_type]

    def has_youtube_review(self) -> bool:
        """Check if post has associated YouTube review link."""
        return self.post.youtube_link is not None and self.post.youtube_link != ""

    def get_manufacturer_links(self) -> List[str]:
        """Get all manufacturer links from the post."""
        return self.post.manufacturer_links

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about the data."""
        quality_counts = {}
        for material in self.materials:
            quality = material.quality_rating.value
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        file_type_counts = {}
        for file in self.files:
            file_type = file.file_type
            file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1

        return {
            "post_info": {
                "url": self.post.url,
                "title": self.post.title,
                "has_youtube": self.has_youtube_review(),
                "manufacturer_links_count": len(self.get_manufacturer_links())
            },
            "files": {
                "total_count": len(self.files),
                "by_type": file_type_counts,
                "total_size_bytes": sum(f.file_size for f in self.files)
            },
            "materials": {
                "total_count": len(self.materials),
                "by_quality": quality_counts,
                "normalized_properties_count": sum(len(m.normalized_values) for m in self.materials)
            },
            "provenance": {
                "storage_key": self.provenance.storage_key,
                "download_timestamp": self.provenance.download_timestamp,
                "sha256_hash": self.provenance.sha256_hash[:8] + "..."
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "post": {
                "url": self.post.url,
                "title": self.post.title,
                "cleaned_text": self.post.cleaned_text,
                "youtube_link": self.post.youtube_link,
                "manufacturer_links": self.post.manufacturer_links,
                "download_timestamp": self.post.download_timestamp,
                "post_hash": self.post.post_hash
            },
            "files": [
                {
                    "filename": f.filename,
                    "file_type": f.file_type,
                    "sha256_hash": f.sha256_hash,
                    "file_path": f.file_path,
                    "download_timestamp": f.download_timestamp,
                    "source_post_url": f.source_post_url,
                    "file_size": f.file_size,
                    "url": f.url
                }
                for f in self.files
            ],
            "materials": [material.to_dict() for material in self.materials],
            "provenance": self.provenance.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONData':
        """Create from dictionary (for deserialization)."""
        # Reconstruct Post
        post_data = data["post"]
        post = Post(
            url=post_data["url"],
            title=post_data["title"],
            cleaned_text=post_data["cleaned_text"],
            youtube_link=post_data.get("youtube_link"),
            manufacturer_links=post_data.get("manufacturer_links", []),
            download_timestamp=post_data["download_timestamp"],
            post_hash=post_data.get("post_hash")
        )

        # Reconstruct ValidFiles
        files = []
        for file_data in data.get("files", []):
            file = ValidFile(
                filename=file_data["filename"],
                file_type=file_data["file_type"],
                sha256_hash=file_data["sha256_hash"],
                file_path=file_data["file_path"],
                download_timestamp=file_data["download_timestamp"],
                source_post_url=file_data["source_post_url"],
                file_size=file_data["file_size"],
                url=file_data["url"]
            )
            files.append(file)

        # Reconstruct MaterialData
        materials = [MaterialData.from_dict(m) for m in data.get("materials", [])]

        # Reconstruct Provenance
        provenance = Provenance.from_dict(data["provenance"])

        return cls(
            post=post,
            files=files,
            materials=materials,
            provenance=provenance
        )

    def __str__(self) -> str:
        return f"JSONData(post='{self.post.title}', files={len(self.files)}, materials={len(self.materials)})"
