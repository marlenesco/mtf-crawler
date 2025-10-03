import pytest
from unittest.mock import Mock, patch
from src.services.crawler_service import CrawlerService
from src.models.post import Post


class TestCrawlerService:
    """Contract tests for CrawlerService per constitutional requirements."""

    def setup_method(self):
        self.crawler_service = CrawlerService()
        self.base_url = "https://www.mytechfun.com/videos/material_test"

    def test_crawl_posts_returns_list_of_posts(self):
        """Test that crawl_posts returns a list of Post objects."""
        # This test MUST FAIL initially - no implementation exists yet
        posts = self.crawler_service.crawl_posts(self.base_url)

        assert isinstance(posts, list)
        for post in posts:
            assert isinstance(post, Post)
            assert post.url is not None
            assert post.title is not None
            assert post.cleaned_text is not None
            assert post.post_hash is not None

    def test_respects_robots_txt(self):
        """Test that crawler checks robots.txt before making requests."""
        with patch('robotexclusionrulesparser.RobotExclusionRulesParser') as mock_robots:
            mock_robots.return_value.is_allowed.return_value = False

            with pytest.raises(Exception) as exc_info:
                self.crawler_service.crawl_posts(self.base_url)

            assert "robots.txt" in str(exc_info.value).lower()

    def test_uses_correct_user_agent(self):
        """Test that crawler uses constitutional user-agent."""
        with patch('requests.Session') as mock_session:
            self.crawler_service.crawl_posts(self.base_url)

            # Verify user-agent header is set
            mock_session.return_value.headers.update.assert_called_with({
                'User-Agent': 'mytechfun-research-bot/1.0 (contact: ...)'
            })

    def test_applies_rate_limiting(self):
        """Test that crawler applies rate limiting between requests."""
        with patch('time.sleep') as mock_sleep:
            with patch('requests.Session.get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.text = '<html><body>Test</body></html>'

                self.crawler_service.crawl_posts(self.base_url)

                # Verify rate limiting is applied
                assert mock_sleep.called

    def test_handles_network_failures_with_retry(self):
        """Test that crawler retries on network failures with exponential backoff."""
        with patch('tenacity.Retrying') as mock_retry:
            with patch('requests.Session.get') as mock_get:
                mock_get.side_effect = [ConnectionError(), Mock()]

                self.crawler_service.crawl_posts(self.base_url)

                # Verify retry mechanism is used
                assert mock_retry.called

    def test_deduplicates_posts_by_content_hash(self):
        """Test that identical posts are deduplicated by SHA-256 hash."""
        # Mock duplicate content
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value.text = '<html><body>Same content</body></html>'

            posts = self.crawler_service.crawl_posts(self.base_url)

            # Should deduplicate identical posts
            post_hashes = [post.post_hash for post in posts]
            assert len(post_hashes) == len(set(post_hashes))

    def test_logs_operations_in_json_format(self):
        """Test that all operations are logged in structured JSON format."""
        with patch('structlog.get_logger') as mock_logger:
            self.crawler_service.crawl_posts(self.base_url)

            # Verify structured logging is used
            assert mock_logger.called
            mock_logger.return_value.info.assert_called()
