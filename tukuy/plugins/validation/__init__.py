"""Validation transformation plugin."""

from ...base import BaseTransformer
from ...plugins.base import TransformerPlugin
from ...transformers.validation import (
    BooleanTransformer,
    EmailValidator,
    PhoneFormatter,
    CreditCardValidator,
    TypeEnforcer
)

class ValidationTransformersPlugin(TransformerPlugin):
    """Plugin providing validation transformation capabilities."""
    
    def __init__(self):
        """Initialize the validation transformers plugin."""
        super().__init__("validation")
        
    @property
    def transformers(self):
        """Get the validation transformers."""
        return {
            # Type validation
            'bool': lambda _: BooleanTransformer('bool'),
            'type_enforcer': lambda params: TypeEnforcer('type_enforcer',
                target_type=params.get('type')),
                
            # Format validation
            'email_validator': lambda params: EmailValidator('email_validator',
                allowed_domains=params.get('allowed_domains')),
            'phone_formatter': lambda params: PhoneFormatter('phone_formatter',
                format=params.get('format', '({area}) {prefix}-{line}')),
            'credit_card_check': lambda params: CreditCardValidator('credit_card_check',
                mask=params.get('mask', False)),
        }
        
    def initialize(self) -> None:
        """Initialize the validation transformers plugin."""
        super().initialize()
        # Could add loading of validation rules or patterns here
        
    def cleanup(self) -> None:
        """Clean up the validation transformers plugin."""
        super().cleanup()
        # Could add cleanup of any validation caches here
