from __future__ import annotations

import ast
import re
from typing import List


NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")


def extract_numbers(text: str) -> List[float]:
    cleaned = text.replace(",", "")
    numbers: List[float] = []
    for match in NUMBER_PATTERN.findall(cleaned):
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    return numbers


def extract_expression(text: str) -> str | None:
    cleaned = text.replace(",", "")
    match = re.search(r"(-?\d+(?:\.\d+)?\s*[\+\-*/]\s*-?\d+(?:\.\d+)?(?:\s*[\+\-*/]\s*-?\d+(?:\.\d+)?)+)", cleaned)
    if match:
        return match.group(1)
    match = re.search(r"(-?\d+(?:\.\d+)?\s*[\+\-*/]\s*-?\d+(?:\.\d+)?)", cleaned)
    if match:
        return match.group(1)
    return None


def parse_expression(expr: str) -> ast.Expression:
    parsed = ast.parse(expr, mode="eval")
    return parsed
