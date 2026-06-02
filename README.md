# Wikipedia Autocomplete Search

Real-time autocomplete search over 7.2 million Wikipedia article titles.

**Live demo:** [Frontend on Vercel](https://wikipedia-autocomplete.vercel.app) · [Backend on Railway](https://wikipedia-autocomplete-production.up.railway.app/search?q=cha)

---

## Features Implemented

| Feature | Status | Notes |
|---|---|---|
| Prefix matching | ✅ | Titles starting with your query appear as you type |
| Case-insensitive | ✅ | `CHA`, `cha`, `Cha` all return the same results |
| Real-time updates | ✅ | 150 ms debounce — fast without hammering the backend |
| Clickable result links | ✅ | Each result opens the Wikipedia article in a new tab |
| Search history | ✅ | Recent searches shown when input is empty (localStorage, max 10) |
| Clear button | ✅ | × clears the query instantly |
| Dark mode | ✅ | Follows system preference automatically |
| Full dataset | ✅ | All 7,226,822 Wikipedia titles indexed |

## Architecture

```
Browser (React/Vite)
  ↓  type "cha"
  ↓  debounce 150ms
  ↓  fetch /search?q=cha
FastAPI backend
  ↓  bisect_left on sorted mmap  (O(log 7.2M) ≈ 23 comparisons)
  ↓  read 10 matching titles from disk
  ↓  return JSON [{title, url}, ...]
Browser renders dropdown
```

## Backend Design

- **mmap + uint32 offset index** — the sorted titles file (138 MB) stays on disk; only a 29 MB `array.array` of line offsets is kept in RAM. Contrast: a Python `list[str]` of all titles would use 570+ MB.
- **Binary search** — `bisect_left` on the mmap proxy: O(log 7.2M) ≈ 23 disk reads per query, all served from OS page cache.
- **One-time OS sort** — on first boot, titles are streamed to a lowercase file (O(1) RAM), then sorted with `sort --buffer-size=256M` (external merge sort, stays under 256 MB). A marker file prevents re-sorting on restarts.
- **Total RAM on Railway free tier: ~180 MB** (well under the 1 GB limit).

## Known Tradeoffs

- **Lowercase display** — titles are stored lowercase for memory-efficient sorting. Production fix: store `lowercase_key\tOriginal Title` pairs and split on read.
- **First boot is slow** — ~2 min to download (138 MB) + sort. Subsequent restarts start in seconds.

## Running Locally

```bash
# Backend (Python 3.10+)
cd autocomplete-search/backend
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
# First run downloads + sorts the data file automatically

# Frontend
cd autocomplete-search/frontend
npm install
npm run dev
# Open http://localhost:5173
```

## Deployment

| Component | Platform | Config |
|---|---|---|
| Frontend | Vercel | Root dir: `autocomplete-search/frontend`, env var: `VITE_API_URL=<railway-url>` |
| Backend | Railway | Root dir: `autocomplete-search/backend`, auto-detects Python + Procfile |
