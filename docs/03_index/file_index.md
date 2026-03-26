# File Index

## Root
- `.dockerignore` → Docker build ignore rules
- `.env.example` → Environment variable template (API_KEY, COOKIES_STR)
- `.gitignore` → Git ignore rules (.env, *.db, __pycache__)
- `Dockerfile` → Multi-stage Docker build (Python 3.10 Alpine)
- `LICENSE` → GNU GPL v3 license
- `README.md` → Project documentation
- `context_manager.py` → SQLite chat context manager
- `docker-compose.yml` → Docker Compose service config
- `main.py` → Main entry (WebSocket connection, message handling)
- `requirements.txt` → Python dependencies
- `XianyuAgent.py` → AI reply bot (intent routing, multi-agent system)
- `XianyuApis.py` → Xianyu API wrapper (token, product info)

## data/
- `chat_history.db` → SQLite database (chat history)

## prompts/
- `classify_prompt_example.txt` → Intent classification prompt template
- `default_prompt_example.txt` → Default reply prompt template
- `price_prompt_example.txt` → Price negotiation prompt template
- `tech_prompt_example.txt` → Technical expert prompt template

## utils/
- `__init__.py` → Package init
- `xianyu_utils.py` → Xianyu utilities (cookie parsing, signature, MessagePack decode)
