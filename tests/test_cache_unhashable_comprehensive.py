"""Comprehensive tests for runtime.cache unhashable argument handling.

Tests FormatCache behavior with unhashable arguments (lists, dicts, custom objects).
Focuses on achieving 100% coverage for unhashable_skips tracking.

"""

from typing import NoReturn

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ftllexbuffer.runtime.cache import FormatCache


class TestCacheBasicOperations:
    """Tests for basic cache operations to achieve full coverage."""

    def test_init_with_zero_maxsize_raises(self) -> None:
        """Verify __init__ raises ValueError for maxsize <= 0 (lines 65-66)."""
        with pytest.raises(ValueError, match="maxsize must be positive"):
            FormatCache(maxsize=0)

    def test_init_with_negative_maxsize_raises(self) -> None:
        """Verify __init__ raises ValueError for negative maxsize."""
        with pytest.raises(ValueError, match="maxsize must be positive"):
            FormatCache(maxsize=-1)

    def test_get_cache_hit_path(self) -> None:
        """Verify cache hit path in get() (lines 106-108)."""
        cache = FormatCache(maxsize=100)

        # Put a value in cache
        args = {"key": "value"}
        result = ("formatted_text", ())
        cache.put("msg-id", args, None, "en-US", result)

        # Get should hit cache
        cached = cache.get("msg-id", args, None, "en-US")

        assert cached == result
        assert cache.hits == 1
        assert cache.misses == 0

    def test_put_updates_existing_key(self) -> None:
        """Verify put() updates existing key and moves to end (line 143)."""
        cache = FormatCache(maxsize=100)

        args = {"key": "value"}
        result1 = ("text1", ())
        result2 = ("text2", ())

        # Put initial value
        cache.put("msg-id", args, None, "en-US", result1)
        assert len(cache) == 1

        # Put updated value for same key
        cache.put("msg-id", args, None, "en-US", result2)
        assert len(cache) == 1  # Still one entry

        # Get should return updated value
        cached = cache.get("msg-id", args, None, "en-US")
        assert cached == result2

    def test_put_evicts_lru_when_full(self) -> None:
        """Verify put() evicts LRU entry when cache is full (line 146)."""
        cache = FormatCache(maxsize=2)

        # Fill cache to capacity
        cache.put("msg1", {"k": "v1"}, None, "en-US", ("text1", ()))
        cache.put("msg2", {"k": "v2"}, None, "en-US", ("text2", ()))
        assert len(cache) == 2

        # Add third entry - should evict first (LRU)
        cache.put("msg3", {"k": "v3"}, None, "en-US", ("text3", ()))
        assert len(cache) == 2

        # First entry should be gone
        result1 = cache.get("msg1", {"k": "v1"}, None, "en-US")
        assert result1 is None

        # Second and third should be present
        result2 = cache.get("msg2", {"k": "v2"}, None, "en-US")
        result3 = cache.get("msg3", {"k": "v3"}, None, "en-US")
        assert result2 is not None
        assert result3 is not None

    def test_make_key_with_none_args(self) -> None:
        """Verify _make_key handles None args correctly (line 205)."""
        key = FormatCache._make_key("msg-id", None, None, "en-US")

        assert key is not None
        assert key == ("msg-id", (), None, "en-US")

    def test_maxsize_property(self) -> None:
        """Verify maxsize property returns correct value (line 231)."""
        cache = FormatCache(maxsize=500)

        assert cache.maxsize == 500


class TestCacheUnhashableArguments:
    """Tests for FormatCache handling of unhashable arguments."""

    def test_get_with_unhashable_list_value(self) -> None:
        """Verify get() handles unhashable list values gracefully (lines 98-101)."""
        cache = FormatCache(maxsize=100)

        # Args contain a list (unhashable)
        args = {"key": [1, 2, 3]}

        # Should return None and increment unhashable_skips
        result = cache.get("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert result is None
        assert cache.unhashable_skips == 1
        assert cache.misses == 1
        assert cache.hits == 0

    def test_get_with_unhashable_dict_value(self) -> None:
        """Verify get() handles unhashable dict values (lines 98-101)."""
        cache = FormatCache(maxsize=100)

        # Args contain a nested dict (unhashable)
        args = {"key": {"nested": "value"}}

        result = cache.get("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert result is None
        assert cache.unhashable_skips == 1
        assert cache.misses == 1

    def test_get_with_unhashable_set_value(self) -> None:
        """Verify get() handles unhashable set values (lines 98-101)."""
        cache = FormatCache(maxsize=100)

        # Args contain a set (unhashable when nested in tuple)
        args = {"key": {1, 2, 3}}

        result = cache.get("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert result is None
        assert cache.unhashable_skips == 1

    def test_put_with_unhashable_list_value(self) -> None:
        """Verify put() handles unhashable list values gracefully (lines 135-137)."""
        cache = FormatCache(maxsize=100)

        # Args contain a list (unhashable)
        args = {"items": [1, 2, 3]}
        result = ("formatted", ())

        # Should skip silently and increment unhashable_skips
        cache.put("msg-id", args, None, "en-US", result)  # type: ignore[arg-type]

        assert len(cache) == 0  # Nothing cached
        assert cache.unhashable_skips == 1

    def test_put_with_unhashable_dict_value(self) -> None:
        """Verify put() handles unhashable dict values (lines 135-137)."""
        cache = FormatCache(maxsize=100)

        args = {"config": {"option": "value"}}
        result = ("formatted", ())

        cache.put("msg-id", args, None, "en-US", result)  # type: ignore[arg-type]

        assert len(cache) == 0
        assert cache.unhashable_skips == 1

    def test_make_key_with_unhashable_args_returns_none(self) -> None:
        """Verify _make_key returns None for unhashable args (lines 211-213)."""
        # Call _make_key directly with unhashable args
        args = {"list_value": [1, 2, 3]}

        key = FormatCache._make_key("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert key is None

    def test_make_key_with_nested_unhashable_returns_none(self) -> None:
        """Verify _make_key returns None for nested unhashable values (lines 211-213)."""
        # Multiple unhashable values
        args: dict[str, object] = {
            "list": [1, 2],
            "dict": {"nested": "value"},
        }

        key = FormatCache._make_key("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert key is None

    def test_unhashable_skips_property(self) -> None:
        """Verify unhashable_skips property returns correct count (lines 257-258)."""
        cache = FormatCache(maxsize=100)

        # Initial value
        assert cache.unhashable_skips == 0

        # Trigger unhashable skips with get
        cache.get("msg1", {"list": [1]}, None, "en-US")  # type: ignore[dict-item]
        assert cache.unhashable_skips == 1

        # Trigger unhashable skips with put
        cache.put("msg2", {"dict": {}}, None, "en-US", ("result", ()))  # type: ignore[dict-item]
        assert cache.unhashable_skips == 2

        # Multiple operations
        cache.get("msg3", {"set": {1, 2}}, None, "en-US")  # type: ignore[dict-item]
        cache.put("msg4", {"list2": [3]}, None, "en-US", ("result", ()))  # type: ignore[dict-item]
        assert cache.unhashable_skips == 4

    def test_unhashable_skips_resets_on_clear(self) -> None:
        """Verify unhashable_skips resets to 0 after clear()."""
        cache = FormatCache(maxsize=100)

        # Generate some unhashable skips
        cache.get("msg", {"list": [1]}, None, "en-US")  # type: ignore[dict-item]
        cache.put("msg2", {"list": [2]}, None, "en-US", ("result", ()))  # type: ignore[dict-item]
        assert cache.unhashable_skips == 2

        # Clear should reset
        cache.clear()
        assert cache.unhashable_skips == 0

    def test_get_stats_includes_unhashable_skips(self) -> None:
        """Verify get_stats() includes unhashable_skips count."""
        cache = FormatCache(maxsize=100)

        # Generate some unhashable operations
        cache.get("msg", {"list": [1]}, None, "en-US")  # type: ignore[dict-item]
        cache.put("msg2", {"dict": {}}, None, "en-US", ("result", ()))  # type: ignore[dict-item]

        stats = cache.get_stats()

        assert "unhashable_skips" in stats
        assert stats["unhashable_skips"] == 2
        assert stats["misses"] == 1  # get increments misses

    @given(
        st.lists(st.integers(), min_size=1, max_size=10),
    )
    def test_get_with_various_unhashable_lists(self, list_value: list[int]) -> None:
        """Property: get() always returns None for list-valued args."""
        cache = FormatCache(maxsize=100)
        args = {"list_arg": list_value}

        result = cache.get("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert result is None
        assert cache.unhashable_skips >= 1

    @given(
        st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), min_size=1, max_size=5),
    )
    def test_put_with_various_unhashable_dicts(self, dict_value: dict[str, int]) -> None:
        """Property: put() always skips for dict-valued args."""
        cache = FormatCache(maxsize=100)
        args = {"dict_arg": dict_value}
        result = ("formatted", ())

        cache.put("msg-id", args, None, "en-US", result)  # type: ignore[arg-type]

        assert len(cache) == 0  # Nothing cached
        assert cache.unhashable_skips >= 1

    def test_mixed_hashable_and_unhashable_args(self) -> None:
        """Verify cache handles mixed hashable/unhashable args correctly."""
        cache = FormatCache(maxsize=100)

        # Some hashable, some unhashable
        args: dict[str, object] = {
            "str_arg": "value",
            "int_arg": 42,
            "list_arg": [1, 2, 3],  # Unhashable!
        }

        # Should skip due to one unhashable value
        result = cache.get("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert result is None
        assert cache.unhashable_skips == 1

    def test_unhashable_custom_object(self) -> None:
        """Verify cache handles custom unhashable objects."""
        cache = FormatCache(maxsize=100)

        class UnhashableClass:
            """Custom class that's not hashable."""

            def __init__(self) -> None:
                self.data = [1, 2, 3]

            def __hash__(self) -> NoReturn:  # pylint: disable=invalid-hash-returned
                # Make it explicitly unhashable by raising TypeError
                msg = "unhashable type"
                raise TypeError(msg)

        args = {"custom": UnhashableClass()}

        result = cache.get("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert result is None
        assert cache.unhashable_skips == 1

    def test_sequential_unhashable_operations(self) -> None:
        """Verify unhashable_skips accumulates correctly across operations."""
        cache = FormatCache(maxsize=100)

        # Sequence of unhashable operations
        operations = [
            ("get", "msg1", {"list": [1]}),
            ("put", "msg2", {"dict": {}}),
            ("get", "msg3", {"set": {1}}),
            ("put", "msg4", {"list2": [2]}),
            ("get", "msg5", {"dict2": {"k": "v"}}),
        ]

        for i, (op, msg_id, args) in enumerate(operations, 1):
            if op == "get":
                cache.get(msg_id, args, None, "en-US")  # type: ignore[arg-type]
            else:  # put
                cache.put(msg_id, args, None, "en-US", ("result", ()))  # type: ignore[arg-type]

            assert cache.unhashable_skips == i

    def test_hashable_args_do_not_increment_unhashable_skips(self) -> None:
        """Verify hashable args don't increment unhashable_skips counter."""
        cache = FormatCache(maxsize=100)

        # Fully hashable args
        args: dict[str, object] = {"str": "value", "int": 42, "float": 3.14}

        cache.get("msg1", args, None, "en-US")  # type: ignore[arg-type]
        cache.put("msg2", args, None, "en-US", ("result", ()))  # type: ignore[arg-type]

        # Should not increment unhashable_skips
        assert cache.unhashable_skips == 0
        assert cache.misses == 1  # get miss

    def test_unhashable_empty_list(self) -> None:
        """Verify empty lists are also handled as unhashable."""
        cache = FormatCache(maxsize=100)

        args: dict[str, list[object]] = {"empty_list": []}

        result = cache.get("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert result is None
        assert cache.unhashable_skips == 1

    def test_unhashable_empty_dict(self) -> None:
        """Verify empty dicts are also handled as unhashable."""
        cache = FormatCache(maxsize=100)

        args: dict[str, dict[object, object]] = {"empty_dict": {}}

        result = cache.get("msg-id", args, None, "en-US")  # type: ignore[arg-type]

        assert result is None
        assert cache.unhashable_skips == 1
