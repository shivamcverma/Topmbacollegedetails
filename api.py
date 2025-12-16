from fastapi import FastAPI, HTTPException
import json, os
from datetime import datetime

app = FastAPI(title="MBA Colleges API")

DATA_FILE = "iim_ahmedabad_full_data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        raise HTTPException(
            status_code=503,
            detail="Data not generated yet. Please wait."
        )

    last_updated = datetime.fromtimestamp(
        os.path.getmtime(DATA_FILE)
    ).isoformat()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "last_updated": last_updated,
        "data": data
    }


@app.get("/")
def root():
    return {
        "status": "API running 🚀",
        "source": "GitHub Actions Auto Scraper"
    }


@app.get("/mba_colleges_details")
def get_all_data():
    return load_data()


@app.get("/mba_colleges_details/{section}")
def get_section(section: str):
    payload = load_data()
    data = payload["data"]

    if section not in data:
        raise HTTPException(status_code=404, detail="Section not found")

    return {
        "last_updated": payload["last_updated"],
        "section": section,
        "data": data[section]
    }
