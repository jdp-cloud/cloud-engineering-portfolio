"""Load the expected-artifact YAML with the standard library.

The file only uses mappings, lists, scalars, and comments. A subset loader keeps
the Lambda zip free of a PyYAML wheel, which would otherwise be built for the
laptop and fail on Amazon Linux.
"""

from __future__ import annotations

import re

_INT = re.compile(r"-?(0|[1-9][0-9]*)")


def loads(text: str):
    lines = _prepare(text)
    if not lines:
        return None
    value, index = _parse_node(lines, 0)
    if index != len(lines):
        number = lines[index][0]
        raise ValueError(f"Could not parse the full YAML file. Stopped at line {number}.")
    return value


def _prepare(text: str) -> list[tuple[int, int, str]]:
    prepared: list[tuple[int, int, str]] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw:
            raise ValueError(f"Line {number} uses a tab. Indent with spaces.")
        code = _strip_comment(raw).rstrip()
        if not code.strip():
            continue
        indent = len(code) - len(code.lstrip(" "))
        prepared.append((number, indent, code.strip()))
    return prepared


def _strip_comment(line: str) -> str:
    in_quote = False
    quote = ""
    for index, char in enumerate(line):
        if char in {'"', "'"}:
            if not in_quote:
                in_quote = True
                quote = char
            elif char == quote:
                in_quote = False
        elif char == "#" and not in_quote:
            return line[:index]
    return line


def _parse_node(lines, index):
    content = lines[index][2]
    if content.startswith("- "):
        return _parse_list(lines, index, lines[index][1])
    return _parse_map(lines, index, lines[index][1])


def _parse_map(lines, index, indent):
    mapping: dict = {}
    while index < len(lines):
        number, line_indent, content = lines[index]
        if line_indent < indent or content.startswith("- "):
            break
        if line_indent > indent:
            raise ValueError(f"Line {number} is indented too far.")
        key, raw_value, nested = _split_key(content, number)
        if key is None:
            raise ValueError(f"Line {number} is not a key.")
        if key in mapping:
            raise ValueError(f"Line {number} repeats key {key}.")
        index += 1
        if nested:
            if index < len(lines) and lines[index][1] > indent:
                mapping[key], index = _parse_node(lines, index)
            else:
                mapping[key] = None
        else:
            mapping[key] = _scalar(raw_value)
    return mapping, index


def _parse_list(lines, index, indent):
    items = []
    while index < len(lines):
        number, line_indent, content = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError(f"Line {number} is indented too far for this list.")
        if not content.startswith("- "):
            break
        body = content[2:].strip()
        index += 1
        if body == "":
            if index < len(lines) and lines[index][1] > indent:
                value, index = _parse_node(lines, index)
                items.append(value)
            else:
                items.append(None)
            continue
        key, raw_value, nested = _split_key(body, number)
        if key is None:
            items.append(_scalar(body))
            continue
        item: dict = {}
        if nested:
            if index < len(lines) and lines[index][1] > indent:
                item[key], index = _parse_node(lines, index)
            else:
                item[key] = None
        else:
            item[key] = _scalar(raw_value)
        if index < len(lines) and lines[index][1] > indent:
            extra, index = _parse_map(lines, index, lines[index][1])
            overlap = set(item).intersection(extra)
            if overlap:
                raise ValueError(f"Repeated key {sorted(overlap)[0]} near line {number}.")
            item.update(extra)
        items.append(item)
    return items, index


def _split_key(content: str, number: int):
    in_quote = False
    quote = ""
    for index, char in enumerate(content):
        if char in {'"', "'"}:
            if not in_quote:
                in_quote = True
                quote = char
            elif char == quote:
                in_quote = False
        elif char == ":" and not in_quote:
            key = content[:index].strip()
            if not key:
                raise ValueError(f"Line {number} has an empty key.")
            rest = content[index + 1 :].strip()
            if rest == "":
                return key, None, True
            return key, rest, False
    return None, content, False


def _scalar(raw: str):
    text = raw.strip()
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    if text in {"null", "~", ""}:
        return None
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if _INT.fullmatch(text):
        return int(text)
    return text
