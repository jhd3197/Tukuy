"""HTML transformation implementations."""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ..base import ChainableTransformer
from ..types import TransformContext
from ..exceptions import ValidationError

class StripHtmlTagsTransformer(ChainableTransformer[str, str]):
    """
    Description:
        A transformer that removes all HTML tags from text while preserving the text
        content. Uses BeautifulSoup for robust HTML parsing and text extraction.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
    
    Returns:
        str: The text content with all HTML tags removed
    
    Raises:
        ValidationError: If the input value is not a string
    
    Example:
        ```python
        transformer = StripHtmlTagsTransformer("strip_tags")
        
        # Remove HTML tags
        result = transformer.transform("<p>Hello <b>World</b>!</p>")
        assert result.value == "Hello World!"
        
        # Handle nested tags
        result = transformer.transform(
            "<div>This is <span>some <i>formatted</i></span> text.</div>"
        )
        assert result.value == "This is some formatted text."
        
        # Chain with other transformers
        strip = StripTransformer("strip")
        pipeline = transformer.chain(strip)
        
        result = pipeline.transform("  <p>Hello World!</p>  ")
        assert result.value == "Hello World!"
        ```
    """
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        soup = BeautifulSoup(value, 'html.parser')
        return soup.get_text()

class HtmlSanitizationTransformer(ChainableTransformer[str, str]):
    """
    Description:
        A transformer that sanitizes HTML content by removing potentially dangerous
        script and style tags while preserving other HTML structure. Uses BeautifulSoup
        for robust HTML parsing and manipulation.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
    
    Returns:
        str: The sanitized HTML with script and style tags removed
    
    Raises:
        ValidationError: If the input value is not a string
    
    """
    
    # List of potentially dangerous tags to remove
    DANGEROUS_TAGS = [
        'script', 'style', 'iframe', 'object', 'embed', 
        'frame', 'frameset', 'meta', 'link'
    ]
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        # Use html5lib parser for better HTML handling
        soup = BeautifulSoup(value, 'html5lib')
        
        # Remove dangerous tags
        for tag in self.DANGEROUS_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
                
        # Remove on* attributes and javascript: URLs
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if attr.startswith('on'):
                    del tag[attr]
                elif attr in ['href', 'src', 'action']:
                    if 'javascript:' in tag[attr].lower():
                        del tag[attr]
        
        # Convert to string, ensuring proper encoding
        return str(soup.encode(formatter='html5').decode('utf-8'))

class LinkExtractionTransformer(ChainableTransformer[str, List[str]]):
    """
    Description:
        A transformer that extracts all href links from HTML content. Uses BeautifulSoup
        to find all anchor tags with href attributes and returns their URLs as a list.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
    
    Returns:
        List[str]: List of URLs found in href attributes of anchor tags
    
    Raises:
        ValidationError: If the input value is not a string
    
    Notes:
        - Only extracts links from <a> tags with href attributes
        - Returns an empty list if no links are found
        - Preserves the original URL format (relative or absolute)
    
    Example:
        ```python
        transformer = LinkExtractionTransformer("extract_links")
        
        # Extract multiple links
        result = transformer.transform('''
            <div>
                <a href="https://example.com">Link 1</a>
                <a href="/relative/path">Link 2</a>
                <a href="page.html">Link 3</a>
            </div>
        ''')
        assert result.value == [
            "https://example.com",
            "/relative/path",
            "page.html"
        ]
        
        # Handle nested links
        result = transformer.transform('''
            <nav>
                <div>
                    <a href="link1.html">First</a>
                    <span>
                        <a href="link2.html">Second</a>
                    </span>
                </div>
            </nav>
        ''')
        assert result.value == ["link1.html", "link2.html"]
        
        # Chain with other transformers
        resolve = ResolveUrlTransformer("resolve", "https://example.com")
        pipeline = transformer.chain(resolve)
        
        result = pipeline.transform('<a href="/page">Link</a>')
        assert result.value == ["https://example.com/page"]
        ```
    """
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> List[str]:
        soup = BeautifulSoup(value, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            links.append(a['href'])
        return links

class ResolveUrlTransformer(ChainableTransformer[str, str]):
    """
    Description:
        A transformer that resolves relative URLs to absolute URLs using a provided
        base URL. Uses Python's urljoin for robust URL resolution that handles
        various relative path formats.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        base_url (str): The base URL to resolve relative URLs against
    
    Returns:
        str: The resolved absolute URL
    
    Raises:
        ValidationError: If the input value is not a string
    
    Notes:
        - Handles various relative path formats (e.g., "../path", "/path", "path")
        - Returns the original URL if it's already absolute
        - Uses urllib.parse.urljoin for standards-compliant URL resolution
    
    Example:
        ```python
        transformer = ResolveUrlTransformer(
            "resolve",
            base_url="https://example.com/blog/"
        )
        
        # Resolve relative paths
        result = transformer.transform("../about")
        assert result.value == "https://example.com/about"
        
        # Resolve root-relative paths
        result = transformer.transform("/contact")
        assert result.value == "https://example.com/contact"
        
        # Handle current directory paths
        result = transformer.transform("./post.html")
        assert result.value == "https://example.com/blog/post.html"
        
        # Leave absolute URLs unchanged
        result = transformer.transform("https://other.com/page")
        assert result.value == "https://other.com/page"
        
        # Chain with other transformers
        domain = ExtractDomainTransformer("domain")
        pipeline = transformer.chain(domain)
        
        result = pipeline.transform("/page")
        assert result.value == "example.com"
        ```
    """
    
    def __init__(self, name: str, base_url: str):
        super().__init__(name)
        self.base_url = base_url
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return urljoin(self.base_url, value)

class ExtractDomainTransformer(ChainableTransformer[str, str]):
    """
    Description:
        A transformer that extracts the domain (netloc) part from URLs. Uses Python's
        urlparse for robust URL parsing that handles various URL formats.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
    
    Returns:
        str: The domain (netloc) part of the URL, or empty string if not found
    
    Raises:
        ValidationError: If the input value is not a string
    
    Notes:
        - Returns the netloc component (domain + optional port)
        - Handles URLs with or without protocol
        - Returns empty string for invalid URLs or URLs without domain
    
    Example::
    
        transformer = ExtractDomainTransformer("domain")
        
        # Basic domain extraction
        result = transformer.transform("https://example.com/path")
        assert result.value == "example.com"
        
        # Handle subdomains
        result = transformer.transform("https://blog.example.com")
        assert result.value == "blog.example.com"
        
        # Handle ports
        result = transformer.transform("http://localhost:8080")
        assert result.value == "localhost:8080"
        
        # Handle protocol-relative URLs
        result = transformer.transform("//cdn.example.com/file.js")
        assert result.value == "cdn.example.com"
        
        # Chain with other transformers
        lowercase = LowercaseTransformer("lowercase")
        pipeline = transformer.chain(lowercase)
        
        result = pipeline.transform("https://EXAMPLE.COM")
        assert result.value == "example.com"
    """
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        parsed = urlparse(value)
        return parsed.netloc

class HtmlExtractor(ChainableTransformer[str, Dict[str, Any]]):
    """
    Description:
        A transformer that extracts structured data from HTML content using a pattern-based
        approach. Supports CSS selectors, nested properties, arrays, and fallback values.
        Uses BeautifulSoup for robust HTML parsing and querying.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        pattern (Dict[str, Any]): Pattern describing what data to extract
    
    Returns:
        Dict[str, Any]: The extracted data according to the pattern
    
    Raises:
        ValidationError: If the input value is not a string
    
    Notes:
        Pattern Structure::

        {
            "properties": [
                {
                    "name": "output_field_name",
                    "selector": {
                        "primary": "css.selector",
                        "fallback": ["alternate.selector", "another.selector"]
                    },
                    "attribute": "text|href|src|data-*",  # default: "text"
                    "type": "string|array|object",
                    "transform": [
                        {"function": "transform_name", "params": {...}}
                    ],
                    "properties": [  # for nested objects
                        {
                            "name": "nested_field",
                            "selector": "nested.selector",
                            # ... same structure as above
                        }
                    ]
                }
            ]
        }
    
    Example::
    
        # Create an extractor for blog posts
        pattern = {
            "properties": [
                {
                    "name": "title",
                    "selector": "h1.post-title",
                    "type": "string"
                },
                {
                    "name": "metadata",
                    "type": "object",
                    "properties": [
                        {
                            "name": "author",
                            "selector": ".author-name"
                        },
                        {
                            "name": "date",
                            "selector": ".post-date"
                        }
                    ]
                },
                {
                    "name": "tags",
                    "selector": ".tag",
                    "type": "array"
                },
                {
                    "name": "image",
                    "selector": {
                        "primary": ".featured-image img",
                        "fallback": [".post-image img"]
                    },
                    "attribute": "src"
                }
            ]
        }
        
        extractor = HtmlExtractor("blog_post", pattern)
        
        # Extract data from HTML
        html = '''
            <article>
                <h1 class="post-title">My First Post</h1>
                <div class="metadata">
                    <span class="author-name">John Doe</span>
                    <time class="post-date">2024-03-24</time>
                </div>
                <img class="featured-image" src="image.jpg">
                <div class="tags">
                    <span class="tag">tech</span>
                    <span class="tag">python</span>
                </div>
            </article>
        '''
        
        result = extractor.transform(html)
        assert result.value == {
            "title": "My First Post",
            "metadata": {
                "author": "John Doe",
                "date": "2024-03-24"
            },
            "image": "image.jpg",
            "tags": ["tech", "python"]
        }
    """
    
    def __init__(self, name: str, pattern: Dict[str, Any]):
        super().__init__(name)
        self.pattern = pattern
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> Dict[str, Any]:
        soup = BeautifulSoup(value, 'html.parser')
        if not self.pattern:
            return {}
            
        return {
            prop['name']: self._extract_property(soup, prop, context)
            for prop in self.pattern.get("properties", [])
        }
    
    def _extract_property(self, soup: BeautifulSoup, prop: Dict[str, Any], context: Optional[TransformContext] = None) -> Any:
        """Extract a property from HTML using the property pattern."""
        selector = prop.get("selector", {})
        primary = selector.get("primary") if isinstance(selector, dict) else selector
        fallback = selector.get("fallback", []) if isinstance(selector, dict) else []
        attribute = prop.get("attribute", "text")
        transforms = prop.get("transform", [])
        data_type = prop.get("type", "string")
        properties = prop.get("properties", [])
        
        # Ensure transforms is a list
        transforms = [transforms] if not isinstance(transforms, list) else transforms
        
        if data_type == "array" or (data_type == "object" and primary and primary.endswith("tr")):
            elements = self._select_elements(soup, primary, fallback)
            results = []
            for el in elements:
                if properties:
                    item_data = {}
                    for nested_prop in properties:
                        nested_value = self._extract_nested_property(el, nested_prop, context)
                        item_data[nested_prop['name']] = nested_value
                    results.append(item_data)
                else:
                    value = self._get_element_value(el, attribute)
                    if value:
                        # Apply transforms
                        transformed_value = self._apply_transforms(value, transforms, context)
                        if transformed_value not in [None, '']:
                            results.append(transformed_value)
            return results
            
        elif data_type == "object":
            if properties:
                element = self._select_element(soup, primary, fallback) if primary else soup
                return self._process_object(element, properties, context)
            else:
                elements = self._select_elements(soup, primary, fallback)
                if len(elements) > 1:
                    return [self._get_element_value(el, attribute) for el in elements]
                element = elements[0] if elements else None
                value = self._get_element_value(element, attribute) if element else None
                return self._apply_transforms(value, transforms, context) if value else None
                
        else:
            # data_type == "string" or anything else
            element = self._select_element(soup, primary, fallback)
            value = self._get_element_value(element, attribute) if element else None
            return self._apply_transforms(value, transforms, context) if value else None
    
    def _select_elements(self, soup: BeautifulSoup, primary: str, fallback: List[str]) -> List[Any]:
        """Select elements using primary selector or fallbacks."""
        elements = soup.select(primary) if primary else []
        if not elements:
            for fb in ([fallback] if isinstance(fallback, str) else fallback):
                elements = soup.select(fb)
                if elements:
                    break
        return elements
    
    def _select_element(self, soup: BeautifulSoup, primary: str, fallback: List[str]) -> Optional[Any]:
        """Select a single element using primary selector or fallbacks."""
        if isinstance(soup, BeautifulSoup):
            element = soup.select_one(primary) if primary else None
        else:
            element = soup.select_one(primary) if primary else soup
            
        if not element and fallback:
            for fb in ([fallback] if isinstance(fallback, str) else fallback):
                if isinstance(soup, BeautifulSoup):
                    temp = soup.select_one(fb)
                else:
                    temp = soup.select_one(fb)
                if temp:
                    element = temp
                    break
        return element
    
    def _get_element_value(self, element: Any, attribute: str) -> str:
        """Get value from element based on attribute."""
        if not element:
            return ""
        if not attribute or attribute == "text" or (isinstance(attribute, list) and not attribute):
            return element.get_text().strip()
        # Handle both regular and data attributes
        if attribute.startswith('data-'):
            return element.get(attribute, "")
        return element.get(attribute, "")
    
    def _extract_nested_property(self, element: Any, prop: Dict[str, Any], context: Optional[TransformContext] = None) -> Any:
        """Extract a nested property from an element."""
        nested_attr = prop.get('attribute', 'text')
        nested_selector = prop.get('selector', {})
        data_type = prop.get('type', 'string')
        transforms = prop.get('transform', [])
        
        if data_type == "object" and prop.get('properties'):
            nested_element = self._select_element(
                element,
                nested_selector.get('primary') if isinstance(nested_selector, dict) else nested_selector,
                nested_selector.get('fallback', []) if isinstance(nested_selector, dict) else []
            )
            return self._process_object(nested_element or element, prop.get('properties', []), context)
            
        elif nested_attr != 'text' and not nested_selector:
            value = element.get(nested_attr, '')
        else:
            nested_element = self._select_element(
                element,
                nested_selector.get('primary') if isinstance(nested_selector, dict) else nested_selector,
                nested_selector.get('fallback', []) if isinstance(nested_selector, dict) else []
            )
            value = self._get_element_value(nested_element, nested_attr) if nested_element else None
            
        return self._apply_transforms(value, transforms, context)
    
    def _process_object(self, element: Any, properties: List[Dict[str, Any]], context: Optional[TransformContext] = None) -> Dict[str, Any]:
        """Process an object with properties."""
        if not element:
            return {}
        results = []
        if element.select('tr'):
            for row in element.select('tr'):
                obj = {}
                for prop in properties:
                    obj[prop['name']] = self._extract_nested_property(row, prop, context)
                results.append(obj)
            return results
        else:
            obj = {}
            for prop in properties:
                obj[prop['name']] = self._extract_property(element, prop, context)
            return obj
    
    def _apply_transforms(self, value: str, transforms: List[Any], context: Optional[TransformContext] = None) -> Any:
        """Apply transforms to a value."""
        if not transforms or value is None:
            return value
            
        # Import here to avoid circular imports
        from ..transformers import TukuyTransformer
        
        # Create a transformer to apply the transforms
        transformer = TukuyTransformer()
        return transformer.transform(value, transforms)
