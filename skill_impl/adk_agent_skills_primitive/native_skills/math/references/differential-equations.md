---
allowed-tools: solve_differential_equation
---

# Differential Equations

Use the differential-equation tool when the user asks to solve a supported first-order ODE rather than perform plain arithmetic.

## Supported Forms

- `dy/dx = x*y`
- `y' - y = 0`
- `y'(x) = x + y`
- `dy/dx = 2*x + 3`

## Workflow

1. Rewrite the user problem into a supported equation form.
2. Call `solve_differential_equation`.
3. Follow the formatting rules from the loaded math skill instructions.
4. Call `format_math_response` with the original equation and the full solver result dictionary.
5. Prefer the returned `pretty_equation` or `final_answer` so the final response is displayed in symbolic math form rather than flattened calculator text.
6. Return the formatted solution clearly.

## Limits

- This tool is intentionally limited to simple first-order forms.
- Supported families:
  - `dy/dx = a*x + b`
  - `dy/dx = (a*x + b)*y`
  - `dy/dx +/- c*y = 0`
- If the equation is outside the supported scope, say so directly.
