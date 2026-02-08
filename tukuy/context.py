"""Typed, scoped context for inter-skill communication.

Phase 6 of the Tukuy roadmap: skills can share state between invocations
via a ``SkillContext`` that flows through chains, branches, and parallel
fan-outs.

Usage::

    from tukuy import skill, SkillContext

    @skill(name="extract_entities")
    def extract_entities(text: str, ctx: SkillContext) -> dict:
        entities = do_extraction(text)
        ctx.set("last_entities", entities)
        return entities

    @skill(name="format_entities")
    def format_entities(ctx: SkillContext) -> str:
        entities = ctx.get("last_entities")
        return format_them(entities)
"""

from typing import Any, Dict, Iterator, Optional, TypeVar

T = TypeVar("T")

_SENTINEL = object()


class SkillContext:
    """Typed, scoped context bag for inter-skill communication.

    Parameters
    ----------
    data : dict, optional
        Initial data to populate the context with.  If *None*, an empty
        dict is used.  This is the **root** data store — child scopes
        created via :meth:`scope` share (read) from this store but write
        into a namespaced prefix.
    parent : SkillContext, optional
        Parent context.  Scoped children set this automatically.
    namespace : str, optional
        Dot-separated namespace prefix for scoped writes.

    Examples
    --------
    >>> ctx = SkillContext()
    >>> ctx.set("user", "alice")
    >>> ctx.get("user")
    'alice'

    >>> child = ctx.scope("branch_0")
    >>> child.set("temp", 42)
    >>> child.get("temp")
    42
    >>> ctx.get("branch_0.temp")
    42
    >>> ctx.get("temp") is None
    True
    """

    def __init__(
        self,
        data: Optional[Dict[str, Any]] = None,
        *,
        parent: Optional["SkillContext"] = None,
        namespace: str = "",
    ) -> None:
        self._data: Dict[str, Any] = data if data is not None else {}
        self._parent = parent
        self._namespace = namespace

    # ------------------------------------------------------------------
    # Core get / set
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Read a value from context.

        Resolution order:
        1. Namespaced key (``{namespace}.{key}``) if a namespace is set.
        2. Bare key in the local data store.
        3. Parent context (if any).
        4. *default*.
        """
        # Namespaced lookup first
        if self._namespace:
            ns_key = f"{self._namespace}.{key}"
            if ns_key in self._data:
                return self._data[ns_key]

        # Bare key in own store
        if key in self._data:
            return self._data[key]

        # Delegate to parent
        if self._parent is not None:
            return self._parent.get(key, default)

        return default

    def set(self, key: str, value: Any) -> None:
        """Write a value into context.

        If a namespace is active the key is stored as ``{namespace}.{key}``
        in the **root** data dict so that the parent and sibling scopes
        can see it via the full qualified key while the child scope sees
        it via the short key.
        """
        if self._namespace:
            ns_key = f"{self._namespace}.{key}"
            self._data[ns_key] = value
        else:
            self._data[key] = value

    def has(self, key: str) -> bool:
        """Check whether *key* is present (respects namespace & parent)."""
        return self.get(key, _SENTINEL) is not _SENTINEL

    def delete(self, key: str) -> None:
        """Remove a key from context.  No-op if missing."""
        if self._namespace:
            ns_key = f"{self._namespace}.{key}"
            self._data.pop(ns_key, None)
        else:
            self._data.pop(key, None)

    def update(self, mapping: Dict[str, Any]) -> None:
        """Bulk-set multiple keys."""
        for k, v in mapping.items():
            self.set(k, v)

    # ------------------------------------------------------------------
    # Scoping
    # ------------------------------------------------------------------

    def scope(self, namespace: str) -> "SkillContext":
        """Create a child context scoped to *namespace*.

        The child shares the same underlying data dict as the root so
        that values written inside the scope are visible to the parent
        (under the fully-qualified ``{namespace}.{key}``).  Reads fall
        through to the parent when the namespaced key is not found.
        """
        # Resolve nested namespaces: if this context already has a
        # namespace, concatenate them.
        full_ns = f"{self._namespace}.{namespace}" if self._namespace else namespace
        return SkillContext(data=self._data, parent=self, namespace=full_ns)

    # ------------------------------------------------------------------
    # Snapshot / merge
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow copy of the raw data dict."""
        return dict(self._data)

    def merge(self, other: "SkillContext") -> None:
        """Merge another context's data into this one."""
        self._data.update(other._data)

    # ------------------------------------------------------------------
    # Bridge to plain dict (TransformContext)
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillContext":
        """Create a SkillContext backed by an existing dict.

        The dict is **not** copied — mutations through the context are
        visible in the original dict and vice-versa.
        """
        return cls(data=data)

    def to_dict(self) -> Dict[str, Any]:
        """Return the underlying data dict (same reference, not a copy)."""
        return self._data

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def parent(self) -> Optional["SkillContext"]:
        return self._parent

    def keys(self) -> Iterator[str]:
        """Iterate over all keys in the raw data store."""
        return iter(self._data)

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        ns = f", namespace={self._namespace!r}" if self._namespace else ""
        return f"SkillContext(keys={list(self._data.keys())!r}{ns})"


__all__ = ["SkillContext"]
