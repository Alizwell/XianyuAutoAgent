# Codebase Structure

**Analysis Date:** 2026-03-18

## Directory Layout

```
/Users/xueyong/Ownspace/xianyu-hotel-agent/
├── main.py                    # Application entry point
├── XianyuAgent.py           # Multi-agent reply system
├── XianyuApis.py            # Xianyu platform API client
├── context_manager.py       # Conversation persistence
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container build definition
├── docker-compose.yml       # Docker compose configuration
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
│
├── utils/                   # Utility functions
│   ├── __init__.py
│   └── xianyu_utils.py    # Cookie parsing, ID generation, crypto
│
├── prompts/                 # LLM prompt templates
│   ├── classify_prompt_example.txt
│   ├── price_prompt_example.txt
│   ├── tech_prompt_example.txt
│   └── default_prompt_example.txt
│
├── docs/                    # Additional documentation
│   ├── login-scheme.md
│   └── message-receiving-scheme.md
│
├── images/                  # Static images (screenshots, QR codes)
│   ├── demo*.png
│   ├── log.png
│   ├── wx_group*.png
│   ├── wechat_pay.jpg
│   └── alipay.jpg
│
└── data/                    # Runtime data (created at runtime)
    └── chat_history.db      # SQLite conversation database
```

## Directory Purposes

**Root Level (Application Core):**
- Purpose: Main application logic and entry points
- Contains: Main modules, configuration templates, documentation
- Key files: `main.py`, `XianyuAgent.py`, `XianyuApis.py`, `context_manager.py`

**`utils/`:**
- Purpose: Reusable utility functions
- Contains: Helper functions for cookie parsing, ID generation, cryptography, MessagePack decoding
- Key files: `xianyu_utils.py` (335 lines, most comprehensive utility module)

**`prompts/`:**
- Purpose: LLM system prompt templates
- Contains: Example prompt files for each agent type
- Files: `*_prompt_example.txt` (should be copied to `*_prompt.txt` for customization)
- Pattern: Examples serve as defaults, user creates non-example versions for customization

**`docs/`:**
- Purpose: Technical documentation
- Contains: Protocol documentation, login schemes, message receiving schemes
- Key files: `login-scheme.md`, `message-receiving-scheme.md`

**`images/`:**
- Purpose: Static assets
- Contains: Demo screenshots, QR codes for WeChat groups, payment QR codes
- Note: Large binary files, not tracked for code analysis

**`data/` (Runtime):**
- Purpose: Persistent storage
- Contains: SQLite database file
- Generated: Created at runtime by `context_manager.py`
- Git: Directory listed in `.gitignore`

## Key File Locations

**Entry Points:**
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/main.py` (lines 751-779): Application entry, environment setup, bot initialization
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/main.py` (XianyuLive.main, lines 609-705): Main connection loop

**Configuration:**
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/.env.example`: Environment variable template
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/Dockerfile`: Container build configuration
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/requirements.txt`: Python dependencies

**Core Logic:**
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/XianyuAgent.py` (296 lines): Multi-agent routing and response generation
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/XianyuApis.py` (302 lines): Xianyu platform API client
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/context_manager.py` (308 lines): Conversation persistence with SQLite
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/main.py` (779 lines): WebSocket connection management, message handling

**Utilities:**
- `/Users/xueyong/Ownspace/xianyu-hotel-agent/utils/xianyu_utils.py` (335 lines): Cryptographic utilities, ID generation, MessagePack decoder

## Naming Conventions

**Files:**
- Main modules: PascalCase with descriptive names (e.g., `XianyuAgent.py`, `XianyuApis.py`)
- Utilities: lowercase with underscore (e.g., `xianyu_utils.py`, `context_manager.py`)
- Example prompts: `{name}_prompt_example.txt` pattern
- Configuration: `.env.example`, `requirements.txt`

**Directories:**
- Lowercase, descriptive: `utils/`, `prompts/`, `docs/`, `images/`
- Runtime data: `data/` (gitignored)

**Classes:**
- PascalCase descriptive names:
  - `XianyuLive`: Main WebSocket handler
  - `XianyuReplyBot`: Agent coordinator
  - `IntentRouter`: Message classification
  - `BaseAgent`, `PriceAgent`, `TechAgent`, `ClassifyAgent`, `DefaultAgent`: Agent hierarchy
  - `ChatContextManager`: Database operations
  - `XianyuApis`: External API client
  - `MessagePackDecoder`: Binary data decoder

**Functions/Methods:**
- snake_case descriptive verbs:
  - `generate_mid()`, `generate_uuid()`, `generate_device_id()`, `generate_sign()`: ID/crypto utilities
  - `trans_cookies()`, `decrypt()`: Data transformation
  - `get_token()`, `get_item_info()`, `hasLogin()`: API operations
  - `send_msg()`, `handle_message()`, `init()`: Connection operations
  - `generate_reply()`, `detect()`, `_build_messages()`: Agent operations
  - `add_message_by_chat()`, `get_context_by_chat()`, `save_item_info()`: Persistence operations

**Variables:**
- snake_case descriptive nouns:
  - `cookies_str`, `device_id`, `chat_id`, `item_id`: Identifiers
  - `heartbeat_interval`, `token_refresh_interval`: Configuration
  - `manual_mode_conversations`, `connection_restart_flag`: State tracking

**Constants (implied by context):**
- API endpoints: `wss://wss-goofish.dingtalk.com/`
- Default values: `HEARTBEAT_INTERVAL = 15`, `TOKEN_REFRESH_INTERVAL = 3600`

## Where to Add New Code

**New Agent Type:**
- Primary code: `/Users/xueyong/Ownspace/xianyu-hotel-agent/XianyuAgent.py` (add new class inheriting from BaseAgent)
- Prompt: `/Users/xueyong/Ownspace/xianyu-hotel-agent/prompts/{name}_prompt_example.txt`
- Routing: Update `IntentRouter.rules` and `XianyuReplyBot._init_agents()` in XianyuAgent.py

**New WebSocket Handler:**
- Implementation: `/Users/xueyong/Ownspace/xianyu-hotel-agent/main.py` (XianyuLive class)
- Pattern: Add detection method (e.g., `is_new_message_type()`) and handler logic in `handle_message()`

**New Database Entity:**
- Schema: `/Users/xueyong/Ownspace/xianyu-hotel-agent/context_manager.py` (ChatContextManager._init_db())
- Operations: Add CRUD methods to ChatContextManager class

**New Utility Function:**
- Location: `/Users/xueyong/Ownspace/xianyu-hotel-agent/utils/xianyu_utils.py`
- Pattern: Standalone function with docstring, imported by other modules as needed

## Special Directories

**`data/`:**
- Purpose: Runtime SQLite database storage
- Generated: Created at runtime by ChatContextManager if not exists
- Committed: No (listed in `.gitignore`)
- Contents: `chat_history.db` with messages, items, chat_bargain_counts tables

**`prompts/`:**
- Purpose: LLM system prompt templates
- Generated: No (static files)
- Committed: Yes
- Pattern: `*_example.txt` files serve as defaults; runtime loads `*.txt` (non-example) if exists, otherwise falls back to example

**`images/`:**
- Purpose: Documentation assets, QR codes, screenshots
- Generated: No (static assets)
- Committed: Yes (binary files)
- Note: Large images may increase repo size; consider external hosting for many assets

**`utils/`:**
- Purpose: Reusable utility functions
- Generated: No (source code)
- Committed: Yes
- Note: Contains cryptography, encoding/decoding, ID generation - security-sensitive code

---

*Structure analysis: 2026-03-18*
