# Coding Conventions

**Analysis Date:** 2026-03-18

## Overview

This is a Python-based AI customer service bot for Xianyu (闲鱼) platform. The codebase follows a traditional Python scripting style with async/await patterns for WebSocket communication.

## Language Standards

**Python Version:** 3.10+ (as specified in Dockerfile)

**Key Language Features Used:**
- Async/await for WebSocket and API communication
- Type hints (basic usage: `List[Dict]`, `str`, `int`)
- Class-based OOP with inheritance
- f-strings for string formatting
- Comprehensions and generator expressions

## Naming Conventions

**Files:**
- PascalCase for main module files: `XianyuAgent.py`, `XianyuApis.py`
- snake_case for utility modules: `context_manager.py`, `xianyu_utils.py`
- Main entry point: `main.py`

**Classes:**
- PascalCase: `XianyuReplyBot`, `BaseAgent`, `IntentRouter`, `ChatContextManager`, `MessagePackDecoder`
- Private/protected methods use single underscore prefix: `_init_agents`, `_build_messages`, `_call_llm`

**Functions/Methods:**
- snake_case: `generate_reply`, `build_item_description`, `handle_message`
- Private methods with underscore prefix: `_calc_temperature`, `_extract_bargain_count`

**Variables:**
- snake_case: `user_msg`, `item_desc`, `context`, `chat_id`
- Constants use uppercase with underscores: `blocked_phrases`, `self.rules`
- Type hints for function parameters and returns (basic usage)

## Code Style

**Formatting:**
- No explicit formatter configuration found (no .black, .isort, or similar)
- Standard 4-space indentation
- Line continuation with implicit line joining inside parentheses/brackets

**Import Organization:**
```python
# 1. Standard library imports
import re
import json
import time
from typing import List, Dict

# 2. Third-party library imports
from openai import OpenAI
from loguru import logger

# 3. Local module imports
from utils.xianyu_utils import generate_mid
```

**Blank Lines:**
- Two blank lines between top-level definitions (classes/functions)
- One blank line between methods in a class
- No strict enforcement observed

## Error Handling

**Patterns:**
- Try/except blocks with specific exception handling where needed
- Generic `except Exception` used frequently (broad exception catching)
- Error logging via `logger.error()` before returning default values

**Example:**
```python
# From context_manager.py
try:
    cursor.execute(...)
    result = cursor.fetchone()
    if result:
        return json.loads(result[0])
    return None
except Exception as e:
    logger.error(f"获取商品信息时出错: {e}")
    return None
finally:
    conn.close()
```

**Silent Failures:** Some methods silently handle errors with empty returns or default values.

## Logging

**Framework:** `loguru` (structured logging)

**Configuration:**
```python
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    level=log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
```

**Usage Patterns:**
- `logger.info()` - General information
- `logger.debug()` - Debug details
- `logger.warning()` - Warning conditions
- `logger.error()` - Error conditions
- `logger.success()` - Success notifications

## Type Hints

**Usage:** Basic type hints present but not comprehensive

**Examples:**
```python
def generate(self, user_msg: str, item_desc: str, context: str, bargain_count: int = 0) -> str:

def _build_messages(self, user_msg: str, item_desc: str, context: str) -> List[Dict]:

def _call_llm(self, messages: List[Dict], temperature: float = 0.4) -> str:
```

**Gaps:** Many functions lack type hints, especially utility functions and methods with complex return types.

## Comments and Documentation

**Docstrings:**
- Google-style docstrings used in some modules (e.g., `context_manager.py`)
- Most functions lack docstrings
- Some have minimal Chinese comments explaining purpose

**Example:**
```python
def _extract_bargain_count(self, context: List[Dict]) -> int:
    """
    从上下文中提取议价次数信息

    Args:
        context: 对话历史

    Returns:
        int: 议价次数，如果没有找到则返回0
    """
```

**Inline Comments:**
- Chinese comments used throughout the codebase
- Explain business logic and complex operations
- Some debug comments left in code (commented out logger.debug calls)

## Module Organization

**Structure:**
```
project/
├── main.py              # Entry point
├── XianyuAgent.py       # AI agent implementation
├── XianyuApis.py        # API client
├── context_manager.py   # Database/Context management
├── requirements.txt     # Dependencies
├── utils/               # Utility modules
│   ├── __init__.py
│   └── xianyu_utils.py  # Helper functions
└── prompts/             # Prompt templates
    ├── classify_prompt_example.txt
    ├── price_prompt_example.txt
    ├── tech_prompt_example.txt
    └── default_prompt_example.txt
```

## Configuration Management

**Environment Variables:**
- Loaded via `python-dotenv` from `.env` file
- `.env.example` provides template
- Required variables checked interactively at startup

**Key Environment Variables:**
- `API_KEY` - LLM API key
- `COOKIES_STR` - Authentication cookies
- `MODEL_BASE_URL` - LLM API base URL
- `MODEL_NAME` - Model name (default: qwen-max)
- `TOGGLE_KEYWORDS` - Keywords to toggle manual mode
- `SIMULATE_HUMAN_TYPING` - Enable human-like typing delay
- `LOG_LEVEL` - Logging verbosity

## Patterns Summary

**Strengths:**
- Async/await used appropriately for I/O operations
- Class-based design with clear inheritance
- Structured logging with loguru
- Database abstraction with SQLite
- Environment-based configuration

**Areas for Improvement:**
- No type checking enforcement (mypy)
- No code formatting standard (black/ruff)
- No linting configuration visible
- Inconsistent docstring coverage
- Broad exception catching in many places
- No automated testing visible

---

*Convention analysis: 2026-03-18*
