"""Instruction packs -- curated sets of LLM-powered tools.

Each pack is a :class:`TransformerPlugin` that exposes its instructions via
the ``instructions`` property. The registry automatically surfaces them as
both instructions *and* skills so bots can discover and invoke them.
"""

from .analysis import AnalysisInstructionPack
from .business import BusinessInstructionPack
from .creative import CreativeInstructionPack
from .customer_support import CustomerSupportInstructionPack
from .data import DataInstructionPack
from .developer import DeveloperInstructionPack
from .education import EducationInstructionPack
from .finance import FinanceInstructionPack
from .hr import HRInstructionPack
from .legal import LegalInstructionPack
from .marketing import MarketingInstructionPack
from .product import ProductInstructionPack
from .sales import SalesInstructionPack
from .social_media import SocialMediaInstructionPack
from .writing import WritingInstructionPack

__all__ = [
    "AnalysisInstructionPack",
    "BusinessInstructionPack",
    "CreativeInstructionPack",
    "CustomerSupportInstructionPack",
    "DataInstructionPack",
    "DeveloperInstructionPack",
    "EducationInstructionPack",
    "FinanceInstructionPack",
    "HRInstructionPack",
    "LegalInstructionPack",
    "MarketingInstructionPack",
    "ProductInstructionPack",
    "SalesInstructionPack",
    "SocialMediaInstructionPack",
    "WritingInstructionPack",
]
