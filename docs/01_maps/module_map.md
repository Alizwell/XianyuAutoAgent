# Module Map

```mermaid
flowchart TD
    A[main.py] --> B[XianyuAgent.py]
    B --> C[XianyuApis.py]
    B --> D[context_manager.py]
    B --> E[utils]
    B --> F[prompts]
```

## Entry Points

- main.py → WebSocket Client & Event Loop
- XianyuAgent.py → Agent Orchestration & Intent Routing
- XianyuApis.py → Xianyu API Client
- context_manager.py → Chat Context Management
- utils/ → Utility Functions
- prompts/ → LLM System Prompts
