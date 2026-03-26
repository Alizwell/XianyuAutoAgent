# Feature Map

## WebSocket Live Connection
→ main.py → Maintains persistent WebSocket to Xianyu

## Intent Classification
→ XianyuAgent.py → Routes messages by intent type

## Multi-Agent Reply System
→ XianyuAgent.py → Orchestrates response generation

## Context Management
→ context_manager.py → Maintains chat state

## Token Refresh
→ XianyuApis.py → Handles auth refresh

## Manual Mode Control
→ main.py → Toggles automatic/manual reply
