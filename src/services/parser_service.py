import os
import requests
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urljoin, urlparse
import structlog
from models.post import Post
from models.valid_file import ValidFile


class ParserService:
    """Service for extracting and downloading valid files from posts per constitutional requirements."""

    def __init__(self):
        self.logger = structlog.get_logger("mtf_crawler.parser")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'mytechfun-research-bot/1.0 (contact: research@example.com)'
        })
        self.valid_extensions = {'.xlsx', '.xls', '.csv'}
        self.ignored_extensions = {'.stl', '.zip', '.jpg', '.jpeg', '.png', '.gif', '.pdf'}

    def extract_files(self, post: Post) -> List[ValidFile]:
        """
        Extract downloadable files from a post's "Download files" section.

        Args:
            post: Post object with cleaned_text and url

        Returns:
            List of ValidFile objects for .xlsx/.xls/.csv files only

        Raises:
            ParserError: When file extraction fails
            DownloadError: When file download fails
        """
        self.logger.info("Extracting files from post", url=post.url)

        try:
            # Parse the post content to find download section
            download_links = self._find_download_links(post.url)

            # Filter for valid file types only
            valid_links = self._filter_valid_files(download_links)
            self.logger.info("Found valid download links", count=len(valid_links))

            # Download and create ValidFile objects
            valid_files = []
            for link in valid_links:
                try:
                    valid_file = self._download_file(link, post.url)
                    if valid_file:
                        valid_files.append(valid_file)
                        self.logger.info("File downloaded successfully",
                                       filename=valid_file.filename,
                                       size=valid_file.file_size)
                except Exception as e:
                    self.logger.error("Failed to download file", url=link, error=str(e))
                    continue

            self.logger.info("File extraction completed",
                           total_files=len(valid_files),
                           post_url=post.url)
            return valid_files

        except Exception as e:
            self.logger.error("File extraction failed", post_url=post.url, error=str(e))
            raise ParserError(f"Failed to extract files from post: {str(e)}")

    def _find_download_links(self, post_url: str) -> List[str]:
        """Find download links in the 'Download files' section of a post."""
        try:
            response = self.session.get(post_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            download_links = []

            # Look for "Download files" section - common patterns
            download_sections = []

            # Method 1: Find by text content
            for element in soup.find_all(text=lambda text: text and 'download' in text.lower()):
                parent = element.parent
                if parent and any(keyword in parent.get_text().lower() for keyword in ['download', 'files', 'attachment']):
                    download_sections.append(parent)

            # Method 2: Find by common class names
            for selector in ['.download', '.files', '.attachments', '.resources']:
                sections = soup.select(selector)
                download_sections.extend(sections)

            # Method 3: Look for links that point to file extensions
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.stl', '.zip']):
                    download_links.append(urljoin(post_url, href))

            # Extract links from identified download sections
            for section in download_sections:
                for link in section.find_all('a', href=True):
                    href = link.get('href')
                    full_url = urljoin(post_url, href)
                    if full_url not in download_links:
                        download_links.append(full_url)

            return list(set(download_links))  # Remove duplicates

        except Exception as e:
            self.logger.error("Failed to find download links", post_url=post_url, error=str(e))
            return []

    def _filter_valid_files(self, download_links: List[str]) -> List[str]:
        """Filter download links to include only valid file types."""
        valid_links = []

        for link in download_links:
            parsed_url = urlparse(link)
            path = parsed_url.path.lower()

            # Check if it's a valid extension
            if any(path.endswith(ext) for ext in self.valid_extensions):
                # Check it's not a gated asset (common patterns)
                if not self._is_gated_asset(link):
                    valid_links.append(link)
                    self.logger.debug("Valid file found", url=link)
                else:
                    self.logger.debug("Gated asset ignored", url=link)
            elif any(path.endswith(ext) for ext in self.ignored_extensions):
                self.logger.debug("Ignored file type", url=link)

        return valid_links

    def _is_gated_asset(self, url: str) -> bool:
        """Check if a URL points to a gated asset (requires login/payment)."""
        gated_indicators = [
            'login', 'signin', 'register', 'subscribe',
            'premium', 'paid', 'member', 'tier'
        ]

        url_lower = url.lower()
        return any(indicator in url_lower for indicator in gated_indicators)

    def _download_file(self, url: str, source_post_url: str) -> ValidFile:
        """Download a file and create a ValidFile object."""
        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Extract filename
            filename = self._extract_filename(url, response)

            # Read file content
            file_content = b''
            file_size = 0

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_content += chunk
                    file_size += len(chunk)

            # Create ValidFile object
            valid_file = ValidFile.from_download(
                url=url,
                filename=filename,
                content=file_content,
                source_post_url=source_post_url
            )

            return valid_file

        except Exception as e:
            self.logger.error("File download failed", url=url, error=str(e))
            raise DownloadError(f"Failed to download file {url}: {str(e)}")

    def _extract_filename(self, url: str, response: requests.Response) -> str:
        """Extract filename from URL or Content-Disposition header."""
        # Try Content-Disposition header first
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
            return filename

        # Fall back to URL path
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)

        if not filename:
            filename = f"download_{hash(url) % 10000}"

        return filename


class ParserError(Exception):
    """Exception raised when file parsing operations fail."""
    pass


class DownloadError(Exception):
    """Exception raised when file download operations fail."""
    pass
