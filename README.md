# LearnInngest: Event-Driven Chat Backend (FastAPI + Inngest + OpenRouter)

## Overview

This project is a small, practical example of using **Inngest** to run an AI chat request in the background.

Instead of running the LLM call directly inside the HTTP request (slow + can time out), the backend uses an event-driven flow:

- The client sends a chat request to FastAPI.
- FastAPI **emits an Inngest event** (`app/chat.requested`).
- An **Inngest function** consumes the event, runs the LLM call (OpenRouter via LangChain), and stores the result.
- The client polls a result endpoint until the response is ready.

Pattern: **request → enqueue → background processing → result retrieval**.

---

## Prerequisites

- Python 3.10+
- Node.js 18+ (for `npx inngest-cli`)
- An OpenRouter API key (`OPENROUTER_API_KEY`)

---

## Quickstart (Windows)

You need **two terminals**.

### 1) Start FastAPI

From `backend/`:

```powershell
$env:INNGEST_DEV="1"
python main.py
```

Open Swagger:

- `http://127.0.0.1:8000/docs`

### 2) Start Inngest Dev Server

From `backend/`:

```powershell
npx --ignore-scripts=false inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
```

Open Inngest UI:

- `http://127.0.0.1:8288`

### 3) Enqueue a chat request

- **POST** `http://127.0.0.1:8000/api/v1/chat`

---

## Folder Structure

```text
LearnInngest/
  README.md
  backend/
    main.py                      # FastAPI entrypoint + mounts /api/inngest
    requirements.txt
    .env
    app/
      inngest_app.py              # inngest_client + chat_worker function
      api/
        routes/
          v1/
            chat.py               # POST /chat emits event + GET /chat/result polls
      services/
        chat_service.py           # chat_completion() (OpenRouter via LangChain)
      utils/
        helpers.py
    learning.ipynb
    results.ipynb
```

---

## Architecture (Option A)

### Why Option A?

Option A is useful when:

- **LLM calls are slow** or variable in latency.
- You want **retries** and durable execution (handled by Inngest).
- You want to keep HTTP endpoints fast and predictable.

### Data Flow

1. **Client → FastAPI**
   - `POST /api/v1/chat` with `{ query, temperature, max_tokens, clean }`

2. **FastAPI → Inngest (Event Send)**
   - The route generates a `request_id`
   - Stores initial state: `{"status":"pending"}`
   - Sends event: `app/chat.requested` with payload data

3. **Inngest Dev Server → FastAPI Inngest handler**
   - Inngest discovers and executes functions via the handler mounted at:
     - `GET/PUT/POST /api/inngest`

4. **Inngest Function executes**
   - Triggered by: `app/chat.requested`
   - Calls `chat_completion()` which uses OpenRouter via LangChain
   - Stores output:
     - `{"status":"done","content":"..."}`

5. **Client polls**
   - `GET /api/v1/chat/result/{request_id}`

---

## Mental model (code point of view)

The system has two call paths that meet at the event name `app/chat.requested`:

1. **HTTP path (enqueue)**
   - `backend/app/api/routes/v1/chat.py`
   - `POST /api/v1/chat` calls `inngest_client.send_sync(Event(name="app/chat.requested", data=...))`
   - This route does not call the worker directly.

2. **Inngest execution path (run worker)**
   - `backend/main.py` mounts the Inngest handler: `inngest.fast_api.serve(app, inngest_client, [chat_worker])`
   - `backend/app/inngest_app.py` defines `chat_worker` with a trigger on `app/chat.requested`
   - Inngest calls back into your FastAPI `/api/inngest` handler, which dispatches to `chat_worker(ctx)`.

Results are stored in-process in `CHAT_RESULTS` and fetched via `GET /api/v1/chat/result/{request_id}`.

---

## Key Endpoints

### 1) Enqueue chat request

- **POST** `http://127.0.0.1:8000/api/v1/chat`
- **Body**

```json
{
  "query": "What is the capital of France?",
  "temperature": 0.7,
  "max_tokens": 200,
  "clean": true
}
```

- **Response**

```json
{
  "request_id": "<uuid>"
}
```

### 2) Fetch chat result

- **GET** `http://127.0.0.1:8000/api/v1/chat/result/<request_id>`

Possible responses:

- Pending:

```json
{ "status": "pending" }
```

- Done:

```json
{ "status": "done", "content": "Paris." }
```

- Error:

```json
{ "status": "error", "error": "..." }
```

### 3) Inngest handler (do not call manually)

- `GET /api/inngest`
- `PUT /api/inngest`
- `POST /api/inngest`

These are automatically used by the **Inngest Dev Server** for:

- function discovery
- syncing
- executing function runs

---

## Where the Inngest Logic Lives

- **FastAPI app wiring**: `backend/main.py`
  - mounts the Inngest handler using `inngest.fast_api.serve(...)`

- **Inngest client + function**: `backend/app/inngest_app.py`
  - defines `inngest_client`
  - defines the function `chat_worker` triggered by `app/chat.requested`
  - stores results in an in-memory map (`CHAT_RESULTS`)

- **LLM call**: `backend/app/services/chat_service.py`
  - function `chat_completion(...)` calls OpenRouter via LangChain

---

## Environment Variables

Create a `backend/.env` file.

### Required

- `OPENROUTER_API_KEY` — your OpenRouter key

### Recommended (Local Development)

- `INNGEST_DEV=1`
  - tells the Inngest Python SDK to run in **Dev mode**
  - Dev mode disables signing requirements for the local Dev Server

### Optional

- `OPENROUTER_MODEL` (default used: `google/gemini-3-flash-preview`)
- `OPENROUTER_SITE_URL` (sent as `HTTP-Referer`)
- `OPENROUTER_APP_NAME` (sent as `X-Title`)

> Note: For the local Inngest Dev Server, you should not set `INNGEST_SIGNING_KEY`.

---

## Running Locally (Windows)

You need **two terminals**.

### Terminal 1 — Start FastAPI

From `backend/`:

```powershell
(base) PS D:\Code_Env\Python_Env\LearnInngest\backend> $env:INNGEST_DEV="1"
(base) PS D:\Code_Env\Python_Env\LearnInngest\backend> python main.py
```

Keep this terminal running.

Alternatively, you can start Uvicorn directly:

```powershell
$env:INNGEST_DEV="1"
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open Swagger:

- `http://127.0.0.1:8000/docs`

### Terminal 2 — Start Inngest Dev Server

From `backend/`:

```powershell
(base) PS D:\Code_Env\Python_Env\LearnInngest\backend> npx --ignore-scripts=false inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
```

Keep this terminal running.

Open Inngest UI:

- `http://127.0.0.1:8288`

---

## Troubleshooting

### Inngest UI shows no functions / no runs

- Make sure FastAPI is running and reachable at `http://127.0.0.1:8000`.
- Make sure you started the dev server with the correct URL:
  - `-u http://127.0.0.1:8000/api/inngest`

### `/api/v1/chat/result/{request_id}` stays `pending`

- Confirm the Inngest Dev Server is running and shows the event/runs in `http://127.0.0.1:8288`.
- Check FastAPI logs for worker errors.
- Ensure `OPENROUTER_API_KEY` is set.

---

## Notes / Limitations

- **In-memory result storage**: results are stored in-process. Restarting FastAPI clears results.
- **Production readiness**:
  - Store results in Redis/Postgres
  - Use Inngest Cloud and configure signing keys (`INNGEST_SIGNING_KEY`)
  - Add authentication and rate-limiting

---

## Developer

**Dr. Partha Majumder**
