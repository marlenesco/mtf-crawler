import json
import os
from typing import List
from datetime import datetime
import structlog
from models.post import Post
from models.valid_file import ValidFile
from models.material_data import MaterialData
from models.json_data import JSONData
from models.provenance import Provenance


class StorageService:
    """Service for saving collected data as structured JSON with full provenance per constitutional requirements."""

    def __init__(self):
        self.logger = structlog.get_logger("mtf_crawler.storage")
        self.output_dir = "data/processed"
        os.makedirs(self.output_dir, exist_ok=True)

    def save_json(self, post: Post, files: List[ValidFile], materials: List[MaterialData]) -> JSONData:
        """
        Save all collected data as structured JSON with full provenance.

        Args:
            post: Post object with extracted content
            files: List of ValidFile objects downloaded
            materials: List of MaterialData objects with normalized data

        Returns:
            JSONData object representing the complete dataset

        Raises:
            StorageError: When JSON serialization or file save fails
            ValidationError: When required constitutional fields are missing
        """
        self.logger.info("Saving JSON data",
                        post_url=post.url,
                        files_count=len(files),
                        materials_count=len(materials))

        try:
            # Validate inputs
            self._validate_inputs(post, files, materials)

            # Create complete JSONData object
            json_data = JSONData.create_complete(post, files, materials)

            # Validate constitutional compliance
            if not json_data.validate():
                raise ValidationError("JSONData failed constitutional validation")

            # Save to file
            output_path = self._save_to_file(json_data)

            self.logger.info("JSON data saved successfully",
                           output_path=output_path,
                           storage_key=json_data.provenance.storage_key)

            return json_data

        except Exception as e:
            self.logger.error("Failed to save JSON data",
                            post_url=post.url,
                            error=str(e))
            raise StorageError(f"Failed to save JSON data: {str(e)}")

    def _validate_inputs(self, post: Post, files: List[ValidFile], materials: List[MaterialData]):
        """Validate required constitutional fields in input objects."""
        # Validate Post
        if not post.validate():
            raise ValidationError("Post object missing required fields")

        # Validate ValidFiles
        for file in files:
            if not file.validate():
                raise ValidationError(f"ValidFile {file.filename} missing required fields")

        # Validate MaterialData
        for material in materials:
            if not material.validate():
                raise ValidationError(f"MaterialData {material.material_name} missing required fields")

        self.logger.debug("Input validation passed")

    def _save_to_file(self, json_data: JSONData) -> str:
        """Save JSONData to file with proper encoding and error handling."""
        # Generate output filename
        filename = f"{json_data.post.post_hash}.json"
        output_path = os.path.join(self.output_dir, filename)

        try:
            # Convert to dictionary for JSON serialization
            data_dict = json_data.to_dict()

            # Add title to main structure
            data_dict['title'] = json_data.post.title

            # Add metadata
            data_dict['_metadata'] = {
                'schema_version': '1.0.0',
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'generator': 'mtf-crawler/1.0.0',
                'constitutional_compliance_verified': True
            }

            # Add licensing information per constitution
            data_dict['_licensing'] = {
                'attribution': 'Data © MyTechFun – Dr. Igor Gaspar, CC BY 4.0',
                'license': 'CC BY 4.0',
                'source_url': json_data.post.url
            }

            # Save with proper formatting
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, sort_keys=True)

            self.logger.debug("File written successfully", path=output_path, size_bytes=os.path.getsize(output_path))
            return output_path

        except Exception as e:
            self.logger.error("File write failed", path=output_path, error=str(e))
            raise StorageError(f"Failed to write JSON file: {str(e)}")

    def load_json(self, storage_key: str) -> JSONData:
        """Load JSONData from file by storage key."""
        try:
            filename = f"{storage_key}.json"
            file_path = os.path.join(self.output_dir, filename)

            if not os.path.exists(file_path):
                raise StorageError(f"JSON file not found: {filename}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)

            # Remove metadata before deserializing
            data_dict.pop('_metadata', None)
            data_dict.pop('_licensing', None)

            json_data = JSONData.from_dict(data_dict)
            self.logger.debug("JSON data loaded", storage_key=storage_key)
            return json_data

        except Exception as e:
            self.logger.error("Failed to load JSON data", storage_key=storage_key, error=str(e))
            raise StorageError(f"Failed to load JSON data: {str(e)}")

    def list_stored_data(self) -> List[str]:
        """List all stored JSON files by their storage keys."""
        try:
            if not os.path.exists(self.output_dir):
                return []

            files = [f for f in os.listdir(self.output_dir) if f.endswith('.json')]
            storage_keys = [os.path.splitext(f)[0] for f in files]

            self.logger.debug("Listed stored data", count=len(storage_keys))
            return storage_keys

        except Exception as e:
            self.logger.error("Failed to list stored data", error=str(e))
            return []

    def delete_json(self, storage_key: str) -> bool:
        """Delete stored JSON data by storage key."""
        try:
            filename = f"{storage_key}.json"
            file_path = os.path.join(self.output_dir, filename)

            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info("JSON data deleted", storage_key=storage_key)
                return True
            else:
                self.logger.warning("JSON file not found for deletion", storage_key=storage_key)
                return False

        except Exception as e:
            self.logger.error("Failed to delete JSON data", storage_key=storage_key, error=str(e))
            raise StorageError(f"Failed to delete JSON data: {str(e)}")

    def get_storage_stats(self) -> dict:
        """Get statistics about stored data."""
        try:
            stats = {
                'total_files': 0,
                'total_size_bytes': 0,
                'oldest_file': None,
                'newest_file': None
            }

            if not os.path.exists(self.output_dir):
                return stats

            files = [f for f in os.listdir(self.output_dir) if f.endswith('.json')]
            stats['total_files'] = len(files)

            if files:
                file_paths = [os.path.join(self.output_dir, f) for f in files]
                stats['total_size_bytes'] = sum(os.path.getsize(p) for p in file_paths)

                # Find oldest and newest files
                file_times = [(p, os.path.getmtime(p)) for p in file_paths]
                file_times.sort(key=lambda x: x[1])

                stats['oldest_file'] = os.path.basename(file_times[0][0])
                stats['newest_file'] = os.path.basename(file_times[-1][0])

            return stats

        except Exception as e:
            self.logger.error("Failed to get storage stats", error=str(e))
            return {'error': str(e)}


class StorageError(Exception):
    """Exception raised when storage operations fail."""
    pass


class ValidationError(Exception):
    """Exception raised when data validation fails."""
    pass
