from fastapi import FastAPI, HTTPException
import json, os, time
from datetime import datetime

from main import scrape_mba_colleges   # 🔥 MASTER FUNCTION

app = FastAPI(title="MBA Colleges API")

DATA_FILE = "mba_data.json"
LAST_UPDATED = 0
UPDATE_INTERVAL = 6 * 60 * 60   # 6 hours


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def update_data_if_needed():
    global LAST_UPDATED

    if not os.path.exists(DATA_FILE) or (time.time() - LAST_UPDATED > UPDATE_INTERVAL):
        print(f"[{datetime.now()}] 🔄 Scraping started")
        data = scrape_mba_colleges()

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        LAST_UPDATED = time.time()
        print(f"[{datetime.now()}] ✅ Scraping done")


@app.get("/")
def root():
    return {"message": "MBA API is running 🚀"}


@app.get("/mba_colleges")
def get_all_data():
    update_data_if_needed()
    return load_data()


@app.get("/mba_colleges/{section}")
def get_section(section: str):
    update_data_if_needed()
    data = load_data()

    if section not in data:
        raise HTTPException(status_code=404, detail="Section not found")

    return data[section]
