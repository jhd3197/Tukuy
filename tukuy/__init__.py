"""Tukuy - A flexible data transformation library with a plugin system."""

from .transformers import TukuyTransformer, AsyncTukuyTransformer
from .base import BaseTransformer, ChainableTransformer
from .async_base import AsyncBaseTransformer, AsyncChainableTransformer, AsyncCompositeTransformer
from .plugins.base import TransformerPlugin, PluginRegistry
from .exceptions import ValidationError, TransformationError
from .types import TransformContext, TransformResult
from .skill import SkillDescriptor, SkillExample, SkillResult, Skill, skill
from .context import SkillContext
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
)

# New decorator-based registration system
from .core.registration import (
    tukuy_plugin,
    transformer,
    register_plugin,
    hot_reload,
    get_plugin_info,
    extract_metadata
)

__version__ = '0.1.0'

__all__ = [
    'TukuyTransformer',
    'AsyncTukuyTransformer',
    'BaseTransformer',
    'ChainableTransformer',
    'AsyncBaseTransformer',
    'AsyncChainableTransformer',
    'AsyncCompositeTransformer',
    'TransformerPlugin',
    'PluginRegistry',
    'ValidationError',
    'TransformationError',
    'TransformContext',
    'TransformResult',
    # Skill system
    'SkillDescriptor',
    'SkillExample',
    'SkillResult',
    'Skill',
    'skill',
    # Context
    'SkillContext',
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
    # New registration system
    'tukuy_plugin',
    'transformer',
    'register_plugin',
    'hot_reload',
    'get_plugin_info',
    'extract_metadata',
]
