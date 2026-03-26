# Module: XianyuAgent

**Responsibility:** Agent Orchestration & Intent Routing - AI reply bot with multi-agent system

## Entry Points

- XianyuAgent.py → Main agent class and intent router

## Key Files

- XianyuAgent.py → Intent classification, agent selection, response generation

## Constraints

- Must classify intents accurately before routing
- Supports multiple agent types (default, price, tech)
- Integrates with OpenAI API for response generation

## Scope Table

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | XianyuAgent.py | Intent routing, agent orchestration, LLM integration |
| Consumer | main.py | Calls agent to process messages |
| Dependency | XianyuApis.py | Product info for context |
| Dependency | context_manager.py | Chat history for context |
