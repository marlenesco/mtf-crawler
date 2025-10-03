from dataclasses import dataclass
from typing import List, Optional
import hashlib
from datetime import datetime
import re
from bs4 import BeautifulSoup


@dataclass
class Post:
    """Represents a single material test post from MyTechFun.com."""

    url: str
    title: str
    cleaned_text: str
    youtube_link: Optional[str]
    manufacturer_links: List[str]
    download_timestamp: str
    post_hash: Optional[str] = None

    def __post_init__(self):
        """Calculate SHA-256 hash of cleaned content for deduplication."""
        if self.post_hash is None:
            content_for_hash = f"{self.url}|{self.cleaned_text}".encode('utf-8')
            self.post_hash = hashlib.sha256(content_for_hash).hexdigest()

    def validate(self) -> bool:
        """Validate required fields per constitutional requirements."""
        required_fields = [self.url, self.title, self.cleaned_text, self.download_timestamp]
        return all(field is not None and field != "" for field in required_fields)

    @classmethod
    def from_html(cls, url: str, title: str, raw_html: str, youtube_link: Optional[str] = None,
                  manufacturer_links: Optional[List[str]] = None) -> 'Post':
        """Create Post from raw HTML with cleaning applied."""
        # Clean HTML content (remove header, footer, menu, etc.)
        cleaned_text = cls._clean_html_content(raw_html)

        return cls(
            url=url,
            title=title,
            cleaned_text=cleaned_text,
            youtube_link=youtube_link,
            manufacturer_links=manufacturer_links or [],
            download_timestamp=datetime.utcnow().isoformat() + "Z"
        )

    @staticmethod
    def _clean_html_content(raw_html: str) -> str:
        """
        Clean HTML content per specification:
        - Remove header, footer, menu
        - Remove first h1 containing "MyTechFun.com"
        - Remove everything after last <hr>
        - Remove self-promotional sections (Patreon, Buy Me a Coffee, etc.)
        """
        soup = BeautifulSoup(raw_html, 'html.parser')

        # Remove header, navigation, and menu elements
        for element in soup.find_all(['header', 'nav', 'menu']):
            element.decompose()

        # Remove first h1 containing "MyTechFun.com"
        h1_elements = soup.find_all('h1')
        for h1 in h1_elements:
            if 'MyTechFun.com' in h1.get_text():
                h1.decompose()
                break

        # Find the last hr and remove everything after it (footer content)
        hr_elements = soup.find_all('hr')
        if hr_elements:
            last_hr = hr_elements[-1]
            # Remove all siblings after the last hr
            for sibling in list(last_hr.next_siblings):
                if hasattr(sibling, 'decompose'):
                    sibling.decompose()
            last_hr.decompose()

        # Remove self-promotional sections
        promotional_keywords = [
            'patreon', 'buymeacoffee', 'paypal', 'donation', 'support',
            'subscribe', 'like and subscribe', 'buy me a coffee'
        ]

        for element in soup.find_all(text=True):
            text_lower = element.lower() if isinstance(element, str) else ''
            if any(keyword in text_lower for keyword in promotional_keywords):
                if hasattr(element, 'parent') and element.parent:
                    element.parent.decompose()

        # Remove common promotional div classes/ids
        for element in soup.find_all(['div', 'section'], class_=re.compile(r'(donation|support|patreon|subscribe)', re.I)):
            element.decompose()

        # Extract and return cleaned text
        cleaned_text = soup.get_text(separator=' ', strip=True)
        # Remove extra whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

        return cleaned_text.strip()

    def __str__(self) -> str:
        return f"Post(url='{self.url}', title='{self.title}', hash='{self.post_hash[:8]}...')"
