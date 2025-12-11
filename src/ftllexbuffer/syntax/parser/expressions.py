"""Expression parsing for Fluent FTL parser.

This module provides parsers for inline expressions, select expressions,
function calls, and other expression types.
"""

from ftllexbuffer.syntax.ast import (
    CallArguments,
    FunctionReference,
    Identifier,
    InlineExpression,
    MessageReference,
    NamedArgument,
    NumberLiteral,
    Placeable,
    SelectExpression,
    StringLiteral,
    TermReference,
    VariableReference,
    Variant,
)
from ftllexbuffer.syntax.cursor import Cursor, ParseResult
from ftllexbuffer.syntax.parser.primitives import (
    parse_identifier,
    parse_number,
    parse_number_value,
    parse_string_literal,
)
from ftllexbuffer.syntax.parser.whitespace import skip_blank, skip_blank_inline


def parse_variant_key(cursor: Cursor) -> ParseResult[Identifier | NumberLiteral] | None:
    """Parse variant key (identifier or number).

    Helper method extracted from parse_variant to reduce complexity.

    Args:
        cursor: Current position in source

    Returns:
        Success(ParseResult(Identifier | NumberLiteral, cursor)) on success
        Failure(ParseError(...)) on parse error
    """
    # Try number first
    if not cursor.is_eof and (cursor.current.isdigit() or cursor.current == "-"):
        num_result = parse_number(cursor)
        if num_result is not None:
            num_parse = num_result
            num_str = num_parse.value
            num_value = parse_number_value(num_str)
            return ParseResult(
                NumberLiteral(value=num_value, raw=num_str), num_parse.cursor
            )

        # Failed to parse as number, try identifier
        id_result = parse_identifier(cursor)
        if id_result is None:
            # Both failed - return parse error
            return None  # "Expected variant key (identifier or number)", cursor

        id_parse = id_result
        return ParseResult(Identifier(id_parse.value), id_parse.cursor)

    # Parse as identifier
    id_result = parse_identifier(cursor)
    if id_result is None:
        return id_result

    id_parse = id_result
    return ParseResult(Identifier(id_parse.value), id_parse.cursor)


def parse_variant(cursor: Cursor) -> ParseResult[Variant] | None:
    """Parse variant: [key] pattern or *[key] pattern

    Variants are the cases in a select expression.

    Examples:
        [zero] no items
        *[other] many items

    Args:
        cursor: Current position in source

    Returns:
        Success(ParseResult(Variant, new_cursor)) on success
        Failure(ParseError(...)) on parse error
    """
    # Import here to avoid circular dependency
    from .patterns import parse_simple_pattern  # noqa: PLC0415

    # Check for default marker *
    is_default = False
    if not cursor.is_eof and cursor.current == "*":
        is_default = True
        cursor = cursor.advance()

    # Expect [
    if cursor.is_eof or cursor.current != "[":
        return None  # "Expected '[' at start of variant", cursor

    cursor = cursor.advance()  # Skip [

    # Parse variant key (identifier or number) using extracted helper
    # Per spec: VariantKey ::= "[" blank? (NumberLiteral | Identifier) blank? "]"
    cursor = skip_blank_inline(cursor)
    key_result = parse_variant_key(cursor)
    if key_result is None:
        return key_result

    key_parse = key_result
    variant_key = key_parse.value
    cursor = skip_blank_inline(key_parse.cursor)

    # Expect ]
    if cursor.is_eof or cursor.current != "]":
        return None  # "Expected ']' after variant key", cursor

    cursor = cursor.advance()  # Skip ]
    # After ], before pattern: blank_inline (same line) or newline+indent
    cursor = skip_blank_inline(cursor)

    # Parse pattern (on same line or next line with indent)
    # Simplified: parse until newline that's not indented
    pattern_result = parse_simple_pattern(cursor)
    if pattern_result is None:
        return pattern_result

    pattern_parse = pattern_result

    # Don't skip trailing whitespace - let select expression parser handle it
    variant = Variant(key=variant_key, value=pattern_parse.value, default=is_default)
    return ParseResult(variant, pattern_parse.cursor)


def parse_select_expression(
    cursor: Cursor, selector: InlineExpression, _start_pos: int
) -> ParseResult[SelectExpression] | None:
    """Parse select expression after seeing selector and ->

    Format: {$var -> [key1] value1 *[key2] value2}

    The selector has already been parsed.

    Example:
        After parsing {$count and seeing ->, we parse:
        [zero] {$count} items
        [one] {$count} item
        *[other] {$count} items
        }

    Args:
        cursor: Current position (should be after ->)
        selector: The selector expression (e.g., VariableReference($count))
        _start_pos: Start position of the selector (reserved for future span tracking)

    Returns:
        Success(ParseResult(SelectExpression, new_cursor)) on success
        Failure(ParseError(...)) on parse error
    """
    # Per spec: SelectExpression ::= InlineExpression blank? "->" blank_inline? variant_list
    # After ->, we need blank_inline before variant list starts (could be on next line)
    # variant_list allows line_end, so use skip_blank to handle newlines
    cursor = skip_blank(cursor)

    # Parse variants
    variants: list[Variant] = []

    while not cursor.is_eof:
        # Within variant_list, allow blank (spaces and newlines)
        cursor = skip_blank(cursor)

        # Check for end of select }
        if cursor.current == "}":
            break

        # Parse variant
        variant_result = parse_variant(cursor)
        if variant_result is None:
            return variant_result

        variant_parse = variant_result
        variants.append(variant_parse.value)
        cursor = variant_parse.cursor

    if not variants:
        return None  # "Select expression must have at least one variant", cursor

    # Validate exactly one default variant (FTL spec requirement)
    default_count = sum(1 for v in variants if v.default)
    if default_count == 0:
        return None  # "Select expression must have exactly one default variant (marked with *)"
    if default_count > 1:
        return None  # "Select expression must have exactly one default variant, found multiple"

    select_expr = SelectExpression(selector=selector, variants=tuple(variants))
    return ParseResult(select_expr, cursor)


def parse_argument_expression(cursor: Cursor) -> ParseResult[InlineExpression] | None:  # noqa: PLR0911
    """Parse a single argument expression (variable, string, number, or identifier).

    Helper method extracted from parse_call_arguments to reduce complexity.

    Args:
        cursor: Current position in source

    Returns:
        Success(ParseResult(InlineExpression, cursor)) on success
        Failure(ParseError(...)) on parse error
    """
    # Import here to avoid circular dependency
    from .patterns import parse_variable_reference  # noqa: PLC0415

    if cursor.current == "$":
        var_result = parse_variable_reference(cursor)
        if var_result is None:
            return var_result
        var_parse = var_result
        return ParseResult(var_parse.value, var_parse.cursor)

    if cursor.current == '"':
        str_result = parse_string_literal(cursor)
        if str_result is None:
            return str_result
        str_parse = str_result
        return ParseResult(StringLiteral(value=str_parse.value), str_parse.cursor)

    if cursor.current.isdigit() or cursor.current == "-":
        num_result = parse_number(cursor)
        if num_result is None:
            return num_result
        num_parse = num_result
        num_str = num_parse.value
        num_value = parse_number_value(num_str)
        return ParseResult(
            NumberLiteral(value=num_value, raw=num_str), num_parse.cursor
        )

    if cursor.current.isalpha():
        id_result = parse_identifier(cursor)
        if id_result is None:
            return id_result
        id_parse = id_result
        return ParseResult(
            MessageReference(id=Identifier(id_parse.value)), id_parse.cursor
        )

    return None  # "Expected argument expression (variable, string, number, or identifier)"


def parse_call_arguments(cursor: Cursor) -> ParseResult[CallArguments] | None:  # noqa: PLR0911
    """Parse function call arguments: (pos1, pos2, name1: val1, name2: val2)

    Arguments consist of positional arguments followed by named arguments.
    Positional arguments must come before named arguments.
    Named argument names must be unique.

    Examples:
        ($value) → CallArguments(positional=[$value], named=[])
        ($value, minimumFractionDigits: 2) → CallArguments with both types

    Args:
        cursor: Position AFTER the opening '('

    Returns:
        Success(ParseResult(CallArguments, cursor_after_))) on success
        Failure(ParseError(...)) on parse error
    """
    # Per spec: CallArguments ::= blank? "(" blank? argument_list blank? ")"
    cursor = skip_blank_inline(cursor)

    positional: list[InlineExpression] = []
    named: list[NamedArgument] = []
    seen_named_arg_names: set[str] = set()
    seen_named = False  # Track if we've seen any named args

    # Parse comma-separated arguments
    while not cursor.is_eof:
        cursor = skip_blank_inline(cursor)

        # Check for end of arguments
        if cursor.current == ")":
            break

        # Parse the argument expression using extracted helper
        arg_result = parse_argument_expression(cursor)
        if arg_result is None:
            return arg_result

        arg_parse = arg_result
        arg_expr = arg_parse.value
        cursor = skip_blank_inline(arg_parse.cursor)

        # Check if this is a named argument (followed by :)
        if not cursor.is_eof and cursor.current == ":":
            # This is a named argument
            cursor = cursor.advance()  # Skip :
            cursor = skip_blank_inline(cursor)

            # The argument expression must be an identifier (MessageReference)
            if not isinstance(arg_expr, MessageReference):
                return None  # "Named argument name must be an identifier", cursor

            arg_name = arg_expr.id.name

            # Check for duplicate named argument names
            if arg_name in seen_named_arg_names:
                return None  # f"Duplicate named argument: '{arg_name}'", cursor
            seen_named_arg_names.add(arg_name)

            # Parse the value (must be inline expression)
            if cursor.is_eof:
                return None  # "Expected value after ':'", cursor

            # Parse value expression using extracted helper
            value_result = parse_argument_expression(cursor)
            if value_result is None:
                return value_result

            value_parse = value_result
            value_expr = value_parse.value
            cursor = value_parse.cursor

            # Per FTL spec: NamedArgument ::= Identifier ":" (StringLiteral | NumberLiteral)
            # Named argument values MUST be literals, NOT references or variables
            if not isinstance(value_expr, (StringLiteral, NumberLiteral)):
                # Named argument values must be literals per FTL spec
                # This restriction enables static analysis by translation tools
                return None  # f"Named argument '{arg_name}' requires a literal value", cursor

            named.append(NamedArgument(name=Identifier(arg_name), value=value_expr))
            seen_named = True

        else:
            # This is a positional argument
            if seen_named:
                return None  # "Positional arguments must come before named arguments", cursor
            positional.append(arg_expr)

        cursor = skip_blank_inline(cursor)

        # Check for comma (optional before closing paren)
        if not cursor.is_eof and cursor.current == ",":
            cursor = cursor.advance()  # Skip comma
            cursor = skip_blank_inline(cursor)

    call_args = CallArguments(positional=tuple(positional), named=tuple(named))
    return ParseResult(call_args, cursor)


def parse_function_reference(cursor: Cursor) -> ParseResult[FunctionReference] | None:
    """Parse function reference: FUNCTION(args)

    Function names must be uppercase identifiers.

    Examples:
        NUMBER($value)
        NUMBER($value, minimumFractionDigits: 2)
        DATETIME($date, dateStyle: "full")

    Args:
        cursor: Position at start of function name

    Returns:
        Success(ParseResult(FunctionReference, cursor_after_))) on success
        Failure(ParseError(...)) on parse error
    """
    # Parse function name (must be uppercase identifier)
    id_result = parse_identifier(cursor)
    if id_result is None:
        return id_result

    id_parse = id_result
    func_name = id_parse.value

    # Validate function name is uppercase
    if not func_name.isupper():
        return None  # f"Function name must be uppercase: '{func_name}'", id_parse.cursor

    # Per spec: FunctionReference uses blank? before "("
    cursor = skip_blank_inline(id_parse.cursor)

    # Expect opening parenthesis
    if cursor.is_eof or cursor.current != "(":
        return None  # "Expected '(' after function name", cursor

    cursor = cursor.advance()  # Skip (

    # Parse arguments
    args_result = parse_call_arguments(cursor)
    if args_result is None:
        return args_result

    args_parse = args_result
    cursor = skip_blank_inline(args_parse.cursor)

    # Expect closing parenthesis
    if cursor.is_eof or cursor.current != ")":
        return None  # "Expected ')' after function arguments"

    cursor = cursor.advance()  # Skip )

    func_ref = FunctionReference(id=Identifier(func_name), arguments=args_parse.value)
    return ParseResult(func_ref, cursor)


def parse_term_reference(cursor: Cursor) -> ParseResult[TermReference] | None:
    """Parse term reference in inline expression (-term-id or -term.attr).

    FTL syntax:
        { -brand }
        { -brand.short }
        { -brand(case: "nominative") }

    Term references can have optional attribute access and arguments.

    Args:
        cursor: Current position (should be at '-')

    Returns:
        Success(ParseResult(TermReference, new_cursor)) on success
        Failure(ParseError(...)) on parse error
    """
    # Expect '-' prefix
    if cursor.is_eof or cursor.current != "-":
        return None  # "Expected '-' at start of term reference", cursor, expected=["-"]

    cursor = cursor.advance()  # Skip '-'

    # Parse identifier
    id_result = parse_identifier(cursor)
    if id_result is None:
        return id_result

    id_parse = id_result
    cursor = id_parse.cursor

    # Check for optional attribute access (.attribute)
    attribute: Identifier | None = None
    if not cursor.is_eof and cursor.current == ".":
        cursor = cursor.advance()  # Skip '.'

        attr_id_result = parse_identifier(cursor)
        if attr_id_result is None:
            return attr_id_result

        attr_id_parse = attr_id_result
        attribute = Identifier(attr_id_parse.value)
        cursor = attr_id_parse.cursor

    # Check for optional arguments (case: "nominative")
    # Per spec: TermReference uses blank? before "("
    cursor = skip_blank_inline(cursor)

    arguments: CallArguments | None = None
    if not cursor.is_eof and cursor.current == "(":
        # Parse call arguments (reuse function argument parsing)
        cursor = cursor.advance()  # Skip '('
        args_result = parse_call_arguments(cursor)
        if args_result is None:
            return args_result

        args_parse = args_result
        cursor = skip_blank_inline(args_parse.cursor)

        # Expect closing parenthesis
        if cursor.is_eof or cursor.current != ")":
            return None  # "Expected ')' after term arguments"

        cursor = cursor.advance()  # Skip ')'
        arguments = args_parse.value

    term_ref = TermReference(
        id=Identifier(id_parse.value), attribute=attribute, arguments=arguments
    )

    return ParseResult(term_ref, cursor)


def parse_inline_expression(  # noqa: PLR0911, PLR0912, PLR0915
    cursor: Cursor,
) -> ParseResult[
    InlineExpression
] | None:
    """Parse inline expression (variable, string, number, function, message, or term reference).

    Helper method extracted to reduce complexity in parse_placeable.

    Handles:
    - Variable references: $var
    - String literals: "text"
    - Number literals: 42
    - Function calls: NUMBER(args)
    - Message references: identifier
    - Term references: -term-id

    Args:
        cursor: Current position in source

    Returns:
        Success(ParseResult(expression, cursor)) on success
        Failure(ParseError(...)) on parse error
    """
    # Import here to avoid circular dependency
    from .patterns import parse_variable_reference  # noqa: PLC0415

    if not cursor.is_eof and cursor.current == "$":
        # Parse variable reference
        var_result = parse_variable_reference(cursor)
        if var_result is None:
            return var_result
        var_parse = var_result
        return ParseResult(var_parse.value, var_parse.cursor)

    if not cursor.is_eof and cursor.current == '"':
        # Parse string literal
        str_result = parse_string_literal(cursor)
        if str_result is None:
            return str_result
        str_parse = str_result
        return ParseResult(StringLiteral(value=str_parse.value), str_parse.cursor)

    if not cursor.is_eof and cursor.current == "-":
        # Could be negative number or term reference
        # Peek ahead to distinguish: -123 is number, -brand is term
        next_cursor = cursor.advance()
        if not next_cursor.is_eof and next_cursor.current.isalpha():
            # It's a term reference: -brand
            term_result = parse_term_reference(cursor)
            if term_result is None:
                return term_result
            term_parse = term_result
            return ParseResult(term_parse.value, term_parse.cursor)
        # It's a negative number: -123
        num_result = parse_number(cursor)
        if num_result is None:
            return num_result
        num_parse = num_result
        num_str = num_parse.value
        num_value = parse_number_value(num_str)
        return ParseResult(
            NumberLiteral(value=num_value, raw=num_str), num_parse.cursor
        )

    if not cursor.is_eof and cursor.current.isdigit():
        # Parse number literal
        num_result = parse_number(cursor)
        if num_result is None:
            return num_result
        num_parse = num_result
        num_str = num_parse.value
        num_value = parse_number_value(num_str)
        return ParseResult(
            NumberLiteral(value=num_value, raw=num_str), num_parse.cursor
        )

    if not cursor.is_eof and cursor.current.isupper():
        # Might be a function call (uppercase identifier followed by '(')
        # Peek ahead to check for opening parenthesis
        id_result = parse_identifier(cursor)
        if id_result is None:
            return id_result

        id_parse = id_result
        func_name = id_parse.value

        # Check if uppercase and followed by '('
        cursor_after_id = skip_blank_inline(id_parse.cursor)
        is_function_call = (
            func_name.isupper()
            and not cursor_after_id.is_eof
            and cursor_after_id.current == "("
        )
        if is_function_call:
            # It's a function call! Parse it fully
            func_result = parse_function_reference(cursor)
            if func_result is None:
                return func_result
            func_parse = func_result
            return ParseResult(func_parse.value, func_parse.cursor)

        # Not a function - must be a message reference (lowercase or no parens)
        # Check for optional attribute access (.attribute)
        cursor_after_id = id_parse.cursor
        attribute: Identifier | None = None

        if not cursor_after_id.is_eof and cursor_after_id.current == ".":
            cursor_after_id = cursor_after_id.advance()  # Skip '.'

            attr_id_result = parse_identifier(cursor_after_id)
            if attr_id_result is None:
                return attr_id_result

            attr_id_parse = attr_id_result
            attribute = Identifier(attr_id_parse.value)
            cursor_after_id = attr_id_parse.cursor

        return ParseResult(
            MessageReference(id=Identifier(func_name), attribute=attribute),
            cursor_after_id
        )

    # Try parsing as lowercase message reference (msg or msg.attr)
    if not cursor.is_eof and (cursor.current.islower() or cursor.current == "_"):
        id_result = parse_identifier(cursor)
        if id_result is None:
            return id_result

        id_parse = id_result
        msg_name = id_parse.value
        cursor_after_id = id_parse.cursor
        msg_attribute: Identifier | None = None

        # Check for optional attribute access (.attribute)
        if not cursor_after_id.is_eof and cursor_after_id.current == ".":
            cursor_after_id = cursor_after_id.advance()  # Skip '.'

            attr_id_result = parse_identifier(cursor_after_id)
            if attr_id_result is None:
                return attr_id_result

            attr_id_parse = attr_id_result
            msg_attribute = Identifier(attr_id_parse.value)
            cursor_after_id = attr_id_parse.cursor

        return ParseResult(
            MessageReference(id=Identifier(msg_name), attribute=msg_attribute),
            cursor_after_id
        )

    return None  # 'Expected variable ($var), string (""), number, or function call'


def parse_placeable(cursor: Cursor) -> ParseResult[Placeable] | None:
    """Parse placeable expression: {$var}, {"\n"}, {$var -> [key] value}, or {FUNC()}.

    Parser combinator helper that reduces nesting in parse_pattern().

    Handles:
    - Variable references: {$var}
    - String literals: {"\n"}
    - Number literals: {42}
    - Select expressions: {$var -> [one] item *[other] items}
    - Function calls: {NUMBER($value, minimumFractionDigits: 2)}

    Args:
        cursor: Position AFTER the opening '{'

    Returns:
        Success(ParseResult(Placeable, cursor_after_})) on success
        Failure(ParseError(...)) on parse error

    Example:
        cursor at: "$var}"  → parses to Placeable(VariableReference("var"))
        cursor at: "\"\n\"}" → parses to Placeable(StringLiteral("\n"))
        cursor at: "$n -> [one] 1 *[other] N}" → parses to Placeable(SelectExpression(...))
        cursor at: "NUMBER($val)}" → parses to Placeable(FunctionReference(...))
    """
    # Per spec: inline_placeable ::= "{" blank? (SelectExpression | InlineExpression) blank? "}"
    cursor = skip_blank_inline(cursor)

    # Capture start position before parsing expression (for select expression span)
    expr_start_pos = cursor.pos

    # Parse the inline expression using extracted helper
    expr_result = parse_inline_expression(cursor)
    if expr_result is None:
        return expr_result

    expr_parse = expr_result
    expression = expr_parse.value
    parse_result_cursor = expr_parse.cursor

    cursor = skip_blank_inline(parse_result_cursor)

    # Check for select expression (->)
    # Per FTL 1.0 spec: SelectExpression ::= InlineExpression blank? "->" ...
    # Valid selectors (any InlineExpression):
    #   - VariableReference: { $var -> ... }
    #   - StringLiteral: { "foo" -> ... }
    #   - NumberLiteral: { 42 -> ... }
    #   - FunctionReference: { NUMBER($x) -> ... }
    #   - MessageReference: { msg -> ... } or { msg.attr -> ... }
    #   - TermReference: { -term -> ... } or { -term.attr -> ... }
    is_valid_selector = isinstance(
        expression,
        (
            VariableReference,
            StringLiteral,
            NumberLiteral,
            FunctionReference,
            MessageReference,
            TermReference,
        ),
    )

    if is_valid_selector and not cursor.is_eof and cursor.current == "-":
        # Peek ahead for ->
        next_cursor = cursor.advance()
        if not next_cursor.is_eof and next_cursor.current == ">":
            # It's a select expression!
            cursor = next_cursor.advance()  # Skip ->

            select_result = parse_select_expression(cursor, expression, expr_start_pos)
            if select_result is None:
                return select_result

            select_parse = select_result
            cursor = skip_blank_inline(select_parse.cursor)

            # Expect }
            if cursor.is_eof or cursor.current != "}":
                return None  # "Expected '}' after select expression", cursor

            cursor = cursor.advance()  # Skip }
            return ParseResult(Placeable(expression=select_parse.value), cursor)

    # Just a simple inline expression {$var}, {"\n"}, or {42}
    # Expect }
    if cursor.is_eof or cursor.current != "}":
        return None  # "Expected '}'", cursor

    cursor = cursor.advance()  # Skip }
    return ParseResult(Placeable(expression=expression), cursor)
