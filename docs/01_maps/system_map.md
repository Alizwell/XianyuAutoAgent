# System Map

## Architecture

```mermaid
flowchart LR
    A[Xianyu WebSocket API] --> B[WebSocket Client]
    B --> C[Intent Router]
    C --> D[Agent]
    D --> E[LLM OpenAI API]
```

## Layers

- Xianyu WebSocket API → External service connection
- WebSocket Client → Maintains live connection
- Intent Router → Classifies incoming messages
- Agent → Orchestrates responses
- LLM → Generates replies
