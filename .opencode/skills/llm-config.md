# llm-config

Set up or change the AI service provider for replenishment recommendation enhancement.

## Available providers

### DeepSeek
In `backend/.env`:
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

### Ollama
Requires Ollama running locally:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
```

### Rule engine
```env
LLM_PROVIDER=rule
```

## Verify configuration
After restarting backend:
```
GET http://127.0.0.1:8000/api/llm/status
```

Response fields:
- `provider`
- `model_name`
- `available`
- `key_configured` — whether DeepSeek API key is set

## Generate recommendations with LLM
```
POST http://127.0.0.1:8000/api/recommendations/generate?enhance_with_llm=true
```

## Architecture
- Provider routing: `backend/app/services/llm/llm_router.py`
- Abstract base: `backend/app/services/llm/base.py`
- DeepSeek client: `backend/app/services/llm/deepseek_client.py`
- Ollama client: `backend/app/services/llm/ollama_client.py`
- Prompt templates: `backend/app/services/llm/prompt_templates.py`

## Important
- **Never commit `backend/.env`** — it contains real API keys
- LLM only enhances replenishment reasons, core logic (quantities, risk levels) runs on rule engine regardless
- If LLM call fails, the system returns rule-based reasons without crashing
