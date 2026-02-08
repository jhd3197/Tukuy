"""Date transformation implementations."""

from datetime import datetime, date, timedelta
from typing import Optional

from ..base import ChainableTransformer
from ..types import TransformContext
from ..exceptions import ValidationError

class DateTransformer(ChainableTransformer[str, datetime]):
    """
    Description:
        A transformer that parses date strings into datetime objects using a specified
        format string. Uses Python's datetime.strptime for robust date parsing.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        ``format`` (str): Date format string using strftime/strptime codes (default: '%Y-%m-%d')
    
    Returns:
        datetime: The parsed datetime object
    
    Raises:
        ValidationError: If the input value is not a string or doesn't match the format
    
    Notes:
        Format codes:
        - %Y: Year with century (e.g., 2024)
        - %m: Month as zero-padded number (01-12)
        - %d: Day as zero-padded number (01-31)
        - %H: Hour (00-23)
        - %M: Minute (00-59)
        - %S: Second (00-59)
        See Python's datetime documentation for more codes.
    
    Example::

        # Basic date parsing
        transformer = DateTransformer("date_parser")
        result = transformer.transform("2024-03-24")
        assert result.value.year == 2024
        assert result.value.month == 3
        assert result.value.day == 24

        # Custom ``format``
        custom = DateTransformer(
            "custom_date",
            format="%d/%m/%Y %H:%M"
        )
        result = custom.transform("24/03/2024 15:30")
        assert result.value.hour == 15
        assert result.value.minute == 30

        # Chain with other transformers
        duration = DurationCalculator(
            "days_since",
            unit="days"
        )
        pipeline = transformer.chain(duration)
    """
    
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

class DurationCalculator(ChainableTransformer[str, int]):
    """
    Description:
        A transformer that calculates the duration between two dates in various units
        (days, months, or years). If no end date is provided, uses today's date.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        unit (str): Unit for duration calculation (``days``, ``months``, or ``years``)
        ``format`` (str): Date format string for parsing dates (default: '%Y-%m-%d')
        end (Optional[str]): End date string. If not provided, uses today's date
    
    Returns:
        int: The duration between dates in the specified unit
    
    Raises:
        ValidationError: If the input value is not a string, doesn't match the ``format``,
            or if an invalid ``unit`` is specified
    
    Notes:
        - For ``months``, calculates full months between dates
        - For ``years``, calculates full years between dates
        - Negative durations are possible if end date is before start date
    
    Example::

        # Calculate days between dates
        transformer = DurationCalculator(
            "days_between",
            unit="days",
            format="%Y-%m-%d"
        )
        result = transformer.transform("2024-01-01")  # to today
        assert isinstance(result.value, int)

        # Calculate months with specific end date
        months = DurationCalculator(
            "months_between",
            unit="months",
            format="%Y-%m-%d",
            end="2024-12-31"
        )
        result = months.transform("2024-01-01")
        assert result.value == 11  # Jan to Dec = 11 months

        # Calculate years
        years = DurationCalculator(
            "years_between",
            unit="years",
            format="%Y-%m-%d"
        )
        result = years.transform("2020-03-24")  # to today
        assert result.value == 4

        # Chain with other transformers
        format_result = StringFormatTransformer(
            "format",
            template="{} days old"
        )
        pipeline = transformer.chain(format_result)

        result = pipeline.transform("2024-01-01")
        assert "days old" in result.value
    """
    
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
    """
    Description:
        A transformer that calculates age in years from a birth date, taking into
        account the month and day to ensure accurate age calculation. Uses a reference
        date (defaults to today) for the calculation.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        ``name`` (str): Unique identifier for this transformer
        ``reference_date`` (Optional[date]): Date to calculate age against (default: today)

    Returns:
        int: The calculated age in years

    Raises:
        ValidationError: If the input value is not a string or doesn't match the format

    Notes:
        - Uses YYYY-MM-DD format for birth date
        - Handles leap years correctly
        - Subtracts one year if birthday hasn't occurred yet in reference year
        - Returns negative age if birth date is in the future

    Example::

        # Calculate age using today's date
        transformer = AgeCalculator("age")
        result = transformer.transform("1990-03-24")
        assert result.value == 34  # as of 2024-03-24

        # Calculate age at specific date
        specific = AgeCalculator(
            "age_at_date",
            reference_date=date(2020, 1, 1)
        )
        result = specific.transform("1990-03-24")
        assert result.value == 29  # not 30 yet in January

        # Handle future dates
        future = AgeCalculator("future_age")
        result = future.transform("2025-01-01")
        assert result.value < 0  # negative age for future date

        # Chain with other transformers
        format_age = StringFormatTransformer(
            "format",
            template="Age: {} years"
        )
        pipeline = transformer.chain(format_age)

        result = pipeline.transform("1990-03-24")
        assert result.value == "Age: 34 years"
    """
    
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
