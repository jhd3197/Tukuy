"""Tukuy - A flexible data transformation library with a plugin system."""

from .transformers import TukuyTransformer
from .base import BaseTransformer, ChainableTransformer
from .plugins.base import TransformerPlugin, PluginRegistry
from .exceptions import ValidationError, TransformationError
from .types import TransformContext, TransformResult

# New decorator-based registration system
from .core.registration import (
    tukuy_plugin,
    transformer,
    register_plugin,
    hot_reload,
    get_plugin_info,
    extract_metadata
)

__version__ = '0.1.0'

__all__ = [
    'TukuyTransformer',
    'BaseTransformer',
    'ChainableTransformer',
    'TransformerPlugin',
    'PluginRegistry',
    'ValidationError',
    'TransformationError',
    'TransformContext',
    'TransformResult',
    # New registration system
    'tukuy_plugin',
    'transformer',
    'register_plugin',
    'hot_reload',
    'get_plugin_info',
    'extract_metadata',
]
