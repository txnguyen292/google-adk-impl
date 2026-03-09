# ADK Skill Impl

Standalone extraction of the ADK native skills implementation from the larger
`langgraph_vs_adk` repo.

## Included

- `skill_impl/adk_agent_skills_primitive/`
- shared `non_skill_impl/adk_agent/skills/`
- shared `core/`
- minimal `adk_agent` support code under `non_skill_impl/adk_agent/`
- focused tests for the primitive ADK skill path

## Run

```bash
uv sync --extra dev
python main.py
```

Or run the local orchestrator directly:

```bash
python -m adk_agent_skills_primitive.agents.orchestrator.main "2+2"
```
