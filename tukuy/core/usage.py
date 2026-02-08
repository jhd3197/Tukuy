"""Usage tracking for Tukuy transformers.

Provides in-memory usage counters with optional JSON file persistence,
so that discovery functions can surface the most popular tools first.
"""

import json
import threading
from collections import Counter
from typing import Dict, List, Optional


class UsageTracker:
    """Thread-safe, in-memory usage counter with optional file persistence."""

    def __init__(self) -> None:
        self._counts: Counter = Counter()
        self._lock = threading.Lock()

    def record(self, tool_name: str) -> None:
        """Increment the usage counter for *tool_name*."""
        with self._lock:
            self._counts[tool_name] += 1

    def get_popular(self, limit: int = 5) -> List[str]:
        """Return the top *limit* tool names ordered by usage count."""
        with self._lock:
            return [name for name, _ in self._counts.most_common(limit)]

    def get_count(self, tool_name: str) -> int:
        """Return the current usage count for *tool_name*."""
        with self._lock:
            return self._counts[tool_name]

    def save(self, path: str) -> None:
        """Persist current counts to a JSON file at *path*."""
        with self._lock:
            data = dict(self._counts)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> None:
        """Load counts from a JSON file at *path*, merging into current state."""
        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, int] = json.load(f)
        with self._lock:
            self._counts.update(data)

    def reset(self) -> None:
        """Clear all usage counts."""
        with self._lock:
            self._counts.clear()


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_usage_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Return the global ``UsageTracker`` singleton (created on first call)."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker
