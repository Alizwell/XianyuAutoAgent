# Module: utils

**Responsibility:** Utility Functions - Xianyu-specific helpers

## Entry Points

- utils/xianyu_utils.py → Utility functions
- utils/__init__.py → Package init

## Key Files

- utils/xianyu_utils.py → Cookie parsing, signature generation, MessagePack decode
- utils/__init__.py → Package initialization

## Constraints

- Handles Xianyu-specific encoding/decoding
- Manages signature generation for API authentication
- Provides cookie parsing utilities

## Scope Table

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | utils/xianyu_utils.py | Cookie parser, signer, MessagePack decoder |
| Consumer | XianyuApis.py | Uses for API authentication |
| Consumer | main.py | Cookie parsing via trans_cookies |
