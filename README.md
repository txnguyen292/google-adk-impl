# ADK Skill Impl

This repo currently contains two main execution styles:

- `skill_impl/`
  ADK native-skill implementation. The orchestrator discovers and loads skills
  before using runtime tools.
- `non_skill_impl/`
  Direct ADK implementations without native-skill loading.
  This includes:
  - a `multi_agent` layout with an orchestrator plus math and web-search agents
  - a `unified_agent` that exposes math and web-search tools directly in one agent

## Requirements

- Python 3.13
- `uv`
- an LLM API key usable through LiteLLM
- a Brave Search API key for any web-search-capable agent

## Installation

From the repo root:

```bash
uv sync --extra dev
source .venv/bin/activate
cp .env.temp .env
```

Then open `.env` and fill in the required values, especially:

- `OPENAI_API_KEY` or the provider key required by your `LITELLM_MODEL`
- `BRAVE_API_KEY` if you want web-search-capable agents to work

If you already have the checked-in virtualenv, you can use it directly:

```bash
.venv/bin/python --version
```

## Environment Variables

The repo loads `.env` automatically for the local CLIs.

Start from the template:

```bash
cp .env.temp .env
```

Minimum useful setup:

```env
OPENAI_API_KEY=...
BRAVE_API_KEY=...
LITELLM_MODEL=openai/gpt-4o-mini
```

Useful optional variables:

```env
ADK_MAX_LLM_CALLS=0
LITELLM_PROVIDER=openai
LITELLM_TEMPERATURE=0.2
LITELLM_DROP_PARAMS=false
LITELLM_SSL_VERIFY=false
BRAVE_SEARCH_COUNTRY=us
BRAVE_SEARCH_LANG=en
BRAVE_VERIFY=true
BRAVE_ALLOW_INSECURE_FALLBACK=false
ADK_DEBUG=false
ADK_TRACE=false
```

Notes:

- `OPENAI_API_KEY` is an example. Use whatever provider credentials your
  `LITELLM_MODEL` requires.
- `BRAVE_API_KEY` is required for web search in:
  - `non_skill_impl/adk_agent/agents/multi_agent/web_search_agent`
  - `non_skill_impl/adk_agent/agents/multi_agent/orchestrator`
  - `non_skill_impl/adk_agent/agents/unified_agent`
- `ADK_MAX_LLM_CALLS` now defaults to `0` in this repo.
- Local agent CLIs print execution steps by default.
  Set `ADK_TRACE=false` if you want quieter output.

## Repository Layout

- `core/`
  Shared config, prompt loading, output rendering, observability, and guard logic.
- `non_skill_impl/adk_agent/skills/`
  Shared prompt and tool definitions used by the ADK implementations.
- `non_skill_impl/adk_agent/agents/multi_agent/`
  Orchestrator plus dedicated math and web-search agents.
- `non_skill_impl/adk_agent/agents/unified_agent/`
  Single ADK agent with both web-search and math tools.
- `skill_impl/adk_agent_skills_primitive/`
  Native-skill-based ADK implementation.
- `tests/`
  Focused coverage for math tools, web search, runner behavior, and agent wiring.

## Run the Skill-Based Agent

Local primitive orchestrator:

```bash
python -m adk_agent_skills_primitive.agents.orchestrator.main "What is 12*19?"
```

Run the primitive agents in ADK Web UI:

```bash
.venv/bin/adk web skill_impl/adk_agent_skills_primitive/agents
```

## Run the Non-Skill Multi-Agent Implementation

Run the orchestrator:

```bash
python -m adk_agent.agents.multi_agent.orchestrator.main "Find the latest CPI print and multiply it by 2"
```

Run the math-only agent:

```bash
python -m adk_agent.agents.multi_agent.math_agent.main "Solve dy/dx = x*y"
```

Run the web-search-only agent:

```bash
python -m adk_agent.agents.multi_agent.web_search_agent.main "Latest OpenAI news"
```

Run the non-skill multi-agent bundle in ADK Web UI:

```bash
.venv/bin/adk web non_skill_impl/adk_agent/agents/multi_agent
```

## Run the Unified Agent

The unified agent exposes both math and web-search tools directly in one ADK
agent instead of delegating through sub-agents.

```bash
python -m adk_agent.agents.unified_agent.main "What is 25*64 and what is the latest inflation print?"
```

Run the unified agent in ADK Web UI:

```bash
.venv/bin/adk web non_skill_impl/adk_agent/agents/unified_agent
```

`adk web` commands used in this repo:

- `skill_impl/adk_agent_skills_primitive/agents`
- `non_skill_impl/adk_agent/agents/multi_agent`
- `non_skill_impl/adk_agent/agents/unified_agent`

## Running Tests

Lint:

```bash
.venv/bin/ruff check .
```

Tests:

```bash
.venv/bin/pytest -q
```

## Notes on Behavior

- The multi-agent orchestrator is instructed to delegate whenever a relevant
  sub-agent exists instead of solving tasks directly.
- The math agent supports:
  - arithmetic
  - supported first-order differential equations
  - formatted final math responses via `format_math_response`
- The web-search implementation uses Brave Search via the
  `DuckDuckGoSearchClient` compatibility alias.
