import pytest
from bs4 import BeautifulSoup

def test_strip_html_tags(transformer):
    # Test basic HTML stripping
    html = "<p>Hello <b>World</b>!</p>"
    assert transformer.transform(html, ["strip_html_tags"]) == "Hello World!"
    
    # Test nested HTML
    html = "<div>Hello <span>Beautiful <strong>World</strong></span>!</div>"
    assert transformer.transform(html, ["strip_html_tags"]) == "Hello Beautiful World!"

def test_html_sanitization(transformer):
    # Test removing script tags
    html = """
    <div>Hello World</div>
    <script>alert('dangerous');</script>
    <p>Safe content</p>
    """
    result = transformer.transform(html, ["html_sanitize"])
    assert "<script>" not in result
    assert "Hello World" in result
    assert "Safe content" in result

def test_link_extraction(transformer):
    # Test extracting links from HTML
    html = """
    <div>
        <a href="https://example.com">Example</a>
        <p>Some text</p>
        <a href="/relative/path">Relative</a>
    </div>
    """
    links = transformer.transform(html, ["link_extraction"])
    assert len(links) == 2
    assert "https://example.com" in links
    assert "/relative/path" in links

def test_url_transforms(transformer):
    # Test URL resolution
    relative_url = "/path/to/resource"
    base_url = "https://example.com"
    result = transformer.transform(relative_url, [{
        "function": "resolve_url",
        "base_url": base_url
    }])
    assert result == "https://example.com/path/to/resource"

    # Test domain extraction
    url = "https://example.com/path?query=123"
    domain = transformer.transform(url, ["extract_domain"])
    assert domain == "example.com"

def test_html_and_text_combination(transformer):
    # Test combination of HTML stripping and text transformation
    html = "<div>HELLO <b>WORLD</b>!</div>"
    result = transformer.transform(html, [
        "strip_html_tags",
        "lowercase",
        {"function": "truncate", "length": 8}
    ])
    assert result == "hello wo..."

def test_complex_product_extraction(transformer):
    # Complex pattern for product extraction
    COMPLEX_HTML = """
    <div class="product-container">
        <span class="model-code">Model ABC-123 Rev.2</span>
        <div class="tech-specs">
            <table>
                <tr><td>CPU</td><td>Intel i9-13900K</td></tr>
                <tr><td>Memory</td><td>64GB DDR5</td></tr>
            </table>
        </div>
        <div class="downloads">
            <a href="/files/manual.pdf" data-filetype="PDF" data-size="2.5 MB">Manual</a>
            <a href="/files/drivers.zip" data-filetype="ZIP" data-size="1.2 GB">Drivers</a>
        </div>
        <div class="variants">
            <div class="product-variant">
                <span data-sku="VAR-001"></span>
                <span class="original-price">$1,299.99</span>
                <span class="discount-tag">20% OFF</span>
                <span class="stock-status" data-stock-level="1">Low Stock</span>
            </div>
            <div class="product-variant">
                <span data-sku="VAR-002"></span>
                <span class="original-price">$1,499.99</span>
                <span class="discount-tag">15% OFF</span>
                <span class="stock-status" data-stock-level="2">In Stock</span>
            </div>
        </div>
    </div>
    """
    
    # Test model info extraction
    model_info = transformer.transform(COMPLEX_HTML, [
        {"function": "html_sanitize"},
        {
            "function": "regex",
            "pattern": r"Model\s*(\w+)-(\d+)\s*Rev\.(\d+)",
            "template": "Series: {1}, Number: {2}, Revision: {3}"
        }
    ])
    assert model_info == "Series: ABC, Number: 123, Revision: 2"
    
    # Test tech specs extraction
    soup = BeautifulSoup(COMPLEX_HTML, 'html.parser')
    specs_rows = soup.select(".tech-specs table tr")
    specs = {}
    for row in specs_rows:
        label = transformer.transform(row.select_one("td:first-child").text, ["strip"])
        value = transformer.transform(row.select_one("td:last-child").text, ["strip"])
        specs[label] = value
    
    assert specs == {
        "CPU": "Intel i9-13900K",
        "Memory": "64GB DDR5"
    }
    
    # Test download links extraction
    download_links = soup.select(".downloads a")
    downloads = []
    for link in download_links:
        downloads.append({
            "url": link["href"],
            "type": transformer.transform(link["data-filetype"], ["lowercase"]),
            "size": transformer.transform(
                link["data-size"],
                [{
                    "function": "regex",
                    "pattern": r"(\d+(?:\.\d+)?)\s*(MB|GB|KB)",
                    "template": "{1} {2}"
                }]
            )
        })
    
    assert downloads == [
        {"url": "/files/manual.pdf", "type": "pdf", "size": "2.5 MB"},
        {"url": "/files/drivers.zip", "type": "zip", "size": "1.2 GB"}
    ]

def test_complex_pattern_extraction(transformer):
    COMPLEX_PATTERN = {
        "name": "complex_product",
        "url": "/products/details/",
        "properties": [
            {
                "name": "model_info",
                "selector": {
                    "primary": ".model-code",
                    "fallback": [".product-code", "#item-code", "[data-type='model']"]
                },
                "attribute": "text",
                "transform": [
                    {"function": "regex", "pattern": r"Model\s*(\w+)-(\d+)\s*Rev\.(\d+)"},
                    {"function": "template", "template": "Series: {1}, Number: {2}, Revision: {3}"}
                ],
                "type": "string"
            },
            {
                "name": "technical_specs",
                "selector": {
                    "primary": ".tech-specs table tr",
                    "fallback": [".specifications table tr", "#specs-table tr"]
                },
                "type": "object",
                "properties": [
                    {
                        "name": "label",
                        "selector": {"primary": "td:first-child"},
                        "attribute": "text",
                        "transform": [{"function": "strip"}]
                    },
                    {
                        "name": "value",
                        "selector": {"primary": "td:last-child"},
                        "attribute": "text",
                        "transform": [{"function": "strip"}]
                    }
                ]
            },
            {
                "name": "download_links",
                "selector": {
                    "primary": ".downloads a",
                    "fallback": [".resources a"]
                },
                "type": "array",
                "properties": [
                    {
                        "name": "url",
                        "attribute": "href"
                    },
                    {
                        "name": "type",
                        "attribute": "data-filetype",
                        "transform": [{"function": "lowercase"}]
                    },
                    {
                        "name": "size",
                        "attribute": "data-size",
                        "transform": [
                            {"function": "regex", "pattern": r"(\d+(?:\.\d+)?)\s*(MB|GB|KB)", "template": "{1} {2}"}
                        ]
                    }
                ]
            }
        ]
    }

    COMPLEX_HTML = """
    <div class="product-container">
        <span class="model-code">Model ABC-123 Rev.2</span>
        <div class="tech-specs">
            <table>
                <tr><td>CPU</td><td>Intel i9-13900K</td></tr>
                <tr><td>Memory</td><td>64GB DDR5</td></tr>
            </table>
        </div>
        <div class="downloads">
            <a href="/files/manual.pdf" data-filetype="PDF" data-size="2.5 MB">Manual</a>
            <a href="/files/drivers.zip" data-filetype="ZIP" data-size="1.2 GB">Drivers</a>
        </div>
        <div class="variants">
            <div class="product-variant">
                <span data-sku="VAR-001"></span>
                <span class="original-price">$1,299.99</span>
                <span class="discount-tag">20% OFF</span>
                <span class="stock-status" data-stock-level="1">Low Stock</span>
            </div>
            <div class="product-variant">
                <span data-sku="VAR-002"></span>
                <span class="original-price">$1,499.99</span>
                <span class="discount-tag">15% OFF</span>
                <span class="stock-status" data-stock-level="2">In Stock</span>
            </div>
        </div>
    </div>
    """

    # Extract data using the pattern
    result = transformer.extract_html_with_pattern(COMPLEX_HTML, COMPLEX_PATTERN)

    # Verify extracted data
    assert result["model_info"] == "Series: ABC, Number: 123, Revision: 2"
    
    assert result["technical_specs"] == [
        {"label": "CPU", "value": "Intel i9-13900K"},
        {"label": "Memory", "value": "64GB DDR5"}
    ]
    
    assert result["download_links"] == [
        {"url": "/files/manual.pdf", "type": "pdf", "size": "2.5 MB"},
        {"url": "/files/drivers.zip", "type": "zip", "size": "1.2 GB"}
    ]

def test_extract_property_from_html(transformer):
    # Test basic property extraction
    html = """
    <div class="container">
        <h1 class="title">Welcome</h1>
        <p class="description">This is a <b>test</b> description.</p>
        <ul class="links">
            <li><a href="link1.html">Link 1</a></li>
            <li><a href="link2.html">Link 2</a></li>
        </ul>
    </div>
    """

    # Test simple text extraction
    result = transformer.extract_property_from_html(html, {
        "name": "title",
        "selector": "h1",
        "transform": ["strip"]
    })
    assert result == "Welcome"

    # Test with HTML stripping
    result = transformer.extract_property_from_html(html, {
        "name": "description",
        "selector": "p.description",
        "transform": ["strip_html_tags", "strip"]
    })
    assert result == "This is a test description."

    # Test array extraction
    result = transformer.extract_property_from_html(html, {
        "name": "links",
        "selector": "a",
        "attribute": "href",
        "type": "array"
    })
    assert result == ["link1.html", "link2.html"]

    # Test with fallback
    result = transformer.extract_property_from_html(html, {
        "name": "subtitle",
        "selector": {
            "primary": "h2.subtitle",
            "fallback": ["h1.title"]
        },
        "transform": ["strip"]
    })
    assert result == "Welcome"

    # Test missing property
    result = transformer.extract_property_from_html(html, {
        "name": "missing",
        "selector": "nonexistent"
    })
    assert result is None