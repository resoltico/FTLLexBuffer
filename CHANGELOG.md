# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-01-28

### Added
- `FluentBundle.get_all_message_variables()` - Batch introspection API for extracting variables from all messages at once. Useful for CI/CD validation pipelines.
- Property-based testing examples in `examples/property_based_testing.py` - 7 examples demonstrating Hypothesis usage with FTLLexBuffer.
- Test suite for batch introspection (`tests/test_bundle_batch_introspection.py`) - 23 tests including property-based tests.

## [0.1.0] - 2025-11-28

Initial release.

[0.1.1]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.1.1
[0.1.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.1.0
