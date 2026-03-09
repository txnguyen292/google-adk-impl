---
name: math
description: Use for arithmetic, calculator-style tasks, and supported simple first-order ordinary differential equations.
allowed-tools: add, subtract, multiply, divide, solve_differential_equation, format_math_response
---

# Math Skill

Use this skill for arithmetic problems, stepwise numeric calculations, expression evaluation, and supported simple first-order ordinary differential equations.

## Instructions

1. Use the arithmetic tools for every calculation step.
2. Do not do mental math when a tool can be used instead.
3. If division by zero occurs, report the tool error clearly.
4. If the user asks for an ordinary differential equation, consult `references/differential-equations.md` and use `solve_differential_equation`.
5. For ordinary differential equations, use `solve_differential_equation` to produce the solved result and supporting metadata.
6. For arithmetic, use the arithmetic tools to compute the final numeric result.
7. Use `references/formatting.md` as the formatting guidance for how to present math steps and final answers.
8. Every mathematical step in the explanation must be written in plain, readable math text, not raw LaTeX markup.
9. For example, write `dy/dx = y`, `1/y dy = dx`, `ln|y| = x + C`, and `y(x) = C1*exp(x)` instead of `\frac`, `\[...\]`, `\(...\)`, or `\boxed{...}` blocks.
10. After solving, call `format_math_response` with the original expression or equation plus the computed result.
11. Do not present the final result before `format_math_response` has been used.
12. In the user-facing reply, prefer `pretty_equation` and `final_answer` unless the user explicitly asks for raw LaTeX or metadata.
13. If you show intermediate derivation steps, format those steps in the same plain math style as `pretty_equation`.
