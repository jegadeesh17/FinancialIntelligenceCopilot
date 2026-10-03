# API Reference — Financial Intelligence Copilot

FastAPI service defined in `api/main.py`. Interactive Swagger docs are served at `/docs`.

Base URL (live): `https://financial-copilot-api-242711953247.asia-south1.run.app`
Local: `http://localhost:8000` (`uvicorn api.main:app --port 8000`) or `http://localhost:8080` (Docker).

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | status, indexed chunk count, corpus mix, index metadata |
| GET | `/eval` | latest RAGAS and retrieval-benchmark summary (feeds the UI "Eval metrics" popover) |
| POST | `/ask` | question in, grounded answer with citations out |
| GET | `/app` | web UI (static `api/index.html`) |
| GET | `/` | redirects to `/app` |

### `GET /health`

Returns `{"status": "ok", "chunk_count": <int>, "corpus": {...}, "index_metadata": {...}}`.

### `GET /eval`

Returns `{"answer_quality": {<mode>: {...}}, "retrieval": {...} | null}`, read from `reports/ragas_eval.json` and `reports/rag_benchmark.json`. Each `answer_quality` mode holds `means`, `nan_counts`, `n_questions`, `generator_model`, `judge_model`, `ragas_version` and `date`. `retrieval` holds `top_k` and, per mode, `hit_rate`, `mrr`, `avg_precision_k` and `total`. Returns `404` if `reports/ragas_eval.json` is missing.

### `POST /ask`

Request body:

| Field | Type | Notes |
|-------|------|-------|
| `question` | string | required, 1–2000 characters |
| `hybrid` | boolean | optional; defaults to the server's `ENABLE_HYBRID_SEARCH` (true) |

Response body:

| Field | Type | Notes |
|-------|------|-------|
| `answer` | string | generated only from retrieved context |
| `citations` | list of `{source, page}` | document filename and page number |
| `model` | string | LLM that produced the answer |
| `low_confidence` | boolean | true when the best retrieval distance is above `LOW_CONFIDENCE_DISTANCE` (default 0.85) |
| `best_score` | number or null | best (lowest) retrieval distance |
| `source_chunks` | list | up to 5 of `{source, page, text (first 500 chars), score, retrieved_at, regulator, document_category}` |

Example:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"question": "What KYC documents are required for individual customers?", "hybrid": true}'
```

Omit the `x-api-key` header when `API_KEY` is not set on the server.

## Authentication and rate limiting

- If the server has `API_KEY` set, `/ask` requires header `x-api-key: <key>`; otherwise it returns `401`. When `API_KEY` is empty, `/ask` is open. Other endpoints are never key-protected.
- `/ask` is limited to `API_RATE_LIMIT_PER_MINUTE` requests (default 60) per client IP per rolling 60 seconds, held in memory per instance. Excess requests return `429`.

## Errors

| Status | When | Body |
|--------|------|------|
| 401 | wrong or missing `x-api-key` while `API_KEY` is set | `{"detail": "Invalid API key."}` |
| 404 | `/eval` report missing, or UI file missing | `{"detail": "..."}` |
| 422 | invalid body (empty or over-long `question`) | FastAPI validation detail |
| 429 | rate limit exceeded | `{"detail": "Rate limit exceeded. Try again in a minute."}` |
| 500 | any unhandled error (details are logged server-side only) | `{"error": "internal_error", "detail": "An unexpected error occurred."}` |
