"""Plugin system for Tukuy transformers."""

import importlib
from typing import Iterator, Tuple, Type

from .base import TransformerPlugin, PluginRegistry


# ---------------------------------------------------------------------------
# Lazy built-in plugin loading
# ---------------------------------------------------------------------------

_BUILTIN_PLUGIN_PATHS = {
    'text': ('tukuy.plugins.text', 'TextTransformersPlugin'),
    'html': ('tukuy.plugins.html', 'HtmlTransformersPlugin'),
    'date': ('tukuy.plugins.date', 'DateTransformersPlugin'),
    'validation': ('tukuy.plugins.validation', 'ValidationTransformersPlugin'),
    'numerical': ('tukuy.plugins.numerical', 'NumericalTransformersPlugin'),
    'json': ('tukuy.plugins.json', 'JsonTransformersPlugin'),
    'crypto': ('tukuy.plugins.crypto', 'CryptoPlugin'),
    'llm': ('tukuy.plugins.llm', 'LlmPlugin'),
    'conversion': ('tukuy.plugins.conversion', 'ConversionPlugin'),
    'file_ops': ('tukuy.plugins.file_ops', 'FileOpsPlugin'),
    'shell': ('tukuy.plugins.shell', 'ShellPlugin'),
    'http': ('tukuy.plugins.http', 'HttpPlugin'),
    'web': ('tukuy.plugins.web', 'WebPlugin'),
    'code_extract': ('tukuy.plugins.code_extract', 'CodeExtractPlugin'),
    'html_validate': ('tukuy.plugins.html_validate', 'HtmlValidatePlugin'),
    'color': ('tukuy.plugins.color', 'ColorPlugin'),
    'minify': ('tukuy.plugins.minify', 'MinifyPlugin'),
    'encoding': ('tukuy.plugins.encoding', 'EncodingPlugin'),
    'env': ('tukuy.plugins.env', 'EnvPlugin'),
    'diff': ('tukuy.plugins.diff', 'DiffPlugin'),
    'schema': ('tukuy.plugins.schema', 'SchemaPlugin'),
    'markdown': ('tukuy.plugins.markdown', 'MarkdownPlugin'),
    'image': ('tukuy.plugins.image', 'ImagePlugin'),
    'compression': ('tukuy.plugins.compression', 'CompressionPlugin'),
    'git': ('tukuy.plugins.git', 'GitPlugin'),
    'sql': ('tukuy.plugins.sql', 'SqlPlugin'),
    'prompt': ('tukuy.plugins.prompt', 'PromptPlugin'),
    'pdf': ('tukuy.plugins.pdf', 'PdfPlugin'),
    'xlsx': ('tukuy.plugins.xlsx', 'XlsxPlugin'),
    'docx': ('tukuy.plugins.docx', 'DocxPlugin'),
    'mermaid': ('tukuy.plugins.mermaid', 'MermaidPlugin'),
    'csv': ('tukuy.plugins.csv_plugin', 'CsvPlugin'),
    'yaml': ('tukuy.plugins.yaml_plugin', 'YamlPlugin'),
    'xml': ('tukuy.plugins.xml_plugin', 'XmlPlugin'),
    'local_plugins': ('tukuy.plugins.local_plugins', 'LocalPluginsPlugin'),
    'feedback': ('tukuy.plugins.feedback', 'FeedbackPlugin'),
    'currency': ('tukuy.plugins.currency', 'CurrencyPlugin'),
    'weather': ('tukuy.plugins.weather', 'WeatherPlugin'),
    'country': ('tukuy.plugins.country', 'CountryPlugin'),
    'qrcode': ('tukuy.plugins.qrcode', 'QrCodePlugin'),
    'translate': ('tukuy.plugins.translate', 'TranslatePlugin'),
    'geocoding': ('tukuy.plugins.geocoding', 'GeocodingPlugin'),
    'coingecko': ('tukuy.plugins.coingecko', 'CoinGeckoPlugin'),
    'google_maps': ('tukuy.plugins.google_maps', 'GoogleMapsPlugin'),
    'yelp': ('tukuy.plugins.yelp', 'YelpPlugin'),
    'newsapi': ('tukuy.plugins.newsapi', 'NewsApiPlugin'),
    'finnhub': ('tukuy.plugins.finnhub', 'FinnhubPlugin'),
    'ticketmaster': ('tukuy.plugins.ticketmaster', 'TicketmasterPlugin'),
    'spotify': ('tukuy.plugins.spotify', 'SpotifyPlugin'),
    'amadeus': ('tukuy.plugins.amadeus', 'AmadeusPlugin'),
    'google_calendar': ('tukuy.plugins.google_calendar', 'GoogleCalendarPlugin'),
    'twilio': ('tukuy.plugins.twilio', 'TwilioPlugin'),
}


class _LazyBuiltinPlugins:
    """Dict-like object that imports plugin classes on first access.

    This avoids importing every plugin module (and their heavy
    dependencies like PIL, openpyxl, etc.) at ``import tukuy`` time.
    """

    def __init__(self):
        self._loaded: dict = {}

    def _load(self, key: str) -> Type[TransformerPlugin]:
        if key not in self._loaded:
            module_path, class_name = _BUILTIN_PLUGIN_PATHS[key]
            module = importlib.import_module(module_path)
            self._loaded[key] = getattr(module, class_name)
        return self._loaded[key]

    def __getitem__(self, key: str) -> Type[TransformerPlugin]:
        if key not in _BUILTIN_PLUGIN_PATHS:
            raise KeyError(key)
        return self._load(key)

    def __contains__(self, key: object) -> bool:
        return key in _BUILTIN_PLUGIN_PATHS

    def __iter__(self) -> Iterator[str]:
        return iter(_BUILTIN_PLUGIN_PATHS)

    def __len__(self) -> int:
        return len(_BUILTIN_PLUGIN_PATHS)

    def keys(self):
        return _BUILTIN_PLUGIN_PATHS.keys()

    def values(self):
        return [self[k] for k in _BUILTIN_PLUGIN_PATHS]

    def items(self) -> Iterator[Tuple[str, Type[TransformerPlugin]]]:
        for key in _BUILTIN_PLUGIN_PATHS:
            yield key, self[key]

    def get(self, key: str, default=None):
        if key in _BUILTIN_PLUGIN_PATHS:
            return self._load(key)
        return default


BUILTIN_PLUGINS = _LazyBuiltinPlugins()


__all__ = [
    'TransformerPlugin',
    'PluginRegistry',
    'BUILTIN_PLUGINS',
]
