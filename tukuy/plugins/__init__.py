"""Plugin system for Tukuy transformers."""

from .base import TransformerPlugin, PluginRegistry
from .text import TextTransformersPlugin
from .html import HtmlTransformersPlugin
from .date import DateTransformersPlugin
from .validation import ValidationTransformersPlugin
from .numerical import NumericalTransformersPlugin
from .json import JsonTransformersPlugin

# Built-in plugins
BUILTIN_PLUGINS = {
    'text': TextTransformersPlugin,
    'html': HtmlTransformersPlugin,
    'date': DateTransformersPlugin,
    'validation': ValidationTransformersPlugin,
    'numerical': NumericalTransformersPlugin,
    'json': JsonTransformersPlugin,
}

__all__ = [
    'TransformerPlugin',
    'PluginRegistry',
    'TextTransformersPlugin',
    'HtmlTransformersPlugin',
    'DateTransformersPlugin',
    'ValidationTransformersPlugin',
    'NumericalTransformersPlugin',
    'JsonTransformersPlugin',
    'BUILTIN_PLUGINS',
]
