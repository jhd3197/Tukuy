"""Tests for Phase 6: Context System (SkillContext).

Covers:
  - SkillContext: typed get/set, has/delete, update, snapshot, merge
  - Scoping: namespace isolation, nested scopes, parent read-through
  - Lifecycle: from_dict, to_dict, bridge with plain dicts
  - Skill integration: auto-injection of SkillContext via @skill decorator
  - Chain integration: context flows through Chain, Branch, Parallel
  - Parallel isolation: each parallel branch gets a scoped context
  - Async variants: arun with context-aware skills
"""

import asyncio

import pytest

from tukuy.context import SkillContext
from tukuy.skill import Skill, SkillDescriptor, SkillResult, skill
from tukuy.chain import Chain, Branch, Parallel, branch, parallel


# ---------------------------------------------------------------------------
# SkillContext basics
# ---------------------------------------------------------------------------

class TestSkillContextBasics:
    """Core get/set/has/delete operations."""

    def test_get_set(self):
        ctx = SkillContext()
        ctx.set("name", "alice")
        assert ctx.get("name") == "alice"

    def test_get_default(self):
        ctx = SkillContext()
        assert ctx.get("missing") is None
        assert ctx.get("missing", 42) == 42

    def test_has(self):
        ctx = SkillContext()
        assert not ctx.has("x")
        ctx.set("x", 1)
        assert ctx.has("x")

    def test_contains(self):
        ctx = SkillContext()
        ctx.set("a", True)
        assert "a" in ctx
        assert "b" not in ctx

    def test_delete(self):
        ctx = SkillContext()
        ctx.set("x", 1)
        ctx.delete("x")
        assert not ctx.has("x")

    def test_delete_missing_is_noop(self):
        ctx = SkillContext()
        ctx.delete("nonexistent")  # should not raise

    def test_update(self):
        ctx = SkillContext()
        ctx.update({"a": 1, "b": 2})
        assert ctx.get("a") == 1
        assert ctx.get("b") == 2

    def test_len(self):
        ctx = SkillContext()
        assert len(ctx) == 0
        ctx.set("x", 1)
        assert len(ctx) == 1
        ctx.set("y", 2)
        assert len(ctx) == 2

    def test_keys(self):
        ctx = SkillContext()
        ctx.set("a", 1)
        ctx.set("b", 2)
        assert set(ctx.keys()) == {"a", "b"}

    def test_initial_data(self):
        ctx = SkillContext({"x": 10, "y": 20})
        assert ctx.get("x") == 10
        assert ctx.get("y") == 20

    def test_repr(self):
        ctx = SkillContext()
        ctx.set("a", 1)
        r = repr(ctx)
        assert "SkillContext" in r
        assert "a" in r

    def test_none_value(self):
        """Setting a key to None should be retrievable and distinct from missing."""
        ctx = SkillContext()
        ctx.set("val", None)
        assert ctx.has("val")
        assert ctx.get("val") is None
        assert ctx.get("val", "default") is None


# ---------------------------------------------------------------------------
# Scoping
# ---------------------------------------------------------------------------

class TestSkillContextScoping:
    """Namespace isolation and parent read-through."""

    def test_scope_write_isolation(self):
        ctx = SkillContext()
        ctx.set("shared", "root")
        child = ctx.scope("branch_0")

        child.set("local", "child_val")
        # Child can read its own write
        assert child.get("local") == "child_val"
        # Parent sees it under the full namespace
        assert ctx.get("branch_0.local") == "child_val"
        # Parent does NOT see it under the bare key
        assert ctx.get("local") is None

    def test_scope_reads_parent(self):
        ctx = SkillContext()
        ctx.set("shared", "root_val")
        child = ctx.scope("branch_0")
        # Child can read parent's keys
        assert child.get("shared") == "root_val"

    def test_scope_does_not_shadow_parent(self):
        ctx = SkillContext()
        ctx.set("x", "root")
        child = ctx.scope("ns")
        child.set("x", "child")
        # Child's write goes to ns.x, not x
        assert ctx.get("x") == "root"
        assert ctx.get("ns.x") == "child"
        # Child reads ns.x first (its own write)
        assert child.get("x") == "child"

    def test_nested_scopes(self):
        ctx = SkillContext()
        a = ctx.scope("a")
        b = a.scope("b")
        b.set("val", 42)
        # Full path in root
        assert ctx.get("a.b.val") == 42
        # Parent scope "a" sees it too
        assert a.get("b.val") == 42
        # The nested child reads its own write
        assert b.get("val") == 42

    def test_scope_namespace_property(self):
        ctx = SkillContext()
        child = ctx.scope("ns")
        assert child.namespace == "ns"
        assert ctx.namespace == ""

    def test_scope_parent_property(self):
        ctx = SkillContext()
        child = ctx.scope("ns")
        assert child.parent is ctx
        assert ctx.parent is None

    def test_sibling_scopes_isolated(self):
        ctx = SkillContext()
        a = ctx.scope("a")
        b = ctx.scope("b")
        a.set("x", 1)
        b.set("x", 2)
        assert a.get("x") == 1
        assert b.get("x") == 2
        assert ctx.get("a.x") == 1
        assert ctx.get("b.x") == 2


# ---------------------------------------------------------------------------
# Snapshot and merge
# ---------------------------------------------------------------------------

class TestSnapshotAndMerge:
    def test_snapshot_returns_copy(self):
        ctx = SkillContext({"a": 1})
        snap = ctx.snapshot()
        snap["b"] = 2
        assert ctx.get("b") is None  # original not affected

    def test_merge(self):
        ctx1 = SkillContext({"a": 1})
        ctx2 = SkillContext({"b": 2, "c": 3})
        ctx1.merge(ctx2)
        assert ctx1.get("a") == 1
        assert ctx1.get("b") == 2
        assert ctx1.get("c") == 3


# ---------------------------------------------------------------------------
# Bridge to plain dict
# ---------------------------------------------------------------------------

class TestDictBridge:
    def test_from_dict_shares_reference(self):
        d = {"x": 1}
        ctx = SkillContext.from_dict(d)
        ctx.set("y", 2)
        assert d["y"] == 2  # same dict

    def test_to_dict_returns_same_reference(self):
        ctx = SkillContext({"a": 1})
        d = ctx.to_dict()
        d["b"] = 2
        assert ctx.get("b") == 2  # same dict


# ---------------------------------------------------------------------------
# Skill context injection
# ---------------------------------------------------------------------------

class TestSkillContextInjection:
    """@skill-decorated functions with SkillContext parameters."""

    def test_skill_with_context_param(self):
        @skill(name="ctx_writer")
        def ctx_writer(text: str, ctx: SkillContext) -> str:
            ctx.set("last_text", text)
            return text.upper()

        s = ctx_writer.__skill__
        ctx = SkillContext()
        result = s.invoke("hello", context=ctx)
        assert result.success
        assert result.value == "HELLO"
        assert ctx.get("last_text") == "hello"

    def test_skill_without_context_param(self):
        """Skills that don't declare SkillContext should work fine."""
        @skill(name="no_ctx")
        def no_ctx(text: str) -> str:
            return text.lower()

        s = no_ctx.__skill__
        ctx = SkillContext()
        result = s.invoke("HELLO", context=ctx)
        assert result.success
        assert result.value == "hello"

    def test_skill_invoke_no_context_kwarg(self):
        """Calling invoke without context= should work even if the function wants one."""
        @skill(name="wants_ctx")
        def wants_ctx(text: str, ctx: SkillContext = None) -> str:
            if ctx is not None:
                ctx.set("ran", True)
            return text

        s = wants_ctx.__skill__
        result = s.invoke("hello")
        assert result.success
        assert result.value == "hello"

    def test_skill_context_schema_inference_skips_ctx(self):
        """SkillContext params should not appear in the input schema."""
        @skill(name="with_ctx")
        def with_ctx(text: str, ctx: SkillContext) -> str:
            return text

        desc = with_ctx.__skill__.descriptor
        # input_schema should be inferred from `text: str`, not ctx
        assert desc.input_schema == {"type": "string"}

    @pytest.mark.asyncio
    async def test_async_skill_with_context(self):
        @skill(name="async_ctx_writer")
        async def async_ctx_writer(text: str, ctx: SkillContext) -> str:
            ctx.set("async_text", text)
            return text.upper()

        s = async_ctx_writer.__skill__
        ctx = SkillContext()
        result = await s.ainvoke("hello", context=ctx)
        assert result.success
        assert result.value == "HELLO"
        assert ctx.get("async_text") == "hello"

    def test_context_read_from_previous_skill(self):
        """Two skills in sequence: first writes, second reads."""
        @skill(name="writer")
        def writer(text: str, ctx: SkillContext) -> str:
            ctx.set("entities", ["date", "email"])
            return text

        @skill(name="reader")
        def reader(text: str, ctx: SkillContext) -> list:
            return ctx.get("entities", [])

        ctx = SkillContext()
        w = writer.__skill__
        r = reader.__skill__

        w.invoke("some text", context=ctx)
        result = r.invoke("some text", context=ctx)
        assert result.success
        assert result.value == ["date", "email"]


# ---------------------------------------------------------------------------
# Chain integration with context
# ---------------------------------------------------------------------------

class TestChainContextIntegration:
    """SkillContext flows through Chain steps."""

    def test_skills_share_context_in_chain(self):
        @skill(name="extract")
        def extract(text: str, ctx: SkillContext) -> str:
            ctx.set("extracted", text.split(","))
            return text

        @skill(name="count")
        def count(text: str, ctx: SkillContext) -> int:
            items = ctx.get("extracted", [])
            return len(items)

        chain = Chain([extract, count])
        result = chain.run("a,b,c")
        assert result == 3

    def test_chain_with_explicit_context(self):
        @skill(name="tag")
        def tag(text: str, ctx: SkillContext) -> str:
            ctx.set("tagged", True)
            return text

        ctx_dict = {}
        chain = Chain([tag])
        chain.run("hello", context=ctx_dict)
        # The SkillContext writes to the underlying dict
        assert ctx_dict.get("tagged") is True

    @pytest.mark.asyncio
    async def test_async_skills_share_context_in_chain(self):
        @skill(name="async_extract")
        async def async_extract(text: str, ctx: SkillContext) -> str:
            ctx.set("words", text.split())
            return text

        @skill(name="async_count")
        async def async_count(text: str, ctx: SkillContext) -> int:
            return len(ctx.get("words", []))

        chain = Chain([async_extract, async_count])
        result = await chain.arun("hello world foo")
        assert result == 3


# ---------------------------------------------------------------------------
# Branch integration with context
# ---------------------------------------------------------------------------

class TestBranchContextIntegration:
    def test_branch_paths_share_context(self):
        @skill(name="upper_tag")
        def upper_tag(text: str, ctx: SkillContext) -> str:
            ctx.set("path", "upper")
            return text.upper()

        @skill(name="lower_tag")
        def lower_tag(text: str, ctx: SkillContext) -> str:
            ctx.set("path", "lower")
            return text.lower()

        ctx_dict = {}
        chain = Chain([
            branch(
                on_match=lambda v: v.startswith("H"),
                true_path=[upper_tag],
                false_path=[lower_tag],
            )
        ])

        chain.run("Hello", context=ctx_dict)
        assert ctx_dict.get("path") == "upper"

        ctx_dict2 = {}
        chain.run("world", context=ctx_dict2)
        assert ctx_dict2.get("path") == "lower"


# ---------------------------------------------------------------------------
# Parallel isolation with context
# ---------------------------------------------------------------------------

class TestParallelContextIsolation:
    """Each parallel branch should get a scoped context."""

    def test_parallel_branches_write_to_scoped_namespaces(self):
        @skill(name="branch_a")
        def branch_a(text: str, ctx: SkillContext) -> str:
            ctx.set("result", "from_a")
            return text + "_a"

        @skill(name="branch_b")
        def branch_b(text: str, ctx: SkillContext) -> str:
            ctx.set("result", "from_b")
            return text + "_b"

        ctx_dict = {}
        chain = Chain([
            parallel(steps=[branch_a, branch_b], merge="dict"),
        ])
        result = chain.run("x", context=ctx_dict)
        assert result["branch_a"] == "x_a"
        assert result["branch_b"] == "x_b"

        # Each branch wrote to its own namespace
        assert ctx_dict.get("parallel_0.result") == "from_a"
        assert ctx_dict.get("parallel_1.result") == "from_b"
        # Bare "result" should NOT be set (no collision)
        assert ctx_dict.get("result") is None

    @pytest.mark.asyncio
    async def test_async_parallel_isolation(self):
        @skill(name="async_a")
        async def async_a(text: str, ctx: SkillContext) -> str:
            ctx.set("val", "a")
            return "A"

        @skill(name="async_b")
        async def async_b(text: str, ctx: SkillContext) -> str:
            ctx.set("val", "b")
            return "B"

        ctx_dict = {}
        chain = Chain([
            parallel(steps=[async_a, async_b], merge="list"),
        ])
        result = await chain.arun("x", context=ctx_dict)
        assert result == ["A", "B"]

        assert ctx_dict.get("parallel_0.val") == "a"
        assert ctx_dict.get("parallel_1.val") == "b"

    def test_parallel_branches_can_read_parent_context(self):
        @skill(name="reader")
        def reader(text: str, ctx: SkillContext) -> str:
            return ctx.get("shared", "missing")

        ctx_dict = {"shared": "root_value"}
        chain = Chain([
            parallel(steps=[reader, reader], merge="list"),
        ])
        result = chain.run("x", context=ctx_dict)
        assert result == ["root_value", "root_value"]


# ---------------------------------------------------------------------------
# End-to-end integration
# ---------------------------------------------------------------------------

class TestEndToEnd:
    """Full pipelines combining context, skills, chains, branches, parallel."""

    def test_extract_then_format_pipeline(self):
        """The canonical Phase 6 example from FEEDBACK.md."""

        @skill(name="extract_entities")
        def extract_entities(text: str, ctx: SkillContext) -> dict:
            # Simplified entity extraction
            entities = {
                "dates": ["2024-01-01"],
                "emails": ["test@example.com"],
            }
            ctx.set("last_entities", entities)
            return entities

        @skill(name="format_entities")
        def format_entities(entities: dict, ctx: SkillContext) -> str:
            stored = ctx.get("last_entities", {})
            parts = []
            for k, v in stored.items():
                parts.append(f"{k}: {', '.join(v)}")
            return "; ".join(parts)

        chain = Chain([extract_entities, format_entities])
        result = chain.run("Meeting on 2024-01-01, email test@example.com")
        assert "dates: 2024-01-01" in result
        assert "emails: test@example.com" in result

    def test_branch_with_context_accumulation(self):
        """Branch writes to context, downstream reads it."""

        @skill(name="classify")
        def classify(text: str, ctx: SkillContext) -> str:
            if "@" in text:
                ctx.set("type", "email")
                return "email"
            ctx.set("type", "text")
            return "text"

        @skill(name="summarize")
        def summarize(classification: str, ctx: SkillContext) -> str:
            t = ctx.get("type", "unknown")
            return f"Input is {t}: {classification}"

        chain = Chain([classify, summarize])
        assert chain.run("user@test.com") == "Input is email: email"
        assert chain.run("hello world") == "Input is text: text"

    @pytest.mark.asyncio
    async def test_async_parallel_context_pipeline(self):
        """Parallel fan-out with context, then merge and read context."""

        @skill(name="extract_dates")
        async def extract_dates(text: str, ctx: SkillContext) -> list:
            dates = ["2024-01-01"]
            ctx.set("dates", dates)
            return dates

        @skill(name="extract_emails")
        async def extract_emails(text: str, ctx: SkillContext) -> list:
            emails = ["a@b.com"]
            ctx.set("emails", emails)
            return emails

        chain = Chain([
            parallel(
                steps=[extract_dates, extract_emails],
                merge="dict",
            ),
        ])
        ctx_dict = {}
        result = await chain.arun("text", context=ctx_dict)
        assert result["extract_dates"] == ["2024-01-01"]
        assert result["extract_emails"] == ["a@b.com"]

        # Context has scoped writes
        assert ctx_dict.get("parallel_0.dates") == ["2024-01-01"]
        assert ctx_dict.get("parallel_1.emails") == ["a@b.com"]
