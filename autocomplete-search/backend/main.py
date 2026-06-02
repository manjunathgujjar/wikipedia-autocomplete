import os
import mmap
import array
import subprocess
import urllib.request
from bisect import bisect_left
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DATA_FILE = "wikipedia-latest-titles.txt"
LOWER_FILE = "wikipedia-lower.txt"
SORTED_FILE = "wikipedia-sorted.txt"
SORT_DONE  = "wikipedia-sort.done"
DATA_URL   = "https://charta-public.s3.us-east-2.amazonaws.com/interview/wikipedia-latest-titles.txt"

if not os.path.exists(DATA_FILE):
    print("Downloading wikipedia-latest-titles.txt from S3...")
    urllib.request.urlretrieve(DATA_URL, DATA_FILE)
    print("Download complete.")

if not os.path.exists(SORT_DONE):
    # Clean up any partial files from a previous killed run
    for f in (LOWER_FILE, SORTED_FILE):
        if os.path.exists(f):
            os.remove(f)

    # Stream-lowercase the file (O(1) memory)
    print("Lowercasing titles...")
    with open(DATA_FILE, "r", encoding="utf-8", errors="replace") as fin, \
         open(LOWER_FILE, "w", encoding="utf-8") as fout:
        for line in fin:
            t = line.strip()
            if t:
                fout.write(t.lower() + "\n")

    # Sort with OS external merge sort, capped at 256 MB RAM
    print("Sorting titles (one-time, ~60s)...")
    subprocess.run(
        ["sort", "--buffer-size=256M", LOWER_FILE, "-o", SORTED_FILE],
        env={**os.environ, "LC_ALL": "C"},
        check=True,
    )
    os.remove(LOWER_FILE)
    open(SORT_DONE, "w").close()  # Mark success so restarts skip this
    print("Sort complete.")

# Memory-map the sorted file + build a uint32 offset index.
# RAM cost: ~29 MB for offsets; file stays on disk via mmap.
print("Building index...")
_f  = open(SORTED_FILE, "rb")
_mm = mmap.mmap(_f.fileno(), 0, access=mmap.ACCESS_READ)
_sz = len(_mm)

_offsets = array.array("I", [0])
pos = 0
while True:
    nl = _mm.find(b"\n", pos)
    if nl == -1:
        break
    if nl + 1 < _sz:
        _offsets.append(nl + 1)
    pos = nl + 1

print(f"Ready: {len(_offsets):,} titles indexed.")


def _get_title(idx: int) -> str:
    start = _offsets[idx]
    nl    = _mm.find(b"\n", start)
    end   = nl if nl != -1 else _sz
    return _mm[start:end].decode("utf-8", errors="replace").strip()


class _Proxy:
    """Sequence proxy for bisect — reads titles from mmap on demand."""
    def __getitem__(self, idx): return _get_title(idx)  # file is already lowercase
    def __len__(self): return len(_offsets)


_proxy = _Proxy()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


def get_matches(prefix: str, limit: int = 10):
    p  = prefix.lower()
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
