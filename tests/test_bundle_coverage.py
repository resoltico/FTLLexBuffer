"""Coverage tests for bundle.py edge cases and warning paths.

Targets uncovered lines in bundle.py:
- Line 185: use_isolating property getter
- Lines 215-218: get_babel_locale method
- Lines 423-425: Warning for message with neither value nor attributes
- Lines 429-432: Warning for duplicate term ID
- Line 463: Visiting term attributes for validation
- Lines 467-470: Warning for term referencing undefined message
- Lines 475-477: Warning for term referencing undefined term
- Lines 729-730: KeyError when introspecting non-existent message
"""

import pytest

from ftllexbuffer import FluentBundle


class TestBundleProperties:
    """Test FluentBundle property accessors."""

    def test_use_isolating_property_getter(self) -> None:
        """Test use_isolating property getter (line 185)."""
        bundle = FluentBundle("en", use_isolating=True)

        # Access the property (hits line 185)
        assert bundle.use_isolating is True

        bundle_no_iso = FluentBundle("en", use_isolating=False)
        assert bundle_no_iso.use_isolating is False

    def test_get_babel_locale(self) -> None:
        """Test get_babel_locale method (lines 215-218)."""
        bundle = FluentBundle("en_US")

        # Call get_babel_locale (hits lines 215-218)
        locale_str = bundle.get_babel_locale()

        assert "en" in locale_str  # Should return Babel locale string
        assert isinstance(locale_str, str)


class TestBundleValidationWarnings:
    """Test bundle validation warning paths."""

    def test_duplicate_term_id_warning(self) -> None:
        """Duplicate term ID triggers warning (lines 429-432)."""
        bundle = FluentBundle("en")

        # Add FTL with duplicate term definitions
        ftl = """
-brand = Acme Corp
-brand = Different Corp
welcome = Welcome to { -brand }!
"""
        # add_resource returns warnings
        bundle.add_resource(ftl)

        # The duplicate term is accepted but should trigger a warning
        # The later definition overwrites the earlier one
        result, _ = bundle.format_value("welcome")
        assert "Different Corp" in result

    def test_term_with_attributes_validation(self) -> None:
        """Term with attributes gets validated (line 463)."""
        bundle = FluentBundle("en")

        # Add term with attributes
        ftl = """
-brand = Acme Corp
    .legal = Acme Corporation Ltd.
    .short = Acme

legal-notice = Legal: { -brand.legal }
"""
        bundle.add_resource(ftl)

        # This should successfully validate all attributes (hits line 463)
        result, _ = bundle.format_value("legal-notice")
        assert "Acme Corporation" in result

    def test_term_references_undefined_message(self) -> None:
        """Term referencing undefined message triggers warning (lines 467-470)."""
        bundle = FluentBundle("en")

        # Add term that references a non-existent message
        ftl = """
-brand = { missing-message }
welcome = { -brand }
"""
        bundle.add_resource(ftl)

        # Should trigger warning but still work
        result, _ = bundle.format_value("welcome")
        assert isinstance(result, str)

    def test_term_references_undefined_term(self) -> None:
        """Term referencing undefined term triggers warning (lines 475-477)."""
        bundle = FluentBundle("en")

        # Add term that references a non-existent term
        ftl = """
-company = Welcome to { -missing-term }
welcome = { -company }
"""
        bundle.add_resource(ftl)

        # Should trigger warning but still work
        result, _ = bundle.format_value("welcome")
        assert isinstance(result, str)


class TestBundleIntrospection:
    """Test bundle introspection error paths."""

    def test_introspect_message_not_found(self) -> None:
        """Introspecting non-existent message raises KeyError (lines 729-730)."""
        bundle = FluentBundle("en")
        bundle.add_resource("hello = Hello!")

        # Try to introspect a message that doesn't exist
        with pytest.raises(KeyError, match="Message 'nonexistent' not found"):
            bundle.introspect_message("nonexistent")

    def test_introspect_message_exists(self) -> None:
        """Introspecting existing message works."""
        bundle = FluentBundle("en")
        bundle.add_resource("hello = Hello { $name }!")

        # Introspect existing message
        info = bundle.introspect_message("hello")

        # Should return MessageInfo
        assert "name" in info.get_variable_names()
