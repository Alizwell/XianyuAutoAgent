# Module: context_manager

**Responsibility:** Chat Context Management - SQLite-based chat history and state

## Entry Points

- context_manager.py → Context manager class

## Key Files

- context_manager.py → Message storage, context retrieval, bargain counting

## Constraints

- Uses SQLite for persistent storage
- Manages chat history per user/session
- Tracks bargain/negotiation rounds

## Scope Table

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | context_manager.py | SQLite operations, context management |
| Implementation | data/chat_history.db | SQLite database file |
| Consumer | XianyuAgent.py | Retrieves context for LLM prompts |
| Dependency | XianyuApis.py | Gets user info |
