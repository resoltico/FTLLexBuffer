"""Pytest configuration for FTLLexBuffer test suite.

This module configures Hypothesis profiles for different execution contexts:
- default: Local development (balanced speed/thoroughness)
- ci: Continuous integration (deterministic, reproducible)

The appropriate profile is auto-detected based on execution context.
"""

from hypothesis import Phase, settings

# =============================================================================
# HYPOTHESIS PROFILES
# =============================================================================

# Default profile: balanced for local development
settings.register_profile(
    "default",
    max_examples=100,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink],
    derandomize=False,
)

# CI profile: deterministic for reproducibility
settings.register_profile(
    "ci",
    max_examples=200,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink],
    derandomize=True,
    print_blob=True,
)


# =============================================================================
# AUTO-DETECT EXECUTION CONTEXT
# =============================================================================


def _detect_profile() -> str:
    """Detect appropriate Hypothesis profile based on execution context."""
    import os

    # Running in CI (GitHub Actions sets CI=true)
    if os.environ.get("CI") == "true":
        return "ci"

    # Local development
    return "default"


# Load appropriate profile automatically
settings.load_profile(_detect_profile())
