# Development Guide

## Setup

### Install dependencies
```bash
pip install -r requirements.txt
```

### Environment Variables

Required env vars:
- `API_KEY` → OpenAI API key
- `COOKIES_STR` → Xianyu account cookies
- `MODEL_BASE_URL` → LLM API base URL
- `MODEL_NAME` → Model name (e.g., gpt-4o)
- `TOGGLE_KEYWORDS` → Keywords to toggle auto-reply
- `SIMULATE_HUMAN_TYPING` → Enable human-like typing delay
- `HEARTBEAT_INTERVAL` → WebSocket heartbeat interval
- `HEARTBEAT_TIMEOUT` → Heartbeat timeout
- `TOKEN_REFRESH_INTERVAL` → Token refresh interval
- `TOKEN_RETRY_INTERVAL` → Token retry interval
- `MANUAL_MODE_TIMEOUT` → Manual mode timeout
- `MESSAGE_EXPIRE_TIME` → Message expiration time
- `LOG_LEVEL` → Logging level

## Running the Server

```bash
python main.py
```
