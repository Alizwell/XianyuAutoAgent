# XianyuAutoAgent - Runbook

<!-- metadata
generated: 2026-03-25
last_synced: 2026-03-25
-->

Agent-optimized knowledge base for XianyuAutoAgent project.

---

## Quick Links

### Getting Started
- [Big Picture](./00_overview/big_picture.md) - What the system does
- [Tech Stack](./00_overview/tech_stack.md) - Dependencies and tools

### Navigation

**Maps** - Find files and understand structure
- [System Map](./01_maps/system_map.md) - Core layers and integrations
- [Feature Map](./01_maps/feature_map.md) - Features and entry points
- [Module Map](./01_maps/module_map.md) - Key modules

**Index** - File reference
- [File Index](./03_index/file_index.md) - Path to meaning

**Modules** - Deep dive
- [main](./04_modules/main.md) - WebSocket Client & Event Loop
- [XianyuAgent](./04_modules/xianyu-agent.md) - Agent Orchestration & Intent Routing
- [XianyuApis](./04_modules/xianyu-apis.md) - Xianyu API Client
- [context_manager](./04_modules/context-manager.md) - Chat Context Management
- [utils](./04_modules/utils.md) - Utility Functions
- [prompts](./04_modules/prompts.md) - LLM System Prompts

### How-To

**Guides**
- [Development](./02_guides/dev.md) - Commands and environment
- [Debug](./02_guides/debug.md) - Common issues
- [Deploy](./02_guides/deploy.md) - Build and deploy

---

## Features

<!-- add links to 06_features/*.md as features are documented -->

---

## Rules

1. Always locate feature before editing code
2. Prefer modifying existing modules over creating new ones
3. Keep API backward compatible unless explicitly required
4. Check module constraints in `./04_modules/*`

---

## Navigation Strategy (for agents)

1. Start from feature_map → identify feature
2. Go to module_map → locate module
3. Use file_index → find exact files
4. Follow guides → perform action
