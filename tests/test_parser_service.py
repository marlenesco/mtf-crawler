import pytest
from unittest.mock import Mock, patch, mock_open
from src.services.parser_service import ParserService
from src.models.post import Post
from src.models.valid_file import ValidFile


class TestParserService:
    """Contract tests for ParserService per constitutional requirements."""

    def setup_method(self):
        self.parser_service = ParserService()
        self.sample_post = Post(
            url="https://www.mytechfun.com/videos/material_test/sample-post",
            title="Test Material Post",
            cleaned_text="""
            Test content with Download files section:
            <a href="/download/test.xlsx">test.xlsx</a>
            <a href="/download/test.stl">test.stl</a>
            <a href="/download/data.csv">data.csv</a>
            """,
            youtube_link="https://youtube.com/watch?v=test",
            manufacturer_links=[],
            download_timestamp="2025-10-03T10:00:00Z",
            post_hash="abc123"
        )

    def test_extract_files_returns_list_of_valid_files(self):
        """Test that extract_files returns a list of ValidFile objects."""
        # This test MUST FAIL initially - no implementation exists yet
        files = self.parser_service.extract_files(self.sample_post)

        assert isinstance(files, list)
        for file in files:
            assert isinstance(file, ValidFile)
            assert file.filename is not None
            assert file.file_type in ['.xlsx', '.xls', '.csv']
            assert file.sha256_hash is not None

    def test_filters_only_spreadsheet_files(self):
        """Test that only .xlsx/.xls/.csv files are extracted."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.content = b'test content'
            mock_get.return_value.status_code = 200

            files = self.parser_service.extract_files(self.sample_post)

            # Should only include spreadsheet files, not .stl
            valid_extensions = {'.xlsx', '.xls', '.csv'}
            for file in files:
                assert file.file_type in valid_extensions

    def test_ignores_non_spreadsheet_files(self):
        """Test that .stl, images, zip, models are ignored."""
        post_with_mixed_files = Post(
            url="https://test.com",
            title="Mixed Files",
            cleaned_text="""
            <a href="/file.xlsx">spreadsheet.xlsx</a>
            <a href="/model.stl">model.stl</a>
            <a href="/image.jpg">image.jpg</a>
            <a href="/archive.zip">archive.zip</a>
            <a href="/data.csv">data.csv</a>
            """,
            youtube_link="", manufacturer_links=[],
            download_timestamp="", post_hash="test"
        )

        with patch('requests.get') as mock_get:
            mock_get.return_value.content = b'test'
            mock_get.return_value.status_code = 200

            files = self.parser_service.extract_files(post_with_mixed_files)

            # Should only have 2 files: .xlsx and .csv
            assert len(files) == 2
            extensions = {f.file_type for f in files}
            assert extensions == {'.xlsx', '.csv'}

    def test_calculates_sha256_hash_for_files(self):
        """Test that SHA-256 hash is calculated for downloaded files."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.content = b'test content'
            mock_get.return_value.status_code = 200

            files = self.parser_service.extract_files(self.sample_post)

            for file in files:
                assert len(file.sha256_hash) == 64  # SHA-256 is 64 hex chars
                assert all(c in '0123456789abcdef' for c in file.sha256_hash)

    def test_handles_broken_download_links(self):
        """Test that broken links are logged and processing continues."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [ConnectionError(), Mock(content=b'ok', status_code=200)]

            with patch('structlog.get_logger') as mock_logger:
                files = self.parser_service.extract_files(self.sample_post)

                # Should log error but continue with other files
                mock_logger.return_value.error.assert_called()
                # Should still return successful downloads
                assert isinstance(files, list)

    def test_deduplicates_files_by_content_hash(self):
        """Test that identical files are deduplicated by SHA-256."""
        post_with_duplicate_content = Post(
            url="https://test.com",
            title="Duplicate Files",
            cleaned_text="""
            <a href="/file1.xlsx">file1.xlsx</a>
            <a href="/file2.xlsx">file2.xlsx</a>
            """,
            youtube_link="", manufacturer_links=[],
            download_timestamp="", post_hash="test"
        )

        with patch('requests.get') as mock_get:
            # Same content for both files
            mock_get.return_value.content = b'identical content'
            mock_get.return_value.status_code = 200

            files = self.parser_service.extract_files(post_with_duplicate_content)

            # Should deduplicate identical content
            if len(files) > 1:
                hashes = {f.sha256_hash for f in files}
                assert len(hashes) == len(files)  # All unique hashes

    def test_stores_files_in_correct_directory_structure(self):
        """Test that files are stored in data/raw/{post_hash}/ structure."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.content = b'test content'
            mock_get.return_value.status_code = 200

            with patch('builtins.open', mock_open()) as mock_file:
                files = self.parser_service.extract_files(self.sample_post)

                for file in files:
                    expected_path = f"data/raw/{self.sample_post.post_hash}/"
                    assert file.file_path.startswith(expected_path)
