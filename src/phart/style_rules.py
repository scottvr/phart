"""Style rule parsing and evaluation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


Token = Tuple[str, Any]


@dataclass(frozen=True)
class CompiledStyleRule:
    """Compiled style rule with parsed predicate."""

    target: str
    priority: int
    order: int
    predicate: Callable[[Dict[str, Any]], bool]
    set_values: Dict[str, str]


def _tokenize(expr: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    length = len(expr)
    while i < length:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue

        if expr.startswith("==", i):
            tokens.append(("EQ", "=="))
            i += 2
            continue
        if expr.startswith("!=", i):
            tokens.append(("NE", "!="))
            i += 2
            continue

        if ch in "(),[]":
            tokens.append((ch, ch))
            i += 1
            continue
        if ch == ",":
            tokens.append(("COMMA", ","))
            i += 1
            continue

        if ch in {"'", '"'}:
            quote = ch
            i += 1
            value_chars: List[str] = []
            while i < length:
                curr = expr[i]
                if curr == "\\" and i + 1 < length:
                    value_chars.append(expr[i + 1])
                    i += 2
                    continue
                if curr == quote:
                    i += 1
                    break
                value_chars.append(curr)
                i += 1
            else:
                raise ValueError("Unterminated string literal in style rule expression")
            tokens.append(("STRING", "".join(value_chars)))
            continue

        if ch.isdigit() or (ch == "-" and i + 1 < length and expr[i + 1].isdigit()):
            start = i
            i += 1
            while i < length and (expr[i].isdigit() or expr[i] == "."):
                i += 1
            text = expr[start:i]
            if text.count(".") > 1:
                raise ValueError(f"Invalid numeric literal '{text}'")
            tokens.append(("NUMBER", float(text) if "." in text else int(text)))
            continue

        if ch.isalpha() or ch == "_":
            start = i
            i += 1
            while i < length and (expr[i].isalnum() or expr[i] in {"_", "."}):
                i += 1
            ident = expr[start:i]
            lowered = ident.lower()
            if lowered in {"and", "or", "not", "in"}:
                tokens.append((lowered.upper(), lowered))
            elif lowered == "true":
                tokens.append(("BOOL", True))
            elif lowered == "false":
                tokens.append(("BOOL", False))
            elif lowered == "null":
                tokens.append(("NULL", None))
            else:
                tokens.append(("IDENT", ident))
            continue

        raise ValueError(f"Unexpected character '{ch}' in style rule expression")

    tokens.append(("EOF", None))
    return tokens


class _ExprParser:
    """Recursive-descent parser for style-rule predicates."""

    def __init__(self, tokens: Sequence[Token]):
        self.tokens = tokens
        self.index = 0

    def _peek(self) -> Token:
        return self.tokens[self.index]

    def _advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _match(self, *types: str) -> Optional[Token]:
        token = self._peek()
        if token[0] in types:
            return self._advance()
        return None

    def _expect(self, token_type: str) -> Token:
        token = self._match(token_type)
        if token is None:
            found = self._peek()[0]
            raise ValueError(f"Expected {token_type}, found {found}")
        return token

    def parse(self) -> Any:
        expr = self._parse_or()
        self._expect("EOF")
        return expr

    def _parse_or(self) -> Any:
        expr = self._parse_and()
        while self._match("OR"):
            right = self._parse_and()
            expr = ("or", expr, right)
        return expr

    def _parse_and(self) -> Any:
        expr = self._parse_not()
        while self._match("AND"):
            right = self._parse_not()
            expr = ("and", expr, right)
        return expr

    def _parse_not(self) -> Any:
        if self._match("NOT"):
            return ("not", self._parse_not())
        return self._parse_comparison()

    def _parse_comparison(self) -> Any:
        left = self._parse_primary()
        token = self._peek()
        token_type = token[0]
        if token_type in {"EQ", "NE"}:
            self._advance()
            right = self._parse_primary()
            op = "==" if token_type == "EQ" else "!="
            return ("cmp", op, left, right)
        if token_type == "IN":
            self._advance()
            right = self._parse_primary()
            return ("cmp", "in", left, right)
        if token_type == "NOT":
            checkpoint = self.index
            self._advance()
            if self._match("IN"):
                right = self._parse_primary()
                return ("cmp", "not in", left, right)
            self.index = checkpoint
        return left

    def _parse_primary(self) -> Any:
        token = self._peek()
        token_type, token_value = token
        if token_type in {"STRING", "NUMBER", "BOOL", "NULL"}:
            self._advance()
            return ("lit", token_value)
        if token_type == "IDENT":
            self._advance()
            return ("ident", token_value)
        if self._match("("):
            expr = self._parse_or()
            self._expect(")")
            return expr
        if self._match("["):
            values: List[Any] = []
            if not self._match("]"):
                while True:
                    item = self._parse_primary()
                    values.append(item)
                    if self._match("]"):
                        break
                    self._expect("COMMA")
            return ("list", values)
        raise ValueError(f"Unexpected token {token_type} in style rule expression")


def _normalize_string(value: Any) -> Any:
    return value.casefold() if isinstance(value, str) else value


def _find_key_case_insensitive(data: Dict[str, Any], key: str) -> Optional[str]:
    if key in data:
        return key
    lowered = key.casefold()
    for existing in data:
        if isinstance(existing, str) and existing.casefold() == lowered:
            return existing
    return None


def _resolve_path(context: Dict[str, Any], path: str) -> Any:
    root_name = path
    remainder = ""
    if "." in path:
        root_name, remainder = path.split(".", 1)
    if root_name not in {"self", "edge", "node", "u", "v"}:
        root_name = "self"
        remainder = path

    current = context.get(root_name)
    if remainder == "":
        return current

    for segment in remainder.split("."):
        if not isinstance(current, dict):
            return None
        key = _find_key_case_insensitive(current, segment)
        if key is None:
            return None
        current = current.get(key)
    return current


def _evaluate_ast(ast: Any, context: Dict[str, Any]) -> Any:
    kind = ast[0]
    if kind == "lit":
        return ast[1]
    if kind == "ident":
        return _resolve_path(context, ast[1])
    if kind == "list":
        return [_evaluate_ast(item, context) for item in ast[1]]
    if kind == "not":
        return not bool(_evaluate_ast(ast[1], context))
    if kind == "and":
        return bool(_evaluate_ast(ast[1], context)) and bool(
            _evaluate_ast(ast[2], context)
        )
    if kind == "or":
        return bool(_evaluate_ast(ast[1], context)) or bool(
            _evaluate_ast(ast[2], context)
        )
    if kind == "cmp":
        op = ast[1]
        left = _evaluate_ast(ast[2], context)
        right = _evaluate_ast(ast[3], context)
        if op == "==":
            return _normalize_string(left) == _normalize_string(right)
        if op == "!=":
            return _normalize_string(left) != _normalize_string(right)
        if op in {"in", "not in"}:
            result = False
            if isinstance(right, (list, tuple, set)):
                left_norm = _normalize_string(left)
                right_norm = [_normalize_string(item) for item in right]
                result = left_norm in right_norm
            elif isinstance(right, str):
                if left is None:
                    result = False
                else:
                    result = str(left).casefold() in right.casefold()
            if op == "not in":
                return not result
            return result
    raise ValueError("Invalid style rule AST")


def compile_predicate(expression: str) -> Callable[[Dict[str, Any]], bool]:
    """Compile a style rule predicate into a callable."""
    text = str(expression).strip()
    if not text:
        return lambda _ctx: True
    tokens = _tokenize(text)
    ast = _ExprParser(tokens).parse()

    def _predicate(context: Dict[str, Any]) -> bool:
        return bool(_evaluate_ast(ast, context))

    return _predicate


def _normalize_set_values(raw_set: Any) -> Dict[str, str]:
    if not isinstance(raw_set, dict):
        raise ValueError("style rule 'set' must be a dict")
    normalized: Dict[str, str] = {}
    for key, value in raw_set.items():
        key_text = str(key).strip().lower()
        if not key_text:
            raise ValueError("style rule set keys cannot be empty")
        value_text = str(value).strip()
        if not value_text:
            raise ValueError("style rule set values cannot be empty")
        normalized[key_text] = value_text
    return normalized


def compile_style_rules(raw_rules: Iterable[Dict[str, Any]]) -> List[CompiledStyleRule]:
    """Compile canonical style rule dictionaries."""
    compiled: List[CompiledStyleRule] = []
    for order, raw in enumerate(raw_rules):
        if not isinstance(raw, dict):
            raise ValueError("Each style rule must be a dict")
        target = str(raw.get("target", "")).strip().lower()
        if target not in {"edge", "node"}:
            raise ValueError("style rule target must be 'edge' or 'node'")
        priority_raw = raw.get("priority", 0)
        try:
            priority = int(priority_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("style rule priority must be an integer") from exc
        set_values = _normalize_set_values(raw.get("set", {}))
        predicate = compile_predicate(str(raw.get("when", "")).strip())
        compiled.append(
            CompiledStyleRule(
                target=target,
                priority=priority,
                order=order,
                predicate=predicate,
                set_values=set_values,
            )
        )
    compiled.sort(key=lambda rule: (-rule.priority, rule.order))
    return compiled


def evaluate_style_rule_color(
    compiled_rules: Sequence[CompiledStyleRule], target: str, context: Dict[str, Any]
) -> Optional[str]:
    """Return first matching color assignment for the target context."""
    for rule in compiled_rules:
        if rule.target != target:
            continue
        if not rule.set_values.get("color"):
            continue
        if rule.predicate(context):
            return rule.set_values["color"]
    return None
