import os
import urllib.request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bisect import bisect_left

DATA_FILE = "wikipedia-latest-titles.txt"
DATA_URL = "https://charta-public.s3.us-east-2.amazonaws.com/interview/wikipedia-latest-titles.txt"

if not os.path.exists(DATA_FILE):
    print(f"Downloading {DATA_FILE} from S3...")
    urllib.request.urlretrieve(DATA_URL, DATA_FILE)
    print("Download complete.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    titles = sorted([line.strip() for line in f if line.strip()], key=str.lower)

def get_matches(prefix, limit=10):
    prefix = prefix.lower()
    start = bisect_left(titles, prefix, key=str.lower)
    end = bisect_left(titles, prefix + chr(255), key=str.lower)
    return titles[start:min(end, start + limit)]

@app.get("/search")
def search(q: str):
    if not q:
        return []
    results =  get_matches(q)
    return [
        {
            "title": title,
            "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        }
        for title in results
    ]
