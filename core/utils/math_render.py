from __future__ import annotations

import re

_SUPERSCRIPTS = str.maketrans("0123456789-+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺")
_SUBSCRIPTS = str.maketrans("0123456789-+", "₀₁₂₃₄₅₆₇₈₉₋₊")


def _replace_frac(text: str) -> str:
    pattern = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")
    previous = None
    current = text
    while previous != current:
        previous = current
        current = pattern.sub(r"(\1)/(\2)", current)
    return current


def _render_superscript_group(content: str) -> str:
    if re.fullmatch(r"[0-9+-]+", content):
        return content.translate(_SUPERSCRIPTS)
    translated = re.sub(
        r"\^([0-9+-]+)",
        lambda m: m.group(1).translate(_SUPERSCRIPTS),
        content,
    )
    translated = re.sub(
        r"([0-9+-]+)",
        lambda m: m.group(1).translate(_SUPERSCRIPTS),
        translated,
    )
    return f"^({translated})"


def _render_subscript_group(content: str) -> str:
    if re.fullmatch(r"[0-9+-]+", content):
        return content.translate(_SUBSCRIPTS)
    return f"_({content})"


def render_math_for_terminal(text: str) -> str:
    rendered = text
    replacements = {
        r"\[": "",
        r"\]": "",
        r"\(": "",
        r"\)": "",
        r"\cdot": "·",
        r"\times": "×",
        r"\neq": "≠",
        r"\pm": "±",
        r"\Rightarrow": "⇒",
        r"\rightarrow": "→",
        r"\equiv": "≡",
        r"\geq": "≥",
        r"\leq": "≤",
        r"\ln": "ln",
        r"\int": "∫",
        r"\,": "",
        r"\!": "",
        r"\left": "",
        r"\right": "",
        r"\qquad": "  ",
        r"\quad": " ",
    }
    for needle, replacement in replacements.items():
        rendered = rendered.replace(needle, replacement)

    rendered = _replace_frac(rendered)
    rendered = re.sub(r"\\boxed\{([^{}]+)\}", r"\1", rendered)
    rendered = re.sub(r"\^\{([^{}]+)\}", lambda m: _render_superscript_group(m.group(1)), rendered)
    rendered = re.sub(r"_\{([^{}]+)\}", lambda m: _render_subscript_group(m.group(1)), rendered)
    rendered = re.sub(r"\^([0-9+-]+)", lambda m: m.group(1).translate(_SUPERSCRIPTS), rendered)
    rendered = re.sub(r"_([0-9+-]+)", lambda m: m.group(1).translate(_SUBSCRIPTS), rendered)
    rendered = rendered.replace("{", "").replace("}", "")
    rendered = re.sub(r"[ \t]+\n", "\n", rendered)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered)
    return rendered.strip()
