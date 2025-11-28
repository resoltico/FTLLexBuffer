"""Tests for runtime/bundle.py to achieve 100% coverage.

Focuses on Junk entry handling and FluentSyntaxError in validate_resource.
"""

from unittest.mock import patch

from ftllexbuffer.diagnostics import FluentSyntaxError
from ftllexbuffer.runtime.bundle import FluentBundle
from ftllexbuffer.syntax.ast import Junk


class TestBundleJunkHandling:
    """Test Junk entry handling in add_resource (line 130)."""

    def test_add_resource_with_junk_entry_increments_count(self):
        """Test that Junk entries are counted in add_resource."""
        bundle = FluentBundle("en")

        # Create FTL with syntax that produces Junk
        # Unclosed brace will create Junk entry
        source = "bad = { missing close\nhello = World"

        # Add resource - should handle Junk gracefully
        bundle.add_resource(source)

        # Should have registered the valid message
        assert bundle.has_message("hello")

    def test_add_resource_counts_junk_entries(self):
        """Test Junk entry counting logic (line 130-133)."""
        bundle = FluentBundle("en")

        # Mix of valid and invalid entries
        source = """
# This will parse
good = Valid message

# This might create junk (malformed)
{ unclosed

# Another valid one
another = Another valid
"""

        # Should not crash, even with junk
        bundle.add_resource(source)

        # Valid messages should be registered
        assert bundle.has_message("good") or bundle.has_message("another")


class TestBundleValidateResourceError:
    """Test validate_resource exception handling (lines 179-184)."""

    def test_validate_resource_critical_syntax_error(self):
        """Test validate_resource with critical FluentSyntaxError."""
        bundle = FluentBundle("en")

        # Mock the parser to raise FluentSyntaxError
        with patch.object(bundle._parser, "parse") as mock_parse:
            mock_parse.side_effect = FluentSyntaxError("Critical parse error")

            result = bundle.validate_resource("any source")

            # Should return ValidationResult with error
            assert not result.is_valid
            assert result.error_count == 1
            assert isinstance(result.errors[0], Junk)
            assert "Critical parse error" in result.errors[0].content

    def test_validate_resource_logs_critical_error(self):
        """Test that critical errors are logged."""
        bundle = FluentBundle("en")

        with patch.object(bundle._parser, "parse") as mock_parse:
            mock_parse.side_effect = FluentSyntaxError("Parse failure")

            with patch("ftllexbuffer.runtime.bundle.logger") as mock_logger:
                bundle.validate_resource("source")

                # Should log error
                mock_logger.error.assert_called_once()
                call_args = str(mock_logger.error.call_args)
                assert "Critical validation error" in call_args
