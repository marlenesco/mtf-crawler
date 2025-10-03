import pytest
from unittest.mock import Mock, patch, mock_open
import json
from src.services.storage_service import StorageService
from src.models.post import Post
from src.models.valid_file import ValidFile
from src.models.material_data import MaterialData
from src.models.json_data import JSONData


class TestStorageService:
    """Contract tests for StorageService per constitutional requirements."""

    def setup_method(self):
        self.storage_service = StorageService()
        self.sample_post = Post(
            url="https://www.mytechfun.com/videos/material_test/sample",
            title="Test Material Analysis",
            cleaned_text="Cleaned post content",
            youtube_link="https://youtube.com/watch?v=test123",
            manufacturer_links=["https://manufacturer.com"],
            download_timestamp="2025-10-03T10:00:00Z",
            post_hash="abc123def456"
        )
        self.sample_files = [
            ValidFile(
                filename="test_data.xlsx",
                file_type=".xlsx",
                sha256_hash="file123hash",
                file_path="data/raw/abc123def456/file123hash.xlsx",
                download_timestamp="2025-10-03T10:01:00Z",
                source_post_url="https://www.mytechfun.com/videos/material_test/sample",
                file_size_bytes=2048
            )
        ]
        self.sample_materials = [
            MaterialData(
                material_name="PLA",
                brand="Test Brand",
                properties={"print_temperature": 200, "bed_temperature": 60},
                original_values={"Print Temp": "200°C", "Bed Temp": "60°C"},
                normalized_values={"print_temperature": {"value": 200, "unit": "C"}},
                quality_rating="OK",
                source_file_hash="file123hash",
                sheet_position="Sheet1!A1:C10"
            )
        ]

    def test_save_json_returns_json_data_object(self):
        """Test that save_json returns a JSONData object with complete structure."""
        # This test MUST FAIL initially - no implementation exists yet
        result = self.storage_service.save_json(
            self.sample_post,
            self.sample_files,
            self.sample_materials
        )

        assert isinstance(result, JSONData)
        assert result.post is not None
        assert result.files is not None
        assert result.materials is not None
        assert result.provenance is not None
        assert result.constitution_compliance is not None

    def test_includes_cc_by_40_attribution(self):
        """Test that CC BY 4.0 attribution is included per constitution."""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                result = self.storage_service.save_json(
                    self.sample_post,
                    self.sample_files,
                    self.sample_materials
                )

                # Check that constitutional compliance includes proper attribution
                assert "Data © MyTechFun – Dr. Igor Gaspar, CC BY 4.0" in str(result.constitution_compliance)

                # Verify JSON was saved with attribution
                saved_data = mock_json_dump.call_args[0][0]
                assert "constitution_compliance" in saved_data
                assert "attribution" in saved_data["constitution_compliance"]

    def test_includes_complete_provenance_metadata(self):
        """Test that complete provenance information is included for audit trail."""
        with patch('builtins.open', mock_open()):
            with patch('json.dump') as mock_json_dump:
                result = self.storage_service.save_json(
                    self.sample_post,
                    self.sample_files,
                    self.sample_materials
                )

                # Check provenance fields
                assert result.provenance.source_url is not None
                assert result.provenance.extraction_timestamp is not None
                assert result.provenance.storage_key is not None

                # Verify saved JSON includes all provenance
                saved_data = mock_json_dump.call_args[0][0]
                provenance = saved_data["provenance"]
                required_fields = ["source_url", "extraction_timestamp", "storage_key"]
                for field in required_fields:
                    assert field in provenance

    def test_generates_unique_storage_key(self):
        """Test that each dataset gets a unique storage key."""
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                result1 = self.storage_service.save_json(
                    self.sample_post, self.sample_files, self.sample_materials
                )

                # Create slightly different post
                different_post = Post(**{**self.sample_post.__dict__, "title": "Different Title"})
                result2 = self.storage_service.save_json(
                    different_post, self.sample_files, self.sample_materials
                )

                # Storage keys should be different
                assert result1.provenance.storage_key != result2.provenance.storage_key

    def test_saves_json_to_correct_file_path(self):
        """Test that JSON is saved to data/processed/{post_hash}.json."""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump'):
                self.storage_service.save_json(
                    self.sample_post,
                    self.sample_files,
                    self.sample_materials
                )

                # Verify file is opened with correct path
                expected_path = f"data/processed/{self.sample_post.post_hash}.json"
                mock_file.assert_called_with(expected_path, 'w', encoding='utf-8')

    def test_validates_required_constitutional_fields(self):
        """Test that missing constitutional fields raise ValidationError."""
        # Create post missing required fields
        incomplete_post = Post(
            url=None,  # Missing required field
            title="Test",
            cleaned_text="Content",
            youtube_link="",
            manufacturer_links=[],
            download_timestamp="",
            post_hash=""
        )

        with pytest.raises(Exception) as exc_info:
            self.storage_service.save_json(
                incomplete_post,
                self.sample_files,
                self.sample_materials
            )

        assert "validation" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_is_idempotent_safe_to_rerun(self):
        """Test that saving the same data multiple times is safe (idempotent)."""
        with patch('builtins.open', mock_open()):
            with patch('json.dump') as mock_json_dump:
                # Save same data twice
                result1 = self.storage_service.save_json(
                    self.sample_post, self.sample_files, self.sample_materials
                )
                result2 = self.storage_service.save_json(
                    self.sample_post, self.sample_files, self.sample_materials
                )

                # Results should be consistent (same storage key for same content)
                assert result1.provenance.storage_key == result2.provenance.storage_key

                # Should not cause errors when run multiple times
                assert mock_json_dump.call_count == 2

    def test_handles_serialization_failures_gracefully(self):
        """Test that serialization failures are handled with proper error logging."""
        # Create object that can't be serialized
        unserializable_material = MaterialData(
            material_name="Test",
            brand=lambda x: x,  # Function can't be JSON serialized
            properties={}, original_values={}, normalized_values={},
            quality_rating="OK", source_file_hash="", sheet_position=""
        )

        with patch('structlog.get_logger') as mock_logger:
            with pytest.raises(Exception):
                self.storage_service.save_json(
                    self.sample_post,
                    self.sample_files,
                    [unserializable_material]
                )

            # Should log the serialization error
            mock_logger.return_value.error.assert_called()

    def test_constitutional_compliance_structure_is_complete(self):
        """Test that constitutional compliance section has all required fields."""
        with patch('builtins.open', mock_open()):
            with patch('json.dump') as mock_json_dump:
                result = self.storage_service.save_json(
                    self.sample_post,
                    self.sample_files,
                    self.sample_materials
                )

                compliance = result.constitution_compliance
                required_compliance_fields = ["attribution", "source_link", "extraction_date"]

                for field in required_compliance_fields:
                    assert hasattr(compliance, field) or field in compliance
