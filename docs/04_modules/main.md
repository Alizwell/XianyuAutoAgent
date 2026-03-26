# Module: main

**Responsibility:** WebSocket Client & Event Loop - main entry point for XianyuAutoAgent

## Entry Points

- main.py → WebSocket connection handler and event loop

## Key Files

- main.py → WebSocket client, message processing, heartbeat maintenance

## Constraints

- Must maintain persistent WebSocket connection to Xianyu API
- Handles automatic reconnection on disconnect
- Manages heartbeat to keep connection alive

## Scope Table

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | main.py | WebSocket connection, event loop, heartbeat |
| Consumer | XianyuAgent.py | Processes messages routed from main.py |
