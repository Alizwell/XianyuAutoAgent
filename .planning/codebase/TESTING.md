# Testing Patterns

**Analysis Date:** 2026-03-18

## Testing Framework Status

**Current State: No Testing Infrastructure**

This codebase currently has NO testing infrastructure in place:
- No test files exist (`find . -name "*test*.py"` returns empty)
- No test configuration files (pytest.ini, setup.cfg, tox.ini)
- No testing dependencies in `requirements.txt`
- No CI/CD configuration files

## Recommended Testing Setup

Based on codebase analysis, here is the recommended testing approach:

### Suggested Testing Stack

**Test Runner:** pytest
- Industry standard for Python testing
- Excellent async support via `pytest-asyncio`
- Rich plugin ecosystem

**Mocking:** pytest-mock (mocker fixture)
- Built on unittest.mock
- Simplified fixture-based approach

**Assertions:** pytest built-in assertions
- Rich introspection on failure

**Coverage:** pytest-cov
- Branch coverage support
- HTML report generation

**Async Testing:** pytest-asyncio
- Required for testing async/await code
- Native coroutine test support

### Proposed Test Configuration

**requirements-dev.txt:**
```
# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0
pytest-cov>=4.0.0

# Type checking
mypy>=1.0.0

# Linting
ruff>=0.1.0

# Testing utilities
freezegun>=1.0.0
responses>=0.23.0
```

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
    --tb=short
asyncio_mode = auto
```

### Suggested Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_xianyu_utils.py    # Utility function tests
│   ├── test_xianyu_apis.py     # API client tests (mocked)
│   └── test_context_manager.py # Database tests
├── integration/
│   ├── __init__.py
│   ├── test_websocket.py       # WebSocket connection tests
│   └── test_agent.py           # AI agent integration tests
└── e2e/
    ├── __init__.py
    └── test_full_flow.py       # End-to-end flow tests
```

### Key Testing Patterns by Module

#### 1. Utility Functions (`utils/xianyu_utils.py`)

**Test Approach:** Pure unit tests

**Key Functions to Test:**
- `trans_cookies()` - Cookie string parsing
- `generate_mid()` - Message ID generation
- `generate_uuid()` - UUID generation
- `generate_device_id()` - Device ID generation
- `generate_sign()` - HMAC signature generation
- `MessagePackDecoder` - Binary message decoding
- `decrypt()` - Message decryption

**Example Test Pattern:**
```python
def test_trans_cookies():
    """Test cookie string parsing"""
    cookie_str = "key1=value1; key2=value2"
    result = trans_cookies(cookie_str)
    assert result == {"key1": "value1", "key2": "value2"}

def test_generate_mid_format():
    """Test mid format"""
    mid = generate_mid()
    parts = mid.split()
    assert len(parts) == 2
    assert parts[1] == "0"
```

#### 2. API Client (`XianyuApis.py`)

**Test Approach:** Mocked HTTP requests

**Key Behaviors to Test:**
- `get_token()` - Token acquisition with retry logic
- `get_item_info()` - Item information fetching
- `hasLogin()` - Login status verification
- Cookie management and deduplication
- Error handling and retry logic

**Example Test Pattern:**
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def api_client():
    from XianyuApis import XianyuApis
    client = XianyuApis()
    return client

@patch('XianyuApis.requests.Session.post')
def test_get_token_success(mock_post, api_client):
    """Test successful token acquisition"""
    mock_response = Mock()
    mock_response.json.return_value = {
        'ret': ['SUCCESS::调用成功'],
        'data': {'accessToken': 'test_token'}
    }
    mock_post.return_value = mock_response

    result = api_client.get_token('device_123')

    assert 'data' in result
    assert result['data']['accessToken'] == 'test_token'
```

#### 3. Context Manager (`context_manager.py`)

**Test Approach:** SQLite in-memory database

**Key Behaviors to Test:**
- Database initialization and schema creation
- `add_message_by_chat()` - Message storage
- `get_context_by_chat()` - Context retrieval
- `increment_bargain_count_by_chat()` - Bargain counting
- `save_item_info()` / `get_item_info()` - Item data persistence

**Example Test Pattern:**
```python
import pytest
import sqlite3

@pytest.fixture
def context_manager(tmp_path):
    from context_manager import ChatContextManager
    db_path = tmp_path / "test.db"
    return ChatContextManager(db_path=str(db_path))

def test_add_and_get_message(context_manager):
    """Test message storage and retrieval"""
    # Add a message
    context_manager.add_message_by_chat(
        chat_id="chat_123",
        user_id="user_456",
        item_id="item_789",
        role="user",
        content="Hello!"
    )

    # Retrieve context
    context = context_manager.get_context_by_chat("chat_123")

    assert len(context) >= 1
    assert context[-1]["role"] == "user"
    assert context[-1]["content"] == "Hello!"

def test_bargain_count(context_manager):
    """Test bargain count tracking"""
    chat_id = "chat_test"

    # Initial count should be 0
    assert context_manager.get_bargain_count_by_chat(chat_id) == 0

    # Increment twice
    context_manager.increment_bargain_count_by_chat(chat_id)
    context_manager.increment_bargain_count_by_chat(chat_id)

    # Count should be 2
    assert context_manager.get_bargain_count_by_chat(chat_id) == 2
```

#### 4. AI Agent (`XianyuAgent.py`)

**Test Approach:** Mocked LLM responses

**Key Behaviors to Test:**
- Intent routing logic (`IntentRouter`)
- Agent selection and delegation
- Temperature calculation for price negotiations
- Message building and prompt formatting
- Safety filter application

**Example Test Pattern:**
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_client():
    """Mock OpenAI client"""
    return Mock()

@pytest.fixture
def router(mock_client):
    from XianyuAgent import IntentRouter, ClassifyAgent
    classify_agent = ClassifyAgent(mock_client, "system prompt", lambda x: x)
    return IntentRouter(classify_agent)

def test_router_tech_keywords(router):
    """Test routing based on tech keywords"""
    result = router.detect("这个有Type-C接口吗？", "item", "context")
    assert result == "tech"

def test_router_price_keywords(router):
    """Test routing based on price keywords"""
    result = router.detect("能便宜点吗？100元卖不卖？", "item", "context")
    assert result == "price"

def test_router_default(router):
    """Test default routing for unclear intent"""
    result = router.detect("你好", "item", "context")
    # Should fall back to classify_agent for unclear intent
    assert result is not None
```

#### 5. WebSocket Handler (`main.py`)

**Test Approach:** Async test patterns with mocked WebSocket

**Key Behaviors to Test:**
- WebSocket connection lifecycle
- Message parsing and routing
- Heartbeat mechanism
- Token refresh logic
- Manual mode toggling
- Context management integration

**Example Test Pattern:**
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

@pytest.fixture
def xianyu_live():
    from main import XianyuLive
    with patch.dict('os.environ', {'COOKIES_STR': 'test_cookie=123'}):
        return XianyuLive('test_cookie=123')

@pytest.mark.asyncio
async def test_heartbeat_sends_correct_format(xianyu_live):
    """Test heartbeat message format"""
    mock_ws = AsyncMock()

    await xianyu_live.send_heartbeat(mock_ws)

    # Verify send was called
    assert mock_ws.send.called

    # Parse the sent message
    sent_msg = mock_ws.send.call_args[0][0]
    import json
    data = json.loads(sent_msg)

    assert data['lwp'] == '/!'
    assert 'headers' in data
    assert 'mid' in data['headers']

def test_is_chat_message_valid(xianyu_live):
    """Test chat message detection"""
    valid_msg = {
        "1": {
            "10": {
                "reminderContent": "Hello!"
            }
        }
    }

    assert xianyu_live.is_chat_message(valid_msg) is True

def test_is_chat_message_invalid(xianyu_live):
    """Test invalid message detection"""
    invalid_msg = {
        "1": {
            "10": {}
        }
    }

    assert xianyu_live.is_chat_message(invalid_msg) is False
```

## Test Coverage Goals

Given the codebase structure, here are recommended coverage targets:

| Module | Target Coverage | Priority |
|--------|-----------------|----------|
| `utils/xianyu_utils.py` | 90% | High |
| `context_manager.py` | 85% | High |
| `XianyuApis.py` | 80% | High |
| `XianyuAgent.py` | 75% | Medium |
| `main.py` | 60% | Medium |

## Running Tests

**Command Examples:**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test module
pytest tests/unit/test_xianyu_utils.py

# Run with verbose output
pytest -v

# Run async tests
pytest --asyncio-mode=auto
```

## Continuous Integration

**Recommended GitHub Actions workflow:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: pytest --cov=. --cov-report=xml --cov-fail-under=80

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

*Testing analysis: 2026-03-18*
