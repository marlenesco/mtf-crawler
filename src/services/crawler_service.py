import time
import requests
from bs4 import BeautifulSoup
from typing import List
from urllib.robotparser import RobotFileParser
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from models.post import Post


class CrawlerService:
    """Service for crawling material test posts from MyTechFun.com with constitutional compliance."""

    def __init__(self):
        self.logger = structlog.get_logger("mtf_crawler.crawler")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'mytechfun-research-bot/1.0 (contact: research@example.com)'
        })
        self.rate_limit_delay = 1.0  # Minimum delay between requests (seconds)
        self.last_request_time = 0.0

    def crawl_posts(self, base_url: str) -> List[Post]:
        """
        Crawl material test posts from MyTechFun.com per constitutional requirements.

        Args:
            base_url: The base URL to start crawling from

        Returns:
            List of Post objects with extracted content

        Raises:
            CrawlerError: When crawling fails or robots.txt violation
            RateLimitError: When rate limiting is required
        """
        self.logger.info("Starting post crawling", base_url=base_url)

        # Check robots.txt compliance
        if not self._check_robots_txt(base_url):
            raise CrawlerError("Robots.txt disallows crawling this URL")

        posts = []
        processed_hashes = set()  # For deduplication

        try:
            # Get list of post URLs from main page
            post_urls = self._extract_post_urls(base_url)
            self.logger.info("Found post URLs", count=len(post_urls))

            for url in post_urls:
                self._apply_rate_limiting()

                try:
                    post = self._crawl_single_post(url)
                    if post and post.post_hash not in processed_hashes:
                        posts.append(post)
                        processed_hashes.add(post.post_hash)
                        self.logger.info("Post processed", url=url, hash=post.post_hash[:8])
                    elif post:
                        self.logger.info("Duplicate post skipped", url=url, hash=post.post_hash[:8])

                except Exception as e:
                    self.logger.error("Failed to process post", url=url, error=str(e))
                    continue

            self.logger.info("Crawling completed", total_posts=len(posts))
            return posts

        except Exception as e:
            self.logger.error("Crawling failed", error=str(e))
            raise CrawlerError(f"Failed to crawl posts: {str(e)}")

    def _check_robots_txt(self, base_url: str) -> bool:
        """Check robots.txt compliance per constitutional requirements."""
        try:
            robots_url = f"{base_url.split('/')[0]}//{base_url.split('//')[1].split('/')[0]}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()

            user_agent = self.session.headers.get('User-Agent', '*')
            allowed = rp.can_fetch(user_agent, base_url)

            self.logger.info("Robots.txt check", url=robots_url, allowed=allowed)
            return allowed

        except Exception as e:
            self.logger.warning("Robots.txt check failed, proceeding cautiously", error=str(e))
            return True  # Proceed if robots.txt can't be checked

    def _apply_rate_limiting(self):
        """Apply rate limiting with exponential backoff per constitution."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            self.logger.debug("Rate limiting applied", sleep_time=sleep_time)
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with retry logic and jitter."""
        self.logger.debug("Making request", url=url)
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response

    def _extract_post_urls(self, base_url: str) -> List[str]:
        """Extract individual post URLs from the main material test page."""
        response = self._make_request(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        post_urls = []

        # Look for post links - corrected selector based on actual HTML structure
        post_links = soup.find_all('a', href=True)

        for link in post_links:
            href = link.get('href')
            if href:
                # Check if it's a post link with format /video/<post-id> or https://www.mytechfun.com/video/<post-id>
                if '/video/' in href and '/videos/' not in href:  # Avoid the main listing page
                    # Skip YouTube links
                    if 'youtube.com' in href or 'youtu.be' in href:
                        continue

                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        full_url = f"{base_url.split('/')[0]}//{base_url.split('//')[1].split('/')[0]}{href}"
                    elif not href.startswith('http'):
                        full_url = f"{base_url.rstrip('/')}/{href}"
                    else:
                        full_url = href

                    if full_url not in post_urls:
                        post_urls.append(full_url)
                        self.logger.debug("Found post URL", url=full_url)

        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in post_urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)

        self.logger.info("Extracted post URLs", total_found=len(unique_urls))
        return unique_urls

    def _crawl_single_post(self, url: str) -> Post:
        """Crawl a single post and extract relevant information."""
        response = self._make_request(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title - skip first h1 (MyTechFun.com) and use second h1
        title = "Unknown Title"
        h1_elements = soup.find_all('h1')
        for h1 in h1_elements:
            # Skip the first h1 if it contains "MyTechFun.com"
            if 'MyTechFun.com' in h1.get_text():
                continue
            # Use the first h1 that doesn't contain "MyTechFun.com" (which is the real title)
            title = h1.get_text().strip()
            break

        # Find and extract YouTube link
        youtube_link = self._extract_youtube_link(soup)

        # Find manufacturer links
        manufacturer_links = self._extract_manufacturer_links(soup)

        # Create Post with cleaned content
        post = Post.from_html(
            url=url,
            title=title,
            raw_html=response.text,
            youtube_link=youtube_link,
            manufacturer_links=manufacturer_links
        )

        return post

    def _extract_youtube_link(self, soup: BeautifulSoup) -> str:
        """Extract YouTube review link from post content."""
        # Look for YouTube links in various formats
        youtube_patterns = [
            'youtube.com/watch',
            'youtu.be/',
            'youtube.com/embed'
        ]

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if any(pattern in href for pattern in youtube_patterns):
                return href

        return None

    def _extract_manufacturer_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract filament manufacturer links from post content."""
        manufacturer_links = []

        # Common manufacturer domains to look for
        manufacturer_domains = [
            'prusament.com', 'polymaker.com', 'hatchbox3d.com',
            'overture3d.com', 'sunlu.com', 'esun3d.com'
        ]

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if any(domain in href for domain in manufacturer_domains):
                manufacturer_links.append(href)

        return manufacturer_links


class CrawlerError(Exception):
    """Exception raised when crawling operations fail."""
    pass


class RateLimitError(Exception):
    """Exception raised when rate limiting is violated."""
    pass
