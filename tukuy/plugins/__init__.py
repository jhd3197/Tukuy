"""Plugin system for Tukuy transformers."""

from .base import TransformerPlugin, PluginRegistry
from .text import TextTransformersPlugin
from .html import HtmlTransformersPlugin
from .date import DateTransformersPlugin
from .validation import ValidationTransformersPlugin
from .numerical import NumericalTransformersPlugin
from .json import JsonTransformersPlugin
from .crypto import CryptoPlugin
from .llm import LlmPlugin
from .conversion import ConversionPlugin
from .file_ops import FileOpsPlugin
from .shell import ShellPlugin
from .http import HttpPlugin
from .web import WebPlugin
from .code_extract import CodeExtractPlugin
from .html_validate import HtmlValidatePlugin
from .color import ColorPlugin
from .minify import MinifyPlugin
from .env import EnvPlugin
from .diff import DiffPlugin
from .schema import SchemaPlugin
from .markdown import MarkdownPlugin
from .image import ImagePlugin
from .compression import CompressionPlugin
from .git import GitPlugin
from .sql import SqlPlugin
from .prompt import PromptPlugin

# Built-in plugins
BUILTIN_PLUGINS = {
    'text': TextTransformersPlugin,
    'html': HtmlTransformersPlugin,
    'date': DateTransformersPlugin,
    'validation': ValidationTransformersPlugin,
    'numerical': NumericalTransformersPlugin,
    'json': JsonTransformersPlugin,
    'crypto': CryptoPlugin,
    'llm': LlmPlugin,
    'conversion': ConversionPlugin,
    'file_ops': FileOpsPlugin,
    'shell': ShellPlugin,
    'http': HttpPlugin,
    'web': WebPlugin,
    'code_extract': CodeExtractPlugin,
    'html_validate': HtmlValidatePlugin,
    'color': ColorPlugin,
    'minify': MinifyPlugin,
    'env': EnvPlugin,
    'diff': DiffPlugin,
    'schema': SchemaPlugin,
    'markdown': MarkdownPlugin,
    'image': ImagePlugin,
    'compression': CompressionPlugin,
    'git': GitPlugin,
    'sql': SqlPlugin,
    'prompt': PromptPlugin,
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
    'CryptoPlugin',
    'LlmPlugin',
    'ConversionPlugin',
    'FileOpsPlugin',
    'ShellPlugin',
    'HttpPlugin',
    'WebPlugin',
    'CodeExtractPlugin',
    'HtmlValidatePlugin',
    'ColorPlugin',
    'MinifyPlugin',
    'EnvPlugin',
    'DiffPlugin',
    'SchemaPlugin',
    'MarkdownPlugin',
    'ImagePlugin',
    'CompressionPlugin',
    'GitPlugin',
    'SqlPlugin',
    'PromptPlugin',
    'BUILTIN_PLUGINS',
]
