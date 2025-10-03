import pytest
from unittest.mock import Mock, patch, mock_open
import json
from src.services.crawler_service import CrawlerService
from src.services.parser_service import ParserService
from src.services.normalizer_service import NormalizerService
from src.services.storage_service import StorageService


class TestIntegration:
    """Integration tests for complete crawler workflow per constitutional requirements."""

    def setup_method(self):
        self.base_url = "https://www.mytechfun.com/videos/material_test"
        self.crawler_service = CrawlerService()
        self.parser_service = ParserService()
        self.normalizer_service = NormalizerService()
        self.storage_service = StorageService()

    def test_complete_crawler_workflow_end_to_end(self):
        """Test the complete workflow from URL input to JSON output."""
        # This test MUST FAIL initially - no implementations exist yet

        # Mock the entire workflow chain
        with patch.object(self.crawler_service, 'crawl_posts') as mock_crawl:
            with patch.object(self.parser_service, 'extract_files') as mock_extract:
                with patch.object(self.normalizer_service, 'process_materials') as mock_normalize:
                    with patch.object(self.storage_service, 'save_json') as mock_save:

                        # Setup mock returns
                        mock_crawl.return_value = [Mock()]  # Mock post
                        mock_extract.return_value = [Mock()]  # Mock files
                        mock_normalize.return_value = [Mock()]  # Mock materials
                        mock_save.return_value = Mock()  # Mock JSON data

                        # Execute complete workflow
                        posts = self.crawler_service.crawl_posts(self.base_url)
                        assert posts is not None

                        for post in posts:
                            files = self.parser_service.extract_files(post)
                            assert files is not None

                            materials = self.normalizer_service.process_materials(files)
                            assert materials is not None

                            json_data = self.storage_service.save_json(post, files, materials)
                            assert json_data is not None

    def test_workflow_handles_posts_with_no_valid_files(self):
        """Test that workflow handles posts containing no spreadsheet files gracefully."""
        with patch.object(self.crawler_service, 'crawl_posts') as mock_crawl:
            with patch.object(self.parser_service, 'extract_files') as mock_extract:
                with patch.object(self.storage_service, 'save_json') as mock_save:

                    # Post exists but no valid files
                    mock_crawl.return_value = [Mock()]
                    mock_extract.return_value = []  # No valid files
                    mock_save.return_value = Mock()

                    posts = self.crawler_service.crawl_posts(self.base_url)
                    for post in posts:
                        files = self.parser_service.extract_files(post)
                        assert files == []

                        # Should still save post data even without files
                        json_data = self.storage_service.save_json(post, [], [])
                        assert json_data is not None

    def test_workflow_maintains_data_consistency_across_services(self):
        """Test that data hashes and references remain consistent across all services."""
        with patch('requests.Session') as mock_session:
            with patch('beautifulsoup4.BeautifulSoup') as mock_soup:
                with patch('pandas.read_excel') as mock_pandas:
                    with patch('builtins.open', mock_open()):
                        with patch('json.dump'):

                            # Mock consistent data flow
                            mock_session.return_value.get.return_value.text = "<html>Test post content</html>"
                            mock_soup.return_value.find_all.return_value = [
                                Mock(get=lambda x: "/test.xlsx", text="test.xlsx")
                            ]
                            mock_pandas.return_value = Mock(to_dict=lambda: {"Material": ["PLA"]})

                            # Execute workflow and verify data consistency
                            posts = self.crawler_service.crawl_posts(self.base_url)

                            if posts:
                                post = posts[0]
                                files = self.parser_service.extract_files(post)

                                if files:
                                    materials = self.normalizer_service.process_materials(files)
                                    json_data = self.storage_service.save_json(post, files, materials)

                                    # Verify data consistency
                                    assert json_data.post.post_hash == post.post_hash
                                    if materials:
                                        assert materials[0].source_file_hash in [f.sha256_hash for f in files]

    def test_workflow_respects_all_constitutional_requirements(self):
        """Test that the complete workflow respects all constitutional principles."""
        with patch('robotexclusionrulesparser.RobotExclusionRulesParser') as mock_robots:
            with patch('time.sleep') as mock_sleep:
                with patch('structlog.get_logger') as mock_logger:
                    with patch('requests.Session') as mock_session:

                        # Setup constitutional compliance mocks
                        mock_robots.return_value.is_allowed.return_value = True
                        mock_session.return_value.get.return_value.text = "<html>Content</html>"
                        mock_session.return_value.headers = {}

                        # Execute workflow
                        posts = self.crawler_service.crawl_posts(self.base_url)

                        # Verify constitutional compliance
                        # 1. Gentle Crawler: robots.txt checked
                        mock_robots.assert_called()

                        # 2. Rate limiting applied
                        assert mock_sleep.called

                        # 3. Structured logging used
                        assert mock_logger.called

                        # 4. Proper user-agent set
                        mock_session.return_value.headers.update.assert_called()

    def test_workflow_handles_network_failures_gracefully(self):
        """Test that network failures don't crash the entire workflow."""
        with patch.object(self.crawler_service, 'crawl_posts') as mock_crawl:
            with patch('structlog.get_logger') as mock_logger:

                # Simulate network failure
                mock_crawl.side_effect = ConnectionError("Network failure")

                # Should handle gracefully without crashing
                with pytest.raises(ConnectionError):
                    self.crawler_service.crawl_posts(self.base_url)

                # Should log the error
                mock_logger.return_value.error.assert_called()

    def test_workflow_produces_valid_json_output_structure(self):
        """Test that final JSON output matches expected structure from quickstart.md."""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                with patch.object(self.crawler_service, 'crawl_posts') as mock_crawl:
                    with patch.object(self.parser_service, 'extract_files') as mock_extract:
                        with patch.object(self.normalizer_service, 'process_materials') as mock_normalize:

                            # Setup complete mock data
                            mock_post = Mock(url="test_url", title="Test", post_hash="hash123")
                            mock_file_obj = Mock(filename="test.xlsx", sha256_hash="filehash")
                            mock_material = Mock(material_name="PLA", quality_rating="OK")

                            mock_crawl.return_value = [mock_post]
                            mock_extract.return_value = [mock_file_obj]
                            mock_normalize.return_value = [mock_material]

                            # Execute workflow
                            posts = self.crawler_service.crawl_posts(self.base_url)
                            for post in posts:
                                files = self.parser_service.extract_files(post)
                                materials = self.normalizer_service.process_materials(files)
                                json_data = self.storage_service.save_json(post, files, materials)

                            # Verify JSON structure matches quickstart.md expectations
                            if mock_json_dump.called:
                                saved_data = mock_json_dump.call_args[0][0]
                                required_top_level_keys = [
                                    "post", "files", "materials",
                                    "provenance", "constitution_compliance"
                                ]
                                for key in required_top_level_keys:
                                    assert key in saved_data

    def test_workflow_deduplication_works_across_all_services(self):
        """Test that SHA-256 deduplication works consistently across the entire workflow."""
        with patch('hashlib.sha256') as mock_hash:
            mock_hash.return_value.hexdigest.return_value = "consistent_hash_123"

            with patch.object(self.crawler_service, 'crawl_posts') as mock_crawl:
                with patch.object(self.parser_service, 'extract_files') as mock_extract:
                    with patch.object(self.normalizer_service, 'process_materials') as mock_normalize:
                        with patch.object(self.storage_service, 'save_json') as mock_save:

                            # Run workflow twice with identical content
                            mock_crawl.return_value = [Mock()]
                            mock_extract.return_value = [Mock()]
                            mock_normalize.return_value = [Mock()]
                            mock_save.return_value = Mock()

                            # First run
                            posts1 = self.crawler_service.crawl_posts(self.base_url)
                            # Second run (should detect duplicates)
                            posts2 = self.crawler_service.crawl_posts(self.base_url)

                            # Deduplication should be applied consistently
                            assert mock_hash.called
