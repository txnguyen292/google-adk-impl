---
name: math
description: Use for arithmetic, calculator-style tasks, and supported simple first-order ordinary differential equations.
allowed-tools: add, subtract, multiply, divide, format_math_response
---

# Math Skill

Use this skill for arithmetic problems, stepwise numeric calculations, expression evaluation, and supported simple first-order ordinary differential equations.

## Instructions

1. Use the arithmetic tools for every calculation step.
2. Do not do mental math when a tool can be used instead.
3. If division by zero occurs, report the tool error clearly.
4. If the user asks for an ordinary differential equation, you MUST first call `load_skill_resource` for `references/differential-equations.md` before using any differential-equation-specific tool.
5. For arithmetic, use the arithmetic tools to compute the final numeric result.
6. After solving any math problem, call `format_math_response` with the original expression or equation plus the computed result.
7. Do not present the final result before `format_math_response` has been used.
8. In the user-facing reply, prefer `pretty_equation` and `final_answer` unless the user explicitly asks for raw LaTeX or metadata.
9. Every mathematical step in the explanation must be written in plain, readable math text, not raw LaTeX markup.
10. Write steps like `dy/dx = y`, `1/y dy = dx`, `ln|y| = x + C`, and `y(x) = C1*exp(x)` instead of `\frac`, `\[...\]`, `\(...\)`, or `\boxed{...}` blocks.
11. Format every intermediate math step in the same plain readable style as the final result.
12. Do not expose `family`, `families`, `latex_equation`, or `latex_problem` unless the user explicitly asks for them.
13. Do not replace the formatted final result with your own LaTeX or alternate wording.
