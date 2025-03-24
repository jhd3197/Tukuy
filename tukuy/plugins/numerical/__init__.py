"""Numerical transformation plugin."""

import re
from decimal import Decimal

from ...base import BaseTransformer, ChainableTransformer
from ...plugins.base import TransformerPlugin
from ...types import TransformContext
from ...transformers.numerical import (
    IntegerTransformer,
    FloatTransformer,
    RoundTransformer,
    CurrencyConverter,
    UnitConverter,
    MathOperationTransformer,
    PercentageCalculator
)

class ExtractNumbersTransformer(ChainableTransformer[str, list]):
    """Extracts all numbers from text."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.pattern = re.compile(r'\d+(?:\.\d+)?')
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: TransformContext = None) -> list:
        return self.pattern.findall(value)

class NumericalTransformersPlugin(TransformerPlugin):
    """Plugin providing numerical transformation capabilities."""
    
    def __init__(self):
        """Initialize the numerical transformers plugin."""
        super().__init__("numerical")
        
    @property
    def transformers(self):
        """Get the numerical transformers."""
        return {
            # Type conversion
            'int': lambda params: IntegerTransformer('int',
                min_value=params.get('min_value'),
                max_value=params.get('max_value')),
            'float': lambda params: FloatTransformer('float',
                min_value=params.get('min_value'),
                max_value=params.get('max_value')),
                
            # Number formatting
            'round': lambda params: RoundTransformer('round',
                decimals=params.get('decimals', 0)),
                
            # Conversions
            'currency_convert': lambda params: CurrencyConverter('currency_convert',
                rate=params.get('rate')),
            'unit_convert': lambda params: UnitConverter('unit_convert',
                rate=params.get('rate')),
                
            # Calculations
            'math_operation': lambda params: MathOperationTransformer('math_operation',
                operation=params.get('operation'),
                operand=params.get('operand')),
            'percentage_calc': lambda _: PercentageCalculator('percentage_calc'),
            
            # Extraction
            'extract_numbers': lambda _: ExtractNumbersTransformer('extract_numbers'),
        }
        
    def initialize(self) -> None:
        """Initialize the numerical transformers plugin."""
        super().initialize()
        # Could add loading of currency rates or unit conversion data here
        
    def cleanup(self) -> None:
        """Clean up the numerical transformers plugin."""
        super().cleanup()
        # Could add cleanup of any numerical caches here
