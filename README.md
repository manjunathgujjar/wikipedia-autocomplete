# Wikipedia Autocomplete Search

Real-time autocomplete search over 7.2 million Wikipedia article titles.

## Features

| Feature | Status |
|---|---|
| Prefix matching | ✅ As you type, titles starting with your query appear instantly |
| Case-insensitive | ✅ `charta` matches `Charta Health`, `CHARTA`, etc. |
| Clickable links | ✅ Each result links directly to the Wikipedia article |
| Real-time updates | ✅ Results update within 150 ms of each keystroke (debounced) |
| Search history | ✅ Recent searches shown when the input is empty (localStorage) |
| Clear button | ✅ × button clears the query |
| Dark mode | ✅ Follows system preference automatically |

## Architecture

```
Frontend (React/Vite)          Backend (FastAPI/Python)
  localhost:5173      ──────►   localhost:8000 /search?q=
                                       │
                                  Binary search
                                  on sorted mmap
                                       │
                               wikipedia-sorted.txt
                               (138 MB, disk-backed)
```

**Backend design choices:**

- **Memory-mapped file** — the 138 MB sorted titles file stays on disk; only a 29 MB `array.array` of `uint32` line offsets is held in RAM (vs 570+ MB for a Python `list[str]`).
- **Binary search via `bisect_left`** — O(log 7.2M) ≈ 23 comparisons per query.
- **OS `sort -f`** — sorts the file once on first startup using external merge sort (handles 138 MB with ~50 MB RAM, ~30 s). Subsequent starts skip this step.
- **CORS enabled** — accepts requests from any origin so the hosted frontend can reach the Railway backend.

## Running Locally

```bash
# Backend
cd autocomplete-search/backend
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
# First run: downloads 138 MB from S3, sorts it (~30s), then serves

# Frontend
cd autocomplete-search/frontend
npm install
npm run dev
# Open http://localhost:5173
```

## Deployment

| Component | Platform | Notes |
|---|---|---|
| Frontend | Vercel | Set `VITE_API_URL` env var to Railway backend URL |
| Backend | Railway | Root directory: `autocomplete-search/backend` |

On Railway first boot: downloads data file from S3 + sorts it (~2–3 min total). Subsequent restarts skip both steps and start in seconds.
