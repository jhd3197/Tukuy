"""Transformer introspection and discovery functionality for Tukuy."""

import inspect
import re
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from logging import getLogger

from ..plugins import BUILTIN_PLUGINS
from ..plugins.base import PluginRegistry, TransformerPlugin

logger = getLogger(__name__)


class TransformerCategory(str, Enum):
    """Categories for classifying transformers."""

    TEXT_PROCESSING = "text_processing"
    DATA_VALIDATION = "data_validation"
    DATA_EXTRACTION = "data_extraction"
    FORMAT_CONVERSION = "format_conversion"
    MATHEMATICAL = "mathematical"
    PATTERN_MATCHING = "pattern_matching"
    UTILITY = "utility"


@dataclass
class TransformerParameter:
    """Represents a parameter for a transformer."""

    name: str
    param_type: str
    description: str = ""
    required: bool = False
    default_value: Any = None

    def __str__(self) -> str:
        default_str = f" = {self.default_value}" if self.default_value is not None else ""
        required_str = " (required)" if self.required else ""
        return f"{self.name}: {self.param_type}{default_str}{required_str}"


@dataclass
class TransformerMetadata:
    """Comprehensive metadata for a transformer."""

    name: str
    plugin: str
    description: str
    category: TransformerCategory
    version: str = "v1"
    status: str = "Production"
    input_type: str = "Any"
    output_type: str = "Any"
    parameters: List[TransformerParameter] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)

    def __str__(self) -> str:
        return f"{self.plugin}.{self.name}"

    def matches_filter(self, category_filter: Optional[str] = None,
                      input_type_filter: Optional[str] = None,
                      plugin_filter: Optional[str] = None) -> bool:
        """Check if this transformer matches the given filters."""

        if category_filter and self.category.value != category_filter:
            return False

        if input_type_filter and self.input_type != input_type_filter:
            return False

        if plugin_filter and self.plugin != plugin_filter:
            return False

        return True


class TransformerFormatter:
    """Formatter for displaying transformer information."""

    def __init__(self, max_description_length: int = 80, show_examples: bool = True):
        self.max_description_length = max_description_length
        self.show_examples = show_examples

    def format_transformer(self, metadata: TransformerMetadata) -> str:
        """Format a single transformer for display."""

        lines = []
        lines.append(f"\n{metadata.plugin}.{metadata.name}")
        lines.append("=" * (len(metadata.plugin) + len(metadata.name) + 1))

        # Description
        desc = metadata.description
        if len(desc) > self.max_description_length:
            desc = desc[:self.max_description_length - 3] + "..."
        lines.append(f"Description: {desc}")

        # Category, Version, Status
        lines.append(f"Category: {metadata.category.value}")
        lines.append(f"Version: {metadata.version}, Status: {metadata.status}")

        # Types
        lines.append(f"Input Type: {metadata.input_type}")
        lines.append(f"Output Type: {metadata.output_type}")

        # Parameters
        if metadata.parameters:
            lines.append("\nParameters:")
            for param in metadata.parameters:
                lines.append(f"  - {param}")
        else:
            lines.append("\nParameters: None")

        # Tags
        if metadata.tags:
            lines.append(f"\nTags: {', '.join(sorted(metadata.tags))}")

        # Examples
        if self.show_examples and metadata.examples:
            lines.append("\nExamples:")
            for i, example in enumerate(metadata.examples, 1):
                lines.append(f"  {i}. {example}")

        return "\n".join(lines)

    def format_transformer_list(self, transformers: List[TransformerMetadata],
                              show_details: bool = True) -> str:
        """Format a list of transformers for display."""

        if not transformers:
            return "No transformers found matching the specified criteria."

        lines = []
        lines.append(f"Found {len(transformers)} transformer(s):")
        lines.append("-" * 50)

        if not show_details:
            # Simple list format
            for metadata in sorted(transformers, key=lambda x: f"{x.plugin}.{x.name}"):
                desc = metadata.description
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                lines.append("11")
        else:
            # Detailed format
            for metadata in sorted(transformers, key=lambda x: f"{x.plugin}.{x.name}"):
                lines.append(self.format_transformer(metadata))
                lines.append("")  # Extra blank line between transformers

        return "\n".join(lines).rstrip()


class TransformerIntrospector:
    """Main class for transformer introspection and discovery."""

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """Initialize the introspector with a plugin registry."""

        if registry is None:
            # Create a registry with built-in plugins
            registry = PluginRegistry()
            for plugin_name, plugin_class in BUILTIN_PLUGINS.items():
                try:
                    plugin = plugin_class()
                    registry.register(plugin)
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")

        self.registry = registry
        self.formatter = TransformerFormatter()

    def extract_metadata_from_docstring(self, docstring: str) -> Dict[str, str]:
        """Extract metadata from a transformer docstring."""

        metadata = {}
        if not docstring:
            return metadata

        # Extract sections from docstring
        sections = re.split(r'\n\s*(?=[A-Z][a-z]+(?: [A-Z][a-z]+)*:)', docstring)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Look for key-value pairs
            if ':' in section:
                key, value = section.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                # Handle multiline values
                if key in ['description', 'version', 'status', 'last_updated']:
                    metadata[key] = value
                elif key == 'args' and 'Args:' in section:
                    metadata['args'] = value
                elif key == 'returns' and 'Returns:' in section:
                    metadata['returns'] = value

        return metadata

    def extract_examples_from_docstring(self, docstring: str) -> List[str]:
        """Extract examples from a transformer docstring."""

        examples = []
        if not docstring:
            return examples

        # Find Example sections
        example_pattern = r'Example(?::|\n)(\n?\s*)(.*?)(?=\n\s*[A-Z][a-z]+:|\n\s*$)'
        matches = re.finditer(example_pattern, docstring, re.DOTALL | re.IGNORECASE)

        for match in matches:
            example_content = match.group(2).strip()
            if example_content:
                # Clean up the example content
                example_lines = []
                for line in example_content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('```'):
                        example_lines.append(line)

                if example_lines:
                    examples.append('\n'.join(example_lines))

        return examples

    def infer_category_from_name_and_plugin(self, name: str, plugin_name: str) -> TransformerCategory:
        """Infer transformer category based on name and plugin."""

        # Category inference based on plugin
        plugin_category_map = {
            'text': TransformerCategory.TEXT_PROCESSING,
            'html': TransformerCategory.DATA_EXTRACTION,
            'json': TransformerCategory.DATA_EXTRACTION,
            'xml': TransformerCategory.DATA_EXTRACTION,
            'validation': TransformerCategory.DATA_VALIDATION,
            'numerical': TransformerCategory.MATHEMATICAL,
            'date': TransformerCategory.FORMAT_CONVERSION,
        }

        if plugin_name in plugin_category_map:
            return plugin_category_map[plugin_name]

        # Category inference based on name patterns
        name_lower = name.lower()
        if any(term in name_lower for term in ['strip', 'lower', 'upper', 'replace', 'template', 'regex', 'truncate']):
            return TransformerCategory.TEXT_PROCESSING
        elif any(term in name_lower for term in ['html_extract', 'json_extract', 'xml_extract']):
            return TransformerCategory.DATA_EXTRACTION
        elif any(term in name_lower for term in ['validate', 'is_valid']):
            return TransformerCategory.DATA_VALIDATION
        elif any(term in name_lower for term in ['parse', 'format', 'encode', 'decode']):
            return TransformerCategory.FORMAT_CONVERSION

        return TransformerCategory.UTILITY

    def extract_parameters_from_factory(self, factory_func: Callable) -> List[TransformerParameter]:
        """Extract parameters from a transformer factory function."""

        parameters = []
        try:
            # Get the signature of the factory function
            sig = inspect.signature(factory_func)

            for param_name, param in sig.parameters.items():
                # Skip 'self' parameter
                if param_name == 'self':
                    continue

                # Determine parameter type
                param_type = "any"
                if param.annotation != param.empty:
                    type_name = getattr(param.annotation, '__name__', str(param.annotation))
                    # Clean up type hints
                    type_name = re.sub(r'<class \'(.+)\'>', r'\1', type_name)
                    type_name = re.sub(r'typing\.(.+)', r'\1', type_name)
                    param_type = type_name

                # Check if parameter is required
                required = param.default == param.empty

                # Get default value
                default_value = None if param.default == param.empty else param.default

                parameters.append(TransformerParameter(
                    name=param_name,
                    param_type=param_type,
                    required=required,
                    default_value=default_value
                ))

        except Exception as e:
            logger.debug(f"Could not extract parameters from factory {factory_func}: {str(e)}")

        return parameters

    def get_transformer_metadata(self, name: str, plugin: TransformerPlugin,
                               factory_func: Callable) -> TransformerMetadata:
        """Extract metadata for a specific transformer."""

        try:
            # Try to instantiate the transformer to get its docstring
            transformer_instance = factory_func({"name": name})

            # Extract metadata from docstring
            docstring = transformer_instance.__doc__ or ""
            doc_metadata = self.extract_metadata_from_docstring(docstring)
            examples = self.extract_examples_from_docstring(docstring)

            # Extract description
            description = doc_metadata.get('description', 'No description available')

            # Extract version and status
            version = doc_metadata.get('version', 'v1')
            status = doc_metadata.get('status', 'Production')

            # Infer category
            category = self.infer_category_from_name_and_plugin(name, plugin.name)

            # Extract parameters
            parameters = self.extract_parameters_from_factory(factory_func)

            # Infer input/output types
            input_type = self._infer_input_type(transformer_instance)
            output_type = self._infer_output_type(transformer_instance)

            # Generate tags
            tags = self._generate_tags(name, plugin.name, category)

            return TransformerMetadata(
                name=name,
                plugin=plugin.name,
                description=description,
                category=category,
                version=version,
                status=status,
                input_type=input_type,
                output_type=output_type,
                parameters=parameters,
                examples=examples,
                tags=tags
            )

        except Exception as e:
            logger.warning(f"Could not extract metadata for transformer {plugin.name}.{name}: {str(e)}")

            # Return minimal metadata
            return TransformerMetadata(
                name=name,
                plugin=plugin.name,
                description=f"Transformer: {name}",
                category=self.infer_category_from_name_and_plugin(name, plugin.name),
                input_type="Any",
                output_type="Any",
                tags=self._generate_tags(name, plugin.name,
                                       self.infer_category_from_name_and_plugin(name, plugin.name))
            )

    def _infer_input_type(self, transformer_instance: Any) -> str:
        """Infer the input type from transformer type hints."""

        try:
            # Try to get type hints from the transformer class
            hints = getattr(transformer_instance.__class__, '__orig_bases__', [])
            for hint in hints:
                if hasattr(hint, '__origin__') and hasattr(hint, '__args__'):
                    # This is likely BaseTransformer[T, U]
                    if len(hint.__args__) >= 1:
                        input_type = hint.__args__[0]
                        if hasattr(input_type, '__name__'):
                            return input_type.__name__
                        elif str(input_type).startswith('typing.'):
                            return str(input_type).replace('typing.', '')
                        else:
                            return str(input_type)
        except Exception:
            pass

        # Fallback based on transformer class name
        class_name = transformer_instance.__class__.__name__.lower()
        if 'text' in class_name:
            return "str"
        elif 'json' in class_name or 'dict' in class_name:
            return "dict"
        elif 'html' in class_name:
            return "str"
        elif 'numeric' in class_name or 'number' in class_name:
            return "int|float"

        return "Any"

    def _infer_output_type(self, transformer_instance: Any) -> str:
        """Infer the output type from transformer type hints."""

        try:
            # Try to get type hints from the transformer class
            hints = getattr(transformer_instance.__class__, '__orig_bases__', [])
            for hint in hints:
                if hasattr(hint, '__origin__') and hasattr(hint, '__args__'):
                    # This is likely BaseTransformer[T, U]
                    if len(hint.__args__) >= 2:
                        output_type = hint.__args__[1]
                        if hasattr(output_type, '__name__'):
                            return output_type.__name__
                        elif str(output_type).startswith('typing.'):
                            return str(output_type).replace('typing.', '')
                        else:
                            return str(output_type)
        except Exception:
            pass

        # Fallback based on transformer class name
        class_name = transformer_instance.__class__.__name__.lower()
        if 'validation' in class_name:
            return "bool"
        elif 'extract' in class_name:
            return "dict"

        return "Any"

    def _generate_tags(self, name: str, plugin: str, category: TransformerCategory) -> Set[str]:
        """Generate tags for a transformer."""

        tags = set()

        # Add category tag
        tags.add(category.value.replace('_', '-'))

        # Add plugin tag
        tags.add(plugin.lower())

        # Add operation-based tags
        name_lower = name.lower()
        if any(word in name_lower for word in ['strip', 'trim']):
            tags.add('cleanup')
        elif any(word in name_lower for word in ['lower', 'upper']):
            tags.add('case-conversion')
        elif 'regex' in name_lower or 'pattern' in name_lower:
            tags.add('regex')
        elif 'extract' in name_lower or 'parse' in name_lower:
            tags.add('extraction')
        elif 'validate' in name_lower:
            tags.add('validation')
        elif 'format' in name_lower or 'template' in name_lower:
            tags.add('formatting')

        return tags

    def list_transformers(self,
                         category: Optional[str] = None,
                         input_type: Optional[str] = None,
                         plugin: Optional[str] = None,
                         format_output: bool = True) -> Union[List[TransformerMetadata], str]:
        """
        List all available transformers with optional filtering.

        Args:
            category: Filter by transformer category
            input_type: Filter by input type
            plugin: Filter by plugin source
            format_output: Whether to format the output as a string

        Returns:
            List of TransformerMetadata objects or formatted string
        """

        transformers = []

        # Iterate through all plugins
        for plugin_name, plugin_instance in self.registry.plugins.items():
            # Iterate through all transformers in each plugin
            for transformer_name, factory_func in plugin_instance.transformers.items():
                try:
                    # Get metadata for this transformer
                    metadata = self.get_transformer_metadata(
                        transformer_name, plugin_instance, factory_func
                    )

                    # Apply filters
                    if metadata.matches_filter(category, input_type, plugin):
                        transformers.append(metadata)

                except Exception as e:
                    logger.warning(f"Could not process transformer {plugin_name}.{transformer_name}: {str(e)}")

        # Sort transformers by plugin.name
        transformers.sort(key=lambda x: f"{x.plugin}.{x.name}")

        if format_output:
            return self.formatter.format_transformer_list(transformers)
        else:
            return transformers

    def get_transformer_details(self, transformer_name: str,
                              plugin_name: Optional[str] = None,
                              format_output: bool = True) -> Union[TransformerMetadata, str, None]:
        """
        Get detailed information about a specific transformer.

        Args:
            transformer_name: Name of the transformer
            plugin_name: Optional plugin name to scope the search
            format_output: Whether to format the output as a string

        Returns:
            TransformerMetadata object, formatted string, or None if not found
        """

        # Search through plugins
        for plugin_name_key, plugin_instance in self.registry.plugins.items():
            if plugin_name and plugin_name_key != plugin_name:
                continue

            # Look for the transformer in this plugin
            if transformer_name in plugin_instance.transformers:
                factory_func = plugin_instance.transformers[transformer_name]
                metadata = self.get_transformer_metadata(
                    transformer_name, plugin_instance, factory_func
                )

                if format_output:
                    return self.formatter.format_transformer(metadata)
                else:
                    return metadata

        return None

    def list_categories(self) -> List[str]:
        """Get list of available transformer categories."""

        return [category.value for category in TransformerCategory]

    def list_plugins(self) -> List[str]:
        """Get list of available plugins."""

        return list(self.registry.plugins.keys())


def list_transformers(category: Optional[str] = None,
                     input_type: Optional[str] = None,
                     plugin: Optional[str] = None) -> str:
    """
    Command-line interface function to list transformers.

    Args:
        category: Filter by transformer category
        input_type: Filter by input type
        plugin: Filter by plugin source

    Returns:
        Formatted string listing transformers
    """

    introspector = TransformerIntrospector()
    return introspector.list_transformers(category, input_type, plugin)


def show_transformer(name: str, plugin: Optional[str] = None) -> str:
    """
    Command-line interface function to show transformer details.

    Args:
        name: Name of the transformer
        plugin: Optional plugin name

    Returns:
        Formatted string with transformer details
    """

    introspector = TransformerIntrospector()

    if plugin:
        result = introspector.get_transformer_details(name, plugin)
    else:
        result = introspector.get_transformer_details(name)

    if result is None:
        return f"Transformer '{name}' not found."

    return result if isinstance(result, str) else introspector.formatter.format_transformer(result)


# CLI integration hooks
def register_cli_commands():
    """
    Register CLI commands for transformer introspection.

    This function should be called by CLI frameworks to register
    the introspection commands.
    """

    # This is a hook that CLI frameworks can call to register commands
    # Actual implementation would depend on the CLI framework used

    commands = {
        'list-transformers': {
            'function': list_transformers,
            'description': 'List all available transformers',
            'parameters': [
                {'name': 'category', 'type': str, 'help': 'Filter by category'},
                {'name': 'input_type', 'type': str, 'help': 'Filter by input type'},
                {'name': 'plugin', 'type': str, 'help': 'Filter by plugin'}
            ]
        },
        'show-transformer': {
            'function': show_transformer,
            'description': 'Show detailed information about a specific transformer',
            'parameters': [
                {'name': 'name', 'type': str, 'help': 'Transformer name', 'required': True},
                {'name': 'plugin', 'type': str, 'help': 'Plugin name'}
            ]
        }
    }

    return commands


__all__ = [
    'TransformerCategory',
    'TransformerParameter',
    'TransformerMetadata',
    'TransformerFormatter',
    'TransformerIntrospector',
    'list_transformers',
    'show_transformer',
    'register_cli_commands'
]