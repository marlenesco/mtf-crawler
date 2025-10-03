import pytest
from unittest.mock import Mock, patch, mock_open
import pandas as pd
from src.services.normalizer_service import NormalizerService
from src.models.valid_file import ValidFile
from src.models.material_data import MaterialData


class TestNormalizerService:
    """Contract tests for NormalizerService per constitutional requirements."""

    def setup_method(self):
        self.normalizer_service = NormalizerService()
        self.sample_xlsx_file = ValidFile(
            filename="test_data.xlsx",
            file_type=".xlsx",
            sha256_hash="abc123def456",
            file_path="data/raw/post123/abc123def456.xlsx",
            download_timestamp="2025-10-03T10:00:00Z",
            source_post_url="https://test.com/post",
            file_size_bytes=1024
        )

    def test_process_materials_returns_list_of_material_data(self):
        """Test that process_materials returns a list of MaterialData objects."""
        # This test MUST FAIL initially - no implementation exists yet
        materials = self.normalizer_service.process_materials([self.sample_xlsx_file])

        assert isinstance(materials, list)
        for material in materials:
            assert isinstance(material, MaterialData)
            assert material.material_name is not None
            assert material.quality_rating in ['OK', 'WARN', 'RAW']
            assert material.source_file_hash is not None

    def test_normalizes_units_to_si_where_possible(self):
        """Test that units are normalized to SI with original values preserved."""
        # Mock pandas read_excel to return test data with various units
        test_data = pd.DataFrame({
            'Material': ['PLA'],
            'Print Temperature': ['210°C'],
            'Bed Temperature': ['60 C'],
            'Print Speed': ['50 mm/s'],
            'Layer Height': ['0.2mm']
        })

        with patch('pandas.read_excel', return_value=test_data):
            materials = self.normalizer_service.process_materials([self.sample_xlsx_file])

            material = materials[0]
            # Should have both original and normalized values
            assert hasattr(material, 'original_values')
            assert hasattr(material, 'normalized_values')

            # Temperature should be normalized to Celsius
            if 'print_temperature' in material.normalized_values:
                assert material.normalized_values['print_temperature']['unit'] == 'C'

    def test_preserves_original_values_and_units(self):
        """Test that original values and units are preserved per constitution."""
        test_data = pd.DataFrame({
            'Material': ['PETG'],
            'Temp': ['230°F'],  # Fahrenheit - should preserve original
            'Speed': ['3000 mm/min']  # Non-standard unit
        })

        with patch('pandas.read_excel', return_value=test_data):
            materials = self.normalizer_service.process_materials([self.sample_xlsx_file])

            material = materials[0]
            assert material.original_values is not None
            # Original values should contain the raw extracted data
            assert '230°F' in str(material.original_values) or 'Temp' in material.original_values

    def test_classifies_data_quality_correctly(self):
        """Test that data quality is classified as OK, WARN, or RAW."""
        # Test with good data (should be OK)
        good_data = pd.DataFrame({
            'Material': ['PLA'],
            'Print Temperature': ['200°C'],
            'Print Speed': ['50 mm/s']
        })

        # Test with questionable data (should be WARN)
        warn_data = pd.DataFrame({
            'Material': ['Unknown'],
            'Temperature': ['Hot'],  # Non-numeric
            'Speed': ['Fast']  # Non-numeric
        })

        with patch('pandas.read_excel', side_effect=[good_data, warn_data]):
            good_materials = self.normalizer_service.process_materials([self.sample_xlsx_file])
            warn_materials = self.normalizer_service.process_materials([self.sample_xlsx_file])

            # Quality ratings should be assigned appropriately
            for material in good_materials + warn_materials:
                assert material.quality_rating in ['OK', 'WARN', 'RAW']

    def test_handles_multiple_materials_per_file(self):
        """Test that multiple materials in single file are separated correctly."""
        multi_material_data = pd.DataFrame({
            'Material': ['PLA', 'PETG', 'ABS'],
            'Print Temperature': ['200°C', '230°C', '250°C'],
            'Bed Temperature': ['60°C', '70°C', '100°C']
        })

        with patch('pandas.read_excel', return_value=multi_material_data):
            materials = self.normalizer_service.process_materials([self.sample_xlsx_file])

            # Should return 3 separate MaterialData objects
            assert len(materials) == 3
            material_names = {m.material_name for m in materials}
            assert 'PLA' in material_names
            assert 'PETG' in material_names
            assert 'ABS' in material_names

    def test_maintains_provenance_information(self):
        """Test that sheet/row/column positions are recorded for audit trail."""
        test_data = pd.DataFrame({
            'Material': ['TPU'],
            'Shore Hardness': ['85A']
        })

        with patch('pandas.read_excel', return_value=test_data):
            materials = self.normalizer_service.process_materials([self.sample_xlsx_file])

            material = materials[0]
            assert material.source_file_hash == self.sample_xlsx_file.sha256_hash
            assert material.sheet_position is not None  # Should record position info

    def test_handles_corrupted_files_gracefully(self):
        """Test that corrupted files are marked as RAW quality with error logging."""
        with patch('pandas.read_excel', side_effect=Exception("Corrupted file")):
            with patch('structlog.get_logger') as mock_logger:
                materials = self.normalizer_service.process_materials([self.sample_xlsx_file])

                # Should log error
                mock_logger.return_value.error.assert_called()

                # Should return RAW quality material if any fallback processing
                if materials:
                    assert all(m.quality_rating == 'RAW' for m in materials)

    def test_supports_all_required_file_formats(self):
        """Test that .xlsx, .xls, and .csv files are all supported."""
        xlsx_file = ValidFile(filename="test.xlsx", file_type=".xlsx", sha256_hash="hash1",
                             file_path="test.xlsx", download_timestamp="", source_post_url="", file_size_bytes=0)
        xls_file = ValidFile(filename="test.xls", file_type=".xls", sha256_hash="hash2",
                            file_path="test.xls", download_timestamp="", source_post_url="", file_size_bytes=0)
        csv_file = ValidFile(filename="test.csv", file_type=".csv", sha256_hash="hash3",
                            file_path="test.csv", download_timestamp="", source_post_url="", file_size_bytes=0)

        test_data = pd.DataFrame({'Material': ['Test'], 'Temp': ['200°C']})

        with patch('pandas.read_excel', return_value=test_data):
            with patch('pandas.read_csv', return_value=test_data):
                # Should handle all formats without error
                for file in [xlsx_file, xls_file, csv_file]:
                    materials = self.normalizer_service.process_materials([file])
                    assert isinstance(materials, list)
