"""Instruction packs -- curated sets of LLM-powered tools.

Each pack is a :class:`TransformerPlugin` that exposes its instructions via
the ``instructions`` property. The registry automatically surfaces them as
both instructions *and* skills so bots can discover and invoke them.
"""

from .analysis import AnalysisInstructionPack
from .business import BusinessInstructionPack
from .creative import CreativeInstructionPack
from .developer import DeveloperInstructionPack
from .education import EducationInstructionPack
from .hr import HRInstructionPack
from .marketing import MarketingInstructionPack
from .sales import SalesInstructionPack
from .social_media import SocialMediaInstructionPack
from .writing import WritingInstructionPack

__all__ = [
    "AnalysisInstructionPack",
    "BusinessInstructionPack",
    "CreativeInstructionPack",
    "DeveloperInstructionPack",
    "EducationInstructionPack",
    "HRInstructionPack",
    "MarketingInstructionPack",
    "SalesInstructionPack",
    "SocialMediaInstructionPack",
    "WritingInstructionPack",
]
