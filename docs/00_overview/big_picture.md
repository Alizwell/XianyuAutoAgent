# Big Picture

AI-powered hotel booking agent for the Xianyu (闲鱼) platform.

## Core Flow

Xianyu WebSocket API → WebSocket Client → Intent Router → Agent → LLM (OpenAI API)

## Constraints

- Requires Xianyu account with active WebSocket connection
- In-memory context storage (volatile)
- Manual mode control for human oversight
