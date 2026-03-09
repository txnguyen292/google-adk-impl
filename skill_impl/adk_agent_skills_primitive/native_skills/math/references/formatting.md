# Math Formatting

Use this reference after computation is complete and you need to present the answer clearly.

Guidelines:

1. Call `format_math_response` with the original expression or equation and the computed result.
2. Use `pretty_equation` and `final_answer` for the user-facing result unless the user explicitly asks for raw LaTeX or metadata.
3. Format every intermediate math step in plain readable math text as well.
4. Write steps like `dy/dx = y`, `1/y dy = dx`, `ln|y| = x + C`, and `y(x) = C1*exp(x)` instead of raw LaTeX markup such as `\frac`, `\[...\]`, `\(...\)`, or `\boxed`.
5. Do not expose `family`, `families`, `latex_equation`, or `latex_problem` unless the user asks for them.
6. Do not replace the formatted final result with your own LaTeX or alternate wording.
7. Keep explanation text readable in plain text; avoid inventing raw LaTeX blocks when a formatted result is already available.
