# Deploy Guide

## Docker Build

```bash
docker build -t xianyuautoagent .
```

## Docker Run

```bash
docker run -d --name xianyuautoagent \
  -v ./data:/app/data \
  -v ./prompts:/app/prompts \
  -v ./.env:/app/.env \
  xianyuautoagent
```

## Docker Compose

```bash
docker-compose up -d
```

## Deployment Pipeline

```mermaid
flowchart LR
    A[Build Image] --> B[Push Registry]
    B --> C[Deploy Container]
    C --> D[Health Check]
```
