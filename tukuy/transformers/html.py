"""HTML transformation implementations."""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ..base import ChainableTransformer
from ..types import TransformContext
from ..exceptions import ValidationError

class StripHtmlTagsTransformer(ChainableTransformer[str, str]):
    """Strip HTML tags from text."""
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        soup = BeautifulSoup(value, 'html.parser')
        return soup.get_text()

class HtmlSanitizationTransformer(ChainableTransformer[str, str]):
    """Sanitize HTML by removing script and style tags."""
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        soup = BeautifulSoup(value, 'html.parser')
        for tag in soup(['script', 'style']):
            tag.decompose()
        return str(soup)

class LinkExtractionTransformer(ChainableTransformer[str, List[str]]):
    """Extract links from HTML."""
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> List[str]:
        soup = BeautifulSoup(value, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            links.append(a['href'])
        return links

class ResolveUrlTransformer(ChainableTransformer[str, str]):
    """Resolve relative URL to absolute URL."""
    
    def __init__(self, name: str, base_url: str):
        super().__init__(name)
        self.base_url = base_url
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return urljoin(self.base_url, value)

class ExtractDomainTransformer(ChainableTransformer[str, str]):
    """Extract domain from URL."""
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        parsed = urlparse(value)
        return parsed.netloc

class HtmlExtractor(ChainableTransformer[str, Dict[str, Any]]):
    """Extract data from HTML using a pattern."""
    
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
