# External Integrations

**Analysis Date:** 2026-03-18

## APIs & External Services

**LLM Provider:**
- DashScope (Alibaba Cloud) - Primary LLM provider
  - SDK/Client: `openai` Python package (OpenAI-compatible API)
  - Endpoint: `https://dashscope.aliyuncs.com/compatible-mode/v1`
  - Auth: API key via `API_KEY` environment variable
  - Default Model: `qwen-max`

**Xianyu/Goofish Platform:**
- Goofish WebSocket API - Real-time messaging
  - Endpoint: `wss://wss-goofish.dingtalk.com/`
  - Protocol: Custom WebSocket with MessagePack encoding
  - Auth: Session cookies from browser

- Goofish HTTP API - Authentication and data retrieval
  - Token endpoint: `https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/`
  - Item info endpoint: `https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail/1.0/`
  - Login check: `https://passport.goofish.com/newlogin/hasLogin.do`
  - Auth: Cookie-based with HMAC-SHA1 signatures

## Data Storage

**Databases:**
- SQLite - Local relational database
  - Path: `data/chat_history.db` (configurable)
  - Connection: Python `sqlite3` module
  - Tables:
    - `messages` - Chat history
    - `chat_bargain_counts` - Bargaining session tracking
    - `items` - Cached product information

**File Storage:**
- Local filesystem only
- Data directory mounted as Docker volume (`./data`)

**Caching:**
- In-memory caching via Python dictionaries
- No external cache service (Redis/Memcached not used)

## Authentication & Identity

**Auth Provider:**
- Custom/Xianyu Native - No OAuth/JWT
- Implementation: Session cookie-based authentication
  - Cookies extracted from browser and stored in `COOKIES_STR` env var
  - Key cookies: `unb` (user ID), `_m_h5_tk` (token), `cookie2`, `XSRF-TOKEN`
  - Cookie refresh handled automatically on token expiration

**Security Model:**
- No user registration/login flow
- Session validity checked via `hasLogin.do` endpoint
- Automatic re-authentication with user prompt on cookie expiration

## Monitoring & Observability

**Error Tracking:**
- None - No Sentry/Rollbar integration
- Errors logged to console/file via `loguru`

**Logs:**
- File: Not configured (console output only by default)
- Format: Colored console output with timestamps
- Levels: DEBUG, INFO, WARNING, ERROR
- Library: `loguru`

## CI/CD & Deployment

**Hosting:**
- Docker container deployment
- Image: `shaxiu/xianyuautoagent:latest` (published to Docker Hub)

**CI Pipeline:**
- None detected - No GitHub Actions/GitLab CI configuration

## Environment Configuration

**Required env vars:**
- `API_KEY` - LLM API key (for DashScope or alternative provider)
- `COOKIES_STR` - Xianyu/Goofish session cookies (semicolon-separated)

**Optional env vars:**
- `MODEL_BASE_URL` - LLM API endpoint (default: https://dashscope.aliyuncs.com/compatible-mode/v1)
- `MODEL_NAME` - Model identifier (default: qwen-max)
- `TOGGLE_KEYWORDS` - Keyword to toggle manual mode (default: 。)
- `SIMULATE_HUMAN_TYPING` - Enable typing delay simulation (default: False)
- `LOG_LEVEL` - Logging level (default: DEBUG)
- `HEARTBEAT_INTERVAL` - WebSocket heartbeat interval in seconds (default: 15)
- `HEARTBEAT_TIMEOUT` - Heartbeat timeout in seconds (default: 5)
- `TOKEN_REFRESH_INTERVAL` - Token refresh interval in seconds (default: 3600)
- `TOKEN_RETRY_INTERVAL` - Token retry interval in seconds (default: 300)
- `MANUAL_MODE_TIMEOUT` - Manual mode timeout in seconds (default: 3600)
- `MESSAGE_EXPIRE_TIME` - Message expiration time in milliseconds (default: 300000)

**Secrets location:**
- `.env` file (gitignored, mounted as Docker volume)

## Webhooks & Callbacks

**Incoming:**
- WebSocket message handler in `main.py` - Processes real-time messages from Goofish

**Outgoing:**
- HTTP POST to Goofish message API for sending replies
- No external webhooks for notifications (no Slack/Discord/Teams integration)

---

*Integration audit: 2026-03-18*
