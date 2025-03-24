"""Date transformation implementations."""

from datetime import datetime, date, timedelta
from typing import Optional

from ..base import ChainableTransformer
from ..types import TransformContext
from ..exceptions import ValidationError

class DateTransformer(ChainableTransformer[str, datetime]):
    """Parse date string into datetime object."""
    
    def __init__(self, name: str, format: str = '%Y-%m-%d'):
        super().__init__(name)
        self.format = format
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> datetime:
        try:
            return datetime.strptime(value, self.format)
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {str(e)}", value)

class TimezoneTransformer(ChainableTransformer[datetime, datetime]):
    """Convert datetime between timezones."""
    
    def __init__(self, name: str, to_zone: str, from_zone: Optional[str] = None):
        super().__init__(name)
        self.to_zone = to_zone
        self.from_zone = from_zone
    
    def validate(self, value: datetime) -> bool:
        return isinstance(value, datetime)
    
    def _transform(self, value: datetime, context: Optional[TransformContext] = None) -> datetime:
        # TODO: Implement timezone conversion
        return value

class DurationCalculator(ChainableTransformer[str, int]):
    """Calculate duration between dates."""
    
    def __init__(self, name: str, unit: str = 'days', format: str = '%Y-%m-%d', end: Optional[str] = None):
        super().__init__(name)
        self.unit = unit
        self.format = format
        self.end = end
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> int:
        try:
            start_date = datetime.strptime(value, self.format).date()
            end_date = datetime.strptime(self.end, self.format).date() if self.end else date.today()
            
            if self.unit == 'days':
                return (end_date - start_date).days
            elif self.unit == 'months':
                return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
            elif self.unit == 'years':
                return end_date.year - start_date.year
            else:
                raise ValidationError(f"Invalid unit: {self.unit}", value)
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {str(e)}", value)

class AgeCalculator(ChainableTransformer[str, int]):
    """Calculate age from birth date."""
    
    def __init__(self, name: str, reference_date: Optional[date] = None):
        super().__init__(name)
        self.reference_date = reference_date or date.today()
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> int:
        try:
            birth_date = datetime.strptime(value, '%Y-%m-%d').date()
            years = self.reference_date.year - birth_date.year
            if (self.reference_date.month, self.reference_date.day) < (birth_date.month, birth_date.day):
                years -= 1
            return years
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {str(e)}", value)
