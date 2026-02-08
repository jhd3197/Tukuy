# Backward-compatibility shim -- canonical home is tukuy.plugins.text
from ..base import RegexTransformer, ReplaceTransformer
from ..plugins.text import (
    StripTransformer,
    LowercaseTransformer,
    UppercaseTransformer,
    TemplateTransformer,
    MapTransformer,
    SplitTransformer,
    TitleCaseTransformer,
    CamelCaseTransformer,
    SnakeCaseTransformer,
    SlugifyTransformer,
    TruncateTransformer,
    RemoveEmojisTransformer,
    RedactSensitiveTransformer,
)
