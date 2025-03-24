"""HTML transformation plugin."""

from urllib.parse import urljoin, urlparse

from ...base import BaseTransformer, ChainableTransformer
from ...plugins.base import TransformerPlugin
from ...types import TransformContext
from ...transformers.html import (
    StripHtmlTagsTransformer,
    HtmlSanitizationTransformer,
    LinkExtractionTransformer,
    HtmlExtractor
)

class UrlJoinTransformer(ChainableTransformer[str, str]):
    """Joins URLs using urllib.parse.urljoin."""
    
    def __init__(self, name: str, base_url: str):
        super().__init__(name)
        self.base_url = base_url
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: TransformContext = None) -> str:
        return urljoin(self.base_url, value)

class ExtractDomainTransformer(ChainableTransformer[str, str]):
    """Extracts domain from URL."""
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: TransformContext = None) -> str:
        return urlparse(value).netloc

class HtmlTransformersPlugin(TransformerPlugin):
    """Plugin providing HTML transformation capabilities."""
    
    def __init__(self):
        """Initialize the HTML transformers plugin."""
        super().__init__("html")
        
    @property
    def transformers(self):
        """Get the HTML transformers."""
        return {
            # HTML manipulation
            'strip_html_tags': lambda _: StripHtmlTagsTransformer('strip_html_tags'),
            'html_sanitize': lambda _: HtmlSanitizationTransformer('html_sanitize'),
            'link_extraction': lambda _: LinkExtractionTransformer('link_extraction'),
            'html_extract': lambda params: HtmlExtractor('html_extract',
                pattern=params.get('pattern', {})),
                
            # URL handling
            'resolve_url': lambda params: UrlJoinTransformer('resolve_url',
                base_url=params.get('base_url', '')),
            'extract_domain': lambda _: ExtractDomainTransformer('extract_domain'),
        }
