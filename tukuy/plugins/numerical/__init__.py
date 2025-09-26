# numerical.py
# =========================================
# Tukuy Numerical transformation plugin
# =========================================
from __future__ import annotations

from ...base import ChainableTransformer
from ...plugins.base import TransformerPlugin
from ...types import TransformContext
from ...transformers.numerical import (
    # Type conversion
    IntegerTransformer,
    FloatTransformer,
    RoundTransformer,
    
    # Currency and unit conversion
    CurrencyConverter,
    UnitConverter,
    
    # Math operations
    MathOperationTransformer,
    PercentageCalculator,
    PowerTransformer,
    SqrtTransformer,
    LogTransformer,
    AbsTransformer,
    FloorTransformer,
    CeilTransformer,
    ClampTransformer,
    
    # Range and scaling
    ScaleTransformer,
    
    # Statistics and formatting
    StatsTransformer,
    FormatNumberTransformer,
    RandomNumberTransformer,
    
    # Number parsing
    parse_shorthand_number,
    ShorthandNumberTransformer,
    ShorthandDecimalTransformer,
    
    # Extraction
    ExtractNumbersTransformer,
)

class NumericalTransformersPlugin(TransformerPlugin):
    """Plugin providing comprehensive numerical transformation capabilities."""
    def __init__(self):
        super().__init__("numerical")
        
    @property
    def transformers(self):
        return {
            # Type conversion
            "int": lambda params: IntegerTransformer("int",
                min_value=params.get("min_value"),
                max_value=params.get("max_value")),
            "float": lambda params: FloatTransformer("float",
                min_value=params.get("min_value"),
                max_value=params.get("max_value")),
            "round": lambda params: RoundTransformer("round",
                decimals=params.get("decimals", 0)),
                
            # Currency/Unit/Math/Percentage
            "currency_convert": lambda params: CurrencyConverter("currency_convert",
                rate=params.get("rate")),
            "unit_convert": lambda params: UnitConverter("unit_convert",
                rate=params.get("rate")),
            "math_operation": lambda params: MathOperationTransformer("math_operation",
                operation=params.get("operation"),
                operand=params.get("operand")),
            "percentage_calc": lambda _: PercentageCalculator("percentage_calc"),

            # Shorthand numbers
            "shorthand_number": lambda params: ShorthandNumberTransformer(
                "shorthand_number",
                allow_currency=params.get("allow_currency", True),
                allow_percent=params.get("allow_percent", True),
                percent_base=params.get("percent_base", 1.0),
            ),
            "shorthand_decimal": lambda params: ShorthandDecimalTransformer(
                "shorthand_decimal",
                allow_currency=params.get("allow_currency", True),
                allow_percent=params.get("allow_percent", True),
                percent_base=params.get("percent_base", 1.0),
            ),

            # Extra numeric utilities
            "abs": lambda _: AbsTransformer("abs"),
            "floor": lambda _: FloorTransformer("floor"),
            "ceil": lambda _: CeilTransformer("ceil"),
            "clamp": lambda params: ClampTransformer("clamp",
                min_value=params.get("min_value"),
                max_value=params.get("max_value")),
            "scale": lambda params: ScaleTransformer("scale",
                src_min=params.get("src_min", 0),
                src_max=params.get("src_max", 1),
                dst_min=params.get("dst_min", 0),
                dst_max=params.get("dst_max", 1)),
            "stats": lambda _: StatsTransformer("stats"),
            "format_number": lambda params: FormatNumberTransformer("format_number",
                decimals=params.get("decimals", 2)),
            "random": lambda params: RandomNumberTransformer("random",
                min_value=params.get("min_value", 0),
                max_value=params.get("max_value", 1),
                seed=params.get("seed")),
            "pow": lambda params: PowerTransformer("pow",
                exponent=params.get("exponent", 2.0)),
            "sqrt": lambda _: SqrtTransformer("sqrt"),
            "log": lambda params: LogTransformer("log",
                base=params.get("base")),
            
            # Extraction
            "extract_numbers": lambda _: ExtractNumbersTransformer("extract_numbers"),
        }
        
    def initialize(self) -> None:
        super().initialize()
        # Load rates/metadata if needed
        
    def cleanup(self) -> None:
        super().cleanup()
        # Clean up caches if applicable
