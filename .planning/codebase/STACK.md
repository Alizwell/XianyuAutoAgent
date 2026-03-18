# Technology Stack

**Analysis Date:** 2026-03-18

## Languages

**Primary:**
- Python 3.10+ - Core application language

**Secondary:**
- SQL (SQLite) - Database queries via context_manager.py

## Runtime

**Environment:**
- Python 3.10 (Docker base image: python:3.10-alpine)

**Package Manager:**
- pip - Standard Python package manager
- Lockfile: Not present (requirements.txt specifies versions)

## Frameworks

**Core:**
- `openai` 1.65.5 - LLM client for API calls to OpenAI-compatible endpoints
- `websockets` 13.1 - WebSocket client for real-time messaging
- `requests` 2.32.3 - HTTP client for REST API calls

**Logging:**
- `loguru` 0.7.3 - Structured logging with rotation support

**Configuration:**
- `python-dotenv` 1.0.1 - Environment variable management from .env files

**Build/Dev:**
- Docker - Multi-stage builds with Alpine Linux

## Key Dependencies

**Critical:**
- `openai` - Core LLM integration, used in `XianyuAgent.py` for all AI responses
- `websockets` - Real-time message handling, used in `main.py` for Xianyu Goofish platform connection
- `requests` - HTTP API calls, used in `XianyuApis.py` for authentication and data retrieval

**Infrastructure:**
- `loguru` - Logging throughout all modules
- `python-dotenv` - Environment configuration at startup

## Configuration

**Environment:**
- Configuration via `.env` file (loaded by python-dotenv)
- Key environment variables defined in `.env.example`:
  - `API_KEY` - LLM API authentication
  - `COOKIES_STR` - Xianyu/Goofish authentication cookies
  - `MODEL_BASE_URL` - LLM API endpoint (default: https://dashscope.aliyuncs.com/compatible-mode/v1)
  - `MODEL_NAME` - Model identifier (default: qwen-max)
  - `TOGGLE_KEYWORDS` - Manual mode toggle keyword (default: 。)
  - `SIMULATE_HUMAN_TYPING` - Typing delay simulation (True/False)

**Build:**
- `Dockerfile` - Multi-stage Alpine-based container
- `docker-compose.yml` - Service orchestration with volume mounts
- `requirements.txt` - Python dependencies

## Platform Requirements

**Development:**
- Python 3.8+ (project uses 3.10)
- pip package manager
- SQLite (included with Python)

**Production:**
- Docker container runtime
- Network access to:
  - DashScope API (or alternative LLM provider)
  - Xianyu/Goofish WebSocket and HTTP endpoints
- Volume mounts for:
  - `./data` - SQLite database persistence
  - `./prompts` - Prompt customization files
  - `./.env` - Environment configuration

---

*Stack analysis: 2026-03-18*
