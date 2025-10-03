# CrawlerService Contract - Two-Phase Architecture

## Phase 1: Discovery & Collection Interface
```python
class CrawlerService:
    def crawl_posts_discovery(self, base_url: str, max_posts: Optional[int] = None) -> List[Post]:
        """
        Phase 1: Crawl material test posts and extract cleaned content
        
        Args:
            base_url: The base URL to start crawling from
            max_posts: Optional limit for testing/development
            
        Returns:
            List of Post objects with cleaned text and metadata
            
        Raises:
            CrawlerError: When crawling fails or robots.txt violation
            RateLimitError: When rate limiting is required
        """
    
    def extract_post_metadata(self, post_url: str) -> Post:
        """
        Extract and clean content from a single post
        
        Args:
            post_url: URL of individual post to process
            
        Returns:
            Post object with cleaned content, YouTube link, manufacturer links
            
        Raises:
            CrawlerError: When post extraction fails
        """
```

## Legacy Interface (Backward Compatibility)
```python
    def crawl_posts(self, base_url: str) -> List[Post]:
        """
        Legacy method - now delegates to crawl_posts_discovery()
        Maintained for backward compatibility with existing code
        """
```

## Constitutional Requirements
- MUST respect robots.txt before any requests
- MUST use user-agent: "mytechfun-research-bot/1.0 (contact: ...)"
- MUST apply rate limiting with exponential backoff (minimum 1 second between requests)
- MUST be idempotent (safe to re-run, uses SHA-256 deduplication)
- MUST log all operations in structured JSON format
- MUST clean post content per specification (remove header, footer, menu, promotional content)

## Input Validation
- base_url must be valid HTTPS URL
- base_url must be mytechfun.com domain
- max_posts must be positive integer if provided

## Output Guarantees
- All Post objects have valid post_hash for deduplication
- cleaned_text has header/footer/promotional content removed
- YouTube links extracted when present
- Manufacturer links identified and extracted
- Download timestamp in ISO format with 'Z' suffix

## Phase-Specific Behavior

### Discovery Phase (Phase 1)
- **Focus**: Collect and clean post content, extract metadata
- **Rate Limiting**: Aggressive (1-2 seconds between requests)
- **Content Processing**: Full HTML cleaning per specification
- **File Handling**: No file downloads in this phase
- **Output**: Clean Post objects ready for file extraction

### Error Handling
- **Network Errors**: Retry with exponential backoff (max 3 attempts)
- **Rate Limiting**: Respect 429 responses with extended delays
- **Robots.txt Violations**: Immediate failure with clear error message
- **Malformed HTML**: Log warning, attempt best-effort extraction
- **Missing Content**: Create Post with available data, mark in logs

## Performance Expectations
- **Rate**: 1-2 posts per minute (constitutional compliance)
- **Memory**: <100MB for typical 100-post crawl
- **Network**: ~1-5KB per post (text content only)
- **Reliability**: >95% success rate for accessible posts

## Testing Contract
```python
def test_crawl_posts_discovery_returns_list_of_posts():
    service = CrawlerService()
    posts = service.crawl_posts_discovery("https://www.mytechfun.com/videos/material_test")
    assert isinstance(posts, list)
    for post in posts:
        assert isinstance(post, Post)
        assert post.url is not None
        assert post.cleaned_text is not None
        assert post.post_hash is not None

def test_respects_robots_txt():
    # Should check robots.txt before making requests
    # Should raise CrawlerError if disallowed

def test_applies_rate_limiting():
    # Should enforce minimum delay between requests
    # Should use exponential backoff on errors
```
