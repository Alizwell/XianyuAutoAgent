# Architecture

**Analysis Date:** 2026-03-18

## Pattern Overview

**Overall:** Multi-Agent Event-Driven Architecture

**Key Characteristics:**
- Multi-agent routing with intent-based message classification
- Event-driven WebSocket message handling
- SQLite-backed persistent conversation context
- Modular agent design with specialized roles
- Real-time bi-directional communication with external API

## Layers

**Entry/Connection Layer:**
- Purpose: WebSocket connection management, heartbeat maintenance, token refresh
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/main.py` (XianyuLive class)
- Contains: WebSocket client, heartbeat loop, token refresh loop, message dispatching
- Depends on: XianyuApis (authentication), XianyuReplyBot (reply generation)
- Used by: Main entry point

**API Integration Layer:**
- Purpose: External API communication with Xianyu platform
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/XianyuApis.py`
- Contains: HTTP session management, token acquisition, item info retrieval, cookie management
- Depends on: utils/xianyu_utils (signature generation)
- Used by: XianyuLive (main connection handler)

**Agent Logic Layer:**
- Purpose: Intent routing and specialized response generation
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/XianyuAgent.py`
- Contains: IntentRouter, XianyuReplyBot, BaseAgent, PriceAgent, TechAgent, ClassifyAgent, DefaultAgent
- Depends on: OpenAI client (LLM provider)
- Used by: XianyuLive (message handler)

**Persistence Layer:**
- Purpose: Conversation context and state management
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/context_manager.py`
- Contains: ChatContextManager class with SQLite operations, message history, bargain count tracking, item info storage
- Depends on: sqlite3, datetime
- Used by: XianyuLive, XianyuReplyBot

**Utility Layer:**
- Purpose: Helper functions and cryptographic operations
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/utils/xianyu_utils.py`
- Contains: Cookie parsing, ID generation (mid, uuid, device_id), signature generation, MessagePack decoder, decryption
- Depends on: hashlib, base64, struct, json, time
- Used by: XianyuApis, XianyuLive

## Data Flow

**Incoming Message Flow:**

1. WebSocket receives encrypted message via `wss://wss-goofish.dingtalk.com/`
2. `XianyuLive.main()` receives raw WebSocket message
3. `XianyuLive.handle_message()` decrypts MessagePack data using `utils/xianyu_utils.decrypt()`
4. Message type detection (chat message, typing status, system message, sync package)
5. For chat messages: extract user_id, item_id, chat_id, message content
6. Check manual mode status (human takeover)
7. Fetch item description from XianyuApis or context_manager cache
8. Fetch conversation context from ChatContextManager
9. Route to XianyuReplyBot.generate_reply() for intent classification and response generation
10. Send reply via WebSocket using `XianyuLive.send_msg()`
11. Store both user message and bot reply in ChatContextManager

**Token Refresh Flow:**

1. `XianyuLive.token_refresh_loop()` runs as background async task
2. Checks if token refresh interval exceeded (default 3600 seconds)
3. Calls `XianyuApis.get_token()` to fetch new access token
4. On success: updates `current_token`, sets `connection_restart_flag = True`
5. Triggers WebSocket reconnection with new token

## Key Abstractions

**IntentRouter:**
- Purpose: Classify user messages and route to appropriate agent
- Location: `XianyuAgent.py` (IntentRouter class)
- Pattern: Rule-based classification with keyword matching, regex patterns, and LLM fallback
- Rules: tech (technical keywords first), price (bargaining keywords), default (LLM classify agent)

**BaseAgent:**
- Purpose: Abstract base for all response-generating agents
- Location: `XianyuAgent.py` (BaseAgent class)
- Pattern: Template method pattern with _build_messages(), _call_llm(), safety_filter()
- Subclasses: PriceAgent, TechAgent, ClassifyAgent, DefaultAgent

**ChatContextManager:**
- Purpose: Persistent storage for conversation state
- Location: `context_manager.py`
- Pattern: Repository pattern with SQLite backend
- Tables: messages (chat history), items (product info), chat_bargain_counts (negotiation tracking)

**XianyuApis:**
- Purpose: External API client for Xianyu platform
- Location: `XianyuApis.py`
- Pattern: Session-based HTTP client with automatic cookie management, request signing
- Methods: hasLogin (auth check), get_token (token acquisition), get_item_info (product details)

## Entry Points

**Application Entry:**
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/main.py` (bottom of file)
- Triggers: `if __name__ == '__main__':`
- Responsibilities: Load environment variables, configure logging, check environment, initialize XianyuReplyBot and XianyuLive, start asyncio event loop

**Main Connection Loop:**
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/main.py` (XianyuLive.main() method)
- Triggers: Called by application entry
- Responsibilities: Establish WebSocket connection, initialize protocol, start heartbeat and token refresh tasks, process incoming messages, handle reconnections

**Message Handler:**
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/main.py` (XianyuLive.handle_message() method)
- Triggers: Called when WebSocket receives a message
- Responsibilities: Decrypt message, detect message type, handle manual mode, fetch item info, generate reply, send response, persist conversation

## Error Handling

**Strategy:** Defensive programming with retry logic and graceful degradation

**Patterns:**
- Retry with exponential backoff: API calls in `XianyuApis` (get_token, get_item_info) retry up to 2-3 times with 0.5s delays
- Cookie refresh on auth failure: When `get_token` fails due to expired cookies, prompts user for new cookies and exits if not provided
- Connection restart: On heartbeat timeout or token refresh, sets `connection_restart_flag` to trigger clean reconnection
- Exception isolation: Individual message handling failures don't crash main loop

**Error Recovery:**
- WebSocket connection closed: Logs warning, cleans up tasks, waits 5s (or immediate for intentional restart), loops to reconnect
- Token refresh failure: Logs error, waits configured retry interval (default 5 minutes), continues checking
- API rate limiting (RGV587_ERROR): Logs critical error, prompts user for cookie refresh via interactive input

## Cross-Cutting Concerns

**Logging:**
- Framework: loguru
- Configuration: In main entry, removes default handler, adds stderr handler with colored format including timestamp, level, module, function, line
- Level: Configurable via LOG_LEVEL environment variable (default DEBUG)
- Patterns: Debug for internal operations, Info for business events, Warning for recoverable issues, Error for failures, Critical for blocking issues

**Configuration:**
- Source: Environment variables via `.env` file (python-dotenv)
- Key configs: API_KEY, COOKIES_STR, MODEL_BASE_URL, MODEL_NAME, HEARTBEAT_INTERVAL, TOKEN_REFRESH_INTERVAL, TOGGLE_KEYWORDS, SIMULATE_HUMAN_TYPING
- Defaults: Provided in `.env.example`, loaded as fallback

**Security:**
- Cookie management: Session cookies stored in memory, written back to `.env` on refresh
- Sensitive data: API keys and cookies stored in `.env` (gitignored), never logged
- Input validation: Safety filter in `XianyuReplyBot` blocks platform-prohibited keywords (微信, QQ, 支付宝, etc.)

---

*Architecture analysis: 2026-03-18*
