"""Date transformation plugin."""

from datetime import date
from typing import Optional

from ...base import BaseTransformer
from ...plugins.base import TransformerPlugin
from ...transformers.date import (
    DateTransformer,
    TimezoneTransformer,
    DurationCalculator,
    AgeCalculator
)

class DateTransformersPlugin(TransformerPlugin):
    """Plugin providing date transformation capabilities."""
    
    def __init__(self):
        """Initialize the date transformers plugin."""
        super().__init__("date")
        
    @property
    def transformers(self):
        """Get the date transformers."""
        return {
            # Date parsing
            'date': lambda params: DateTransformer('date',
                format=params.get('format', '%Y-%m-%d')),
                
            # Timezone conversion
            'timezone_convert': lambda params: TimezoneTransformer('timezone_convert',
                to_zone=params.get('to_zone'),
                from_zone=params.get('from_zone')),
                
            # Date calculations
            'duration_calc': lambda params: DurationCalculator('duration_calc',
                unit=params.get('unit', 'days'),
                format=params.get('format', '%Y-%m-%d'),
                end=params.get('end')),
                
            'age_calc': lambda params: AgeCalculator('age_calc',
                reference_date=params.get('reference_date')),
        }
        
    def initialize(self) -> None:
        """Initialize the date transformers plugin."""
        super().initialize()
        # Could add loading of timezone data or date formats here
        
    def cleanup(self) -> None:
        """Clean up the date transformers plugin."""
        super().cleanup()
        # Could add cleanup of any date caches here
