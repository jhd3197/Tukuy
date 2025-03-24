#!/usr/bin/env python
"""
Tukuy - Example usage for the Tukuy transformation library.
This file contains practical examples of text and HTML transformations.
"""

from tukuy import ToolsTransformer
from tukuy.exceptions import ValidationError, TransformationError, ParseError

def text_transformation_examples():
    """Examples of text transformations using Tukuy."""
    print("\n===== TEXT TRANSFORMATION EXAMPLES =====\n")
    
    # Create the transformer
    tools = ToolsTransformer()
    
    # Example 1: Basic text transformations
    text = "  Hello World! This is a TEST string.  "
    print(f"Original text: '{text}'")
    
    # Strip whitespace
    result = tools.transform(text, ["strip"])
    print(f"After strip: '{result}'")
    
    # Convert to lowercase
    result = tools.transform(text, ["lowercase"])
    print(f"After lowercase: '{result}'")
    
    # Chain transformations - strip and lowercase
    result = tools.transform(text, ["strip", "lowercase"])
    print(f"After strip and lowercase: '{result}'")
    
    # Example 2: Parametrized text transformations
    text = "Hello World! This is a sample text that is quite long."
    print(f"\nOriginal text: '{text}'")
    
    # Truncate with ellipsis
    result = tools.transform(text, [{"function": "truncate", "length": 20}])
    print(f"Truncated to 20 chars: '{result}'")
    
    # Example 3: Regular expressions
    text = "User ID: ABC-12345, Order: XYZ-67890"
    print(f"\nOriginal text: '{text}'")
    
    # Extract user ID using regex
    result = tools.transform(text, [
        {"function": "regex", "pattern": r"User ID: ([A-Z]+-\d+)", "template": "{1}"}
    ])
    print(f"Extracted User ID: '{result}'")
    
    # Example 4: Text replacement
    text = "Hello world! This is a test."
    print(f"\nOriginal text: '{text}'")
    
    # Replace word
    result = tools.transform(text, [
        {"function": "replace", "find": "world", "replace": "Tukuy"}
    ])
    print(f"After replacement: '{result}'")

def html_transformation_examples():
    """Examples of HTML transformations using Tukuy."""
    print("\n===== HTML TRANSFORMATION EXAMPLES =====\n")
    
    # Create the transformer
    tools = ToolsTransformer()
    
    # Example 1: Simple HTML extraction
    html = """
    <html>
    <head><title>Tukuy Example</title></head>
    <body>
        <h1>Welcome to Tukuy</h1>
        <p>This is a <b>powerful</b> data transformation library.</p>
        <ul>
            <li><a href="https://example.com/features">Features</a></li>
            <li><a href="https://example.com/docs">Documentation</a></li>
            <li><a href="https://example.com/support">Support</a></li>
        </ul>
    </body>
    </html>
    """
    print("Original HTML: (truncated for readability)")
    
    # Extract text without HTML tags
    result = tools.transform(html, ["strip_html_tags"])
    print(f"\nText without HTML tags:\n'{result}'")
    
    # Example 2: Pattern-based HTML extraction
    print("\nPattern-based extraction:")
    
    pattern = {
        "properties": [
            {
                "name": "title",
                "selector": "h1",
                "transform": ["strip"]
            },
            {
                "name": "description",
                "selector": "p",
                "transform": ["strip", "strip_html_tags"]
            },
            {
                "name": "links",
                "selector": "a",
                "attribute": "href",
                "type": "array"
            },
            {
                "name": "link_texts",
                "selector": "a",
                "type": "array"
            }
        ]
    }
    
    try:
        data = tools.extract_html_with_pattern(html, pattern)
        print(f"\nExtracted title: '{data['title']}'")
        print(f"Extracted description: '{data['description']}'")
        print(f"Extracted links: {data['links']}")
        print(f"Extracted link texts: {data['link_texts']}")
    except (ValidationError, ParseError, TransformationError) as e:
        print(f"Error during pattern extraction: {e}")

def json_transformation_example():
    """Example of JSON transformations using Tukuy."""
    print("\n===== JSON TRANSFORMATION EXAMPLES =====\n")
    
    # Create the transformer
    tools = ToolsTransformer()
    
    # Example: JSON parsing and extraction
    json_str = """
    {
        "user": {
            "name": "John Doe",
            "email": "john@example.com",
            "profile": {
                "age": 30,
                "location": "New York",
                "interests": ["programming", "data science", "hiking"]
            }
        },
        "settings": {
            "theme": "dark",
            "notifications": true
        }
    }
    """
    
    # Parse JSON
    try:
        parsed = tools.transform(json_str, ["json_parse"])
        print("Parsed JSON:")
        print(f"User name: {parsed['user']['name']}")
        print(f"User interests: {parsed['user']['profile']['interests']}")
        print(f"Settings theme: {parsed['settings']['theme']}")
        
        # Pattern-based JSON extraction
        pattern = {
            "properties": [
                {
                    "name": "username",
                    "selector": "user.name"
                },
                {
                    "name": "email",
                    "selector": "user.email"
                },
                {
                    "name": "interests",
                    "selector": "user.profile.interests",
                    "type": "array"
                },
                {
                    "name": "preferences",
                    "selector": "settings",
                    "type": "object"
                }
            ]
        }
        
        data = tools.extract_json_with_pattern(json_str, pattern)
        print("\nExtracted data using pattern:")
        print(f"Username: {data['username']}")
        print(f"Email: {data['email']}")
        print(f"Interests: {data['interests']}")
        print(f"Preferences: {data['preferences']}")
        
    except (ValidationError, ParseError, TransformationError) as e:
        print(f"Error during JSON transformation: {e}")

def main():
    """Main function to run all examples."""
    print("=" * 50)
    print("TUKUY TRANSFORMATION LIBRARY - EXAMPLES")
    print("=" * 50)
    
    try:
        text_transformation_examples()
        html_transformation_examples()
        json_transformation_example()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("End of Tukuy examples")
    print("=" * 50)

if __name__ == "__main__":
    main()