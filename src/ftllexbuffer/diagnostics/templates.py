"""Error message templates.

Centralized error message templates for testable, consistent error messages.
Python 3.13+. Zero external dependencies.
"""

from __future__ import annotations

from .codes import Diagnostic, DiagnosticCode


class ErrorTemplate:
    """Centralized error message templates.

    All error messages are created here. NO f-strings in exception constructors!
    This solves EM101/EM102 violations while providing:
        - Testable error messages
        - Consistent formatting
        - Easy i18n in the future
        - Documentation of all error cases
    """

    # Base documentation URL
    _DOCS_BASE = "https://projectfluent.org/fluent/guide"

    @staticmethod
    def message_not_found(message_id: str) -> Diagnostic:
        """Message reference not found in bundle.

        Args:
            message_id: The message identifier that was not found

        Returns:
            Diagnostic for MESSAGE_NOT_FOUND
        """
        msg = f"Message '{message_id}' not found"
        return Diagnostic(
            code=DiagnosticCode.MESSAGE_NOT_FOUND,
            message=msg,
            span=None,
            hint="Check that the message is defined in the loaded resources",
            help_url=f"{ErrorTemplate._DOCS_BASE}/messages.html",
        )

    @staticmethod
    def attribute_not_found(attribute: str, message_id: str) -> Diagnostic:
        """Message attribute not found.

        Args:
            attribute: The attribute name that was not found
            message_id: The message containing (or not) the attribute

        Returns:
            Diagnostic for ATTRIBUTE_NOT_FOUND
        """
        msg = f"Attribute '{attribute}' not found in message '{message_id}'"
        return Diagnostic(
            code=DiagnosticCode.ATTRIBUTE_NOT_FOUND,
            message=msg,
            span=None,
            hint=f"Check that message '{message_id}' has an attribute '.{attribute}'",
            help_url=f"{ErrorTemplate._DOCS_BASE}/attributes.html",
        )

    @staticmethod
    def term_not_found(term_id: str) -> Diagnostic:
        """Term reference not found.

        Args:
            term_id: The term identifier (without leading -)

        Returns:
            Diagnostic for TERM_NOT_FOUND
        """
        msg = f"Term '-{term_id}' not found"
        return Diagnostic(
            code=DiagnosticCode.TERM_NOT_FOUND,
            message=msg,
            span=None,
            hint="Terms must be defined before they are referenced",
            help_url=f"{ErrorTemplate._DOCS_BASE}/terms.html",
        )

    @staticmethod
    def term_attribute_not_found(attribute: str, term_id: str) -> Diagnostic:
        """Term attribute not found.

        Args:
            attribute: The attribute name that was not found
            term_id: The term identifier (without leading -)

        Returns:
            Diagnostic for TERM_ATTRIBUTE_NOT_FOUND
        """
        msg = f"Attribute '{attribute}' not found in term '-{term_id}'"
        return Diagnostic(
            code=DiagnosticCode.TERM_ATTRIBUTE_NOT_FOUND,
            message=msg,
            span=None,
            hint=f"Check that term '-{term_id}' has an attribute '.{attribute}'",
            help_url=f"{ErrorTemplate._DOCS_BASE}/terms.html",
        )

    @staticmethod
    def variable_not_provided(variable_name: str) -> Diagnostic:
        """Variable not provided in arguments.

        Args:
            variable_name: The variable name (without leading $)

        Returns:
            Diagnostic for VARIABLE_NOT_PROVIDED
        """
        msg = f"Variable '${variable_name}' not provided"
        return Diagnostic(
            code=DiagnosticCode.VARIABLE_NOT_PROVIDED,
            message=msg,
            span=None,
            hint=f"Pass '{variable_name}' in the arguments dictionary",
            help_url=f"{ErrorTemplate._DOCS_BASE}/variables.html",
        )

    @staticmethod
    def message_no_value(message_id: str) -> Diagnostic:
        """Message has no value (only attributes).

        Args:
            message_id: The message identifier

        Returns:
            Diagnostic for MESSAGE_NO_VALUE
        """
        msg = f"Message '{message_id}' has no value"
        return Diagnostic(
            code=DiagnosticCode.MESSAGE_NO_VALUE,
            message=msg,
            span=None,
            hint="Message has only attributes; specify which attribute to format",
            help_url=f"{ErrorTemplate._DOCS_BASE}/messages.html",
        )

    @staticmethod
    def cyclic_reference(resolution_path: list[str]) -> Diagnostic:
        """Circular reference detected.

        Args:
            resolution_path: The path of message references forming the cycle

        Returns:
            Diagnostic for CYCLIC_REFERENCE
        """
        # Build cycle visualization
        cycle_chain = " -> ".join(resolution_path)
        msg = f"Circular reference detected: {cycle_chain}"

        return Diagnostic(
            code=DiagnosticCode.CYCLIC_REFERENCE,
            message=msg,
            span=None,
            hint="Break the circular dependency by removing one of the references",
            help_url=f"{ErrorTemplate._DOCS_BASE}/references.html",
        )

    @staticmethod
    def no_variants() -> Diagnostic:
        """Select expression has no variants.

        Returns:
            Diagnostic for NO_VARIANTS
        """
        msg = "No variants in select expression"
        return Diagnostic(
            code=DiagnosticCode.NO_VARIANTS,
            message=msg,
            span=None,
            hint="Select expressions must have at least one variant",
            help_url=f"{ErrorTemplate._DOCS_BASE}/selectors.html",
        )

    @staticmethod
    def function_not_found(function_name: str) -> Diagnostic:
        """Function not found in registry.

        Args:
            function_name: The function name (e.g., "NUMBER", "DATETIME")

        Returns:
            Diagnostic for FUNCTION_NOT_FOUND
        """
        msg = f"Function '{function_name}' not found"
        return Diagnostic(
            code=DiagnosticCode.FUNCTION_NOT_FOUND,
            message=msg,
            span=None,
            hint="Built-in functions: NUMBER, DATETIME. Check spelling.",
            help_url=f"{ErrorTemplate._DOCS_BASE}/functions.html",
        )

    @staticmethod
    def function_failed(function_name: str, error_msg: str) -> Diagnostic:
        """Function execution failed.

        Args:
            function_name: The function that failed
            error_msg: The error message from the function

        Returns:
            Diagnostic for FUNCTION_FAILED
        """
        msg = f"Function '{function_name}' failed: {error_msg}"
        return Diagnostic(
            code=DiagnosticCode.FUNCTION_FAILED,
            message=msg,
            span=None,
            hint="Check the function arguments and their types",
            help_url=f"{ErrorTemplate._DOCS_BASE}/functions.html",
            function_name=function_name,
        )

    @staticmethod
    def type_mismatch(
        function_name: str,
        argument_name: str,
        expected_type: str,
        received_type: str,
        *,
        ftl_location: str | None = None,
    ) -> Diagnostic:
        """Type mismatch in function argument.

        Args:
            function_name: Function where type mismatch occurred
            argument_name: Argument name that has wrong type
            expected_type: Expected type (e.g., "Number", "String")
            received_type: Actual type received
            ftl_location: FTL file location (optional)

        Returns:
            Diagnostic for TYPE_MISMATCH
        """
        msg = f"Type mismatch in {function_name}(): expected {expected_type}, got {received_type}"
        hint = f"Convert '{argument_name}' to {expected_type} before passing to {function_name}()"
        return Diagnostic(
            code=DiagnosticCode.TYPE_MISMATCH,
            message=msg,
            span=None,
            hint=hint,
            help_url=f"{ErrorTemplate._DOCS_BASE}/functions.html",
            function_name=function_name,
            argument_name=argument_name,
            expected_type=expected_type,
            received_type=received_type,
            ftl_location=ftl_location,
        )

    @staticmethod
    def invalid_argument(
        function_name: str,
        argument_name: str,
        reason: str,
        *,
        ftl_location: str | None = None,
    ) -> Diagnostic:
        """Invalid argument value.

        Args:
            function_name: Function where invalid argument was provided
            argument_name: Argument name that is invalid
            reason: Why the argument is invalid
            ftl_location: FTL file location (optional)

        Returns:
            Diagnostic for INVALID_ARGUMENT
        """
        msg = f"Invalid argument '{argument_name}' in {function_name}(): {reason}"
        return Diagnostic(
            code=DiagnosticCode.INVALID_ARGUMENT,
            message=msg,
            span=None,
            hint=f"Check the value of '{argument_name}' argument",
            help_url=f"{ErrorTemplate._DOCS_BASE}/functions.html",
            function_name=function_name,
            argument_name=argument_name,
            ftl_location=ftl_location,
        )

    @staticmethod
    def argument_required(
        function_name: str,
        argument_name: str,
        *,
        ftl_location: str | None = None,
    ) -> Diagnostic:
        """Required argument not provided.

        Args:
            function_name: Function missing required argument
            argument_name: Name of required argument
            ftl_location: FTL file location (optional)

        Returns:
            Diagnostic for ARGUMENT_REQUIRED
        """
        msg = f"Required argument '{argument_name}' not provided for {function_name}()"
        return Diagnostic(
            code=DiagnosticCode.ARGUMENT_REQUIRED,
            message=msg,
            span=None,
            hint=f"Add '{argument_name}' argument to {function_name}() call",
            help_url=f"{ErrorTemplate._DOCS_BASE}/functions.html",
            function_name=function_name,
            argument_name=argument_name,
            ftl_location=ftl_location,
        )

    @staticmethod
    def pattern_invalid(
        function_name: str,
        pattern: str,
        reason: str,
        *,
        ftl_location: str | None = None,
    ) -> Diagnostic:
        """Invalid format pattern.

        Args:
            function_name: Function with invalid pattern
            pattern: The invalid pattern string
            reason: Why the pattern is invalid
            ftl_location: FTL file location (optional)

        Returns:
            Diagnostic for PATTERN_INVALID
        """
        msg = f"Invalid pattern in {function_name}(): {reason}"
        return Diagnostic(
            code=DiagnosticCode.PATTERN_INVALID,
            message=msg,
            span=None,
            hint=f"Check pattern syntax: '{pattern}'",
            help_url=f"{ErrorTemplate._DOCS_BASE}/functions.html",
            function_name=function_name,
            argument_name="pattern",
            ftl_location=ftl_location,
            severity="error",
        )

    @staticmethod
    def unknown_expression(expr_type: str) -> Diagnostic:
        """Unknown expression type encountered.

        Args:
            expr_type: The expression type name

        Returns:
            Diagnostic for UNKNOWN_EXPRESSION
        """
        msg = f"Unknown expression type: {expr_type}"
        return Diagnostic(
            code=DiagnosticCode.UNKNOWN_EXPRESSION,
            message=msg,
            span=None,
            hint="This is likely a bug in the parser or resolver",
        )

    @staticmethod
    def unexpected_eof(position: int) -> Diagnostic:
        """Unexpected end of file.

        Args:
            position: The position where EOF was encountered

        Returns:
            Diagnostic for UNEXPECTED_EOF
        """
        msg = f"Unexpected EOF at position {position}"
        return Diagnostic(
            code=DiagnosticCode.UNEXPECTED_EOF,
            message=msg,
            span=None,
            hint="Check for unclosed braces or incomplete syntax",
        )
