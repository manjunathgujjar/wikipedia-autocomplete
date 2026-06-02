import os
import mmap
import array
import subprocess
import urllib.request
from bisect import bisect_left
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DATA_FILE = "wikipedia-latest-titles.txt"
SORTED_FILE = "wikipedia-sorted.txt"
DATA_URL = "https://charta-public.s3.us-east-2.amazonaws.com/interview/wikipedia-latest-titles.txt"

if not os.path.exists(DATA_FILE):
    print("Downloading wikipedia-latest-titles.txt from S3...")
    urllib.request.urlretrieve(DATA_URL, DATA_FILE)
    print("Download complete.")

# Sort once using the OS sort command — handles 138 MB on disk without
# loading everything into Python heap (external merge sort, ~30s, ~50 MB RAM).
if not os.path.exists(SORTED_FILE):
    print("Sorting titles (one-time, ~30s)...")
    env = {**os.environ, "LC_ALL": "C"}  # fast byte-order sort
    subprocess.run(["sort", "-f", DATA_FILE, "-o", SORTED_FILE], env=env, check=True)
    print("Sort complete.")

# Memory-map the sorted file and build a uint32 offset index.
# Total RAM: ~29 MB for offsets + OS-managed mmap — vs 570+ MB for a Python list.
print("Building index...")
_f = open(SORTED_FILE, "rb")
_mm = mmap.mmap(_f.fileno(), 0, access=mmap.ACCESS_READ)
_size = len(_mm)

_offsets = array.array("I", [0])
pos = 0
while True:
    nl = _mm.find(b"\n", pos)
    if nl == -1:
        break
    if nl + 1 < _size:
        _offsets.append(nl + 1)
    pos = nl + 1

print(f"Ready: {len(_offsets):,} titles indexed.")


def _get_title(idx: int) -> str:
    start = _offsets[idx]
    nl = _mm.find(b"\n", start)
    end = nl if nl != -1 else _size
    return _mm[start:end].decode("utf-8", errors="replace").strip()


class _TitleProxy:
    """Sequence proxy for bisect — returns lowercase titles without storing them."""
    def __getitem__(self, idx): return _get_title(idx).lower()
    def __len__(self): return len(_offsets)


_proxy = _TitleProxy()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


def get_matches(prefix: str, limit: int = 10):
    p = prefix.lower()
    lo = bisect_left(_proxy, p)
    hi = bisect_left(_proxy, p + chr(255))
    return [_get_title(i) for i in range(lo, min(hi, lo + limit))]


@app.get("/search")
def search(q: str):
    if not q:
        return []
    return [
        {"title": t, "url": f"https://en.wikipedia.org/wiki/{t.replace(' ', '_')}"}
        for t in get_matches(q)
    ]
