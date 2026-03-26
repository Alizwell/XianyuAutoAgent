# Module: XianyuApis

**Responsibility:** Xianyu API Client - wrapper for Xianyu platform APIs

## Entry Points

- XianyuApis.py → API client class

## Key Files

- XianyuApis.py → Token management, product info fetching

## Constraints

- Must handle token refresh automatically
- Manages authentication with Xianyu platform
- Provides product information for chat context

## Scope Table

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | XianyuApis.py | API wrapper, token management |
| Consumer | XianyuAgent.py | Fetches product info for context |
| Consumer | context_manager.py | Uses for user data |
