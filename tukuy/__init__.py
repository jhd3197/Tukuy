"""Tukuy - A flexible data transformation library with a plugin system."""

from .transformers import TukuyTransformer, AsyncTukuyTransformer
from .base import BaseTransformer, ChainableTransformer
from .async_base import AsyncBaseTransformer, AsyncChainableTransformer
from .plugins.base import TransformerPlugin, PluginRegistry, PluginSource
from .exceptions import ValidationError, TransformationError
from .types import TransformContext, TransformResult
from .skill import (
    RiskLevel, ConfigScope, ConfigParam,
    SkillDescriptor, SkillExample, SkillResult, Skill, skill,
)
from .context import SkillContext
from .manifest import PluginManifest, PluginRequirements
from .availability import (
    AvailabilityReason, SkillAvailability, PluginDiscoveryResult,
    get_available_skills, discover_plugins,
)
from .bridges import (
    to_openai_tool, to_anthropic_tool,
    to_openai_tools, to_anthropic_tools,
    format_result_openai, format_result_anthropic,
    dispatch_openai, dispatch_anthropic,
    async_dispatch_openai, async_dispatch_anthropic,
)
from .chain import Chain, Branch, Parallel, branch, parallel
from .safety import (
    SafetyViolation, SafetyError, SafetyManifest, SafetyPolicy,
    set_policy, get_policy, reset_policy,
    SecurityError, SecurityContext,
    set_security_context, get_security_context, reset_security_context,
)

# Two-phase discovery
from .core.unified import browse_tools, get_tool_details, search_tools

__version__ = '0.0.17'

__all__ = [
    # Core
    'TukuyTransformer',
    'AsyncTukuyTransformer',
    'BaseTransformer',
    'ChainableTransformer',
    'AsyncBaseTransformer',
    'AsyncChainableTransformer',
    # Plugin system
    'TransformerPlugin',
    'PluginRegistry',
    'PluginSource',
    # Errors & types
    'ValidationError',
    'TransformationError',
    'TransformContext',
    'TransformResult',
    # Skill system
    'RiskLevel',
    'ConfigScope',
    'ConfigParam',
    'SkillDescriptor',
    'SkillExample',
    'SkillResult',
    'Skill',
    'skill',
    'SkillContext',
    # Plugin manifest
    'PluginManifest',
    'PluginRequirements',
    # Availability engine
    'AvailabilityReason',
    'SkillAvailability',
    'PluginDiscoveryResult',
    'get_available_skills',
    'discover_plugins',
    # Agent bridges
    'to_openai_tool',
    'to_anthropic_tool',
    'to_openai_tools',
    'to_anthropic_tools',
    'format_result_openai',
    'format_result_anthropic',
    'dispatch_openai',
    'dispatch_anthropic',
    'async_dispatch_openai',
    'async_dispatch_anthropic',
    # Composition
    'Chain',
    'Branch',
    'Parallel',
    'branch',
    'parallel',
    # Safety
    'SafetyViolation',
    'SafetyError',
    'SafetyManifest',
    'SafetyPolicy',
    'set_policy',
    'get_policy',
    'reset_policy',
    # Security
    'SecurityError',
    'SecurityContext',
    'set_security_context',
    'get_security_context',
    'reset_security_context',
    # Two-phase discovery
    'browse_tools',
    'get_tool_details',
    'search_tools',
]
