from fastapi import FastAPI, HTTPException
import json, os, threading
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime



# ✅ Import your scraper function from main.py
from main import scrape_mba_colleges  # Make sure this function returns the structured JSON

app = FastAPI(title="MBA Colleges API")
DATA_FILE = "mba_data.json"

# -------------------------
# 1️⃣ Load data from JSON
# -------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# -------------------------
# 2️⃣ Function to update data
# -------------------------
def update_data():
    """
    Calls the scraper in main.py and updates mba_data.json
    """
    try:
        print(f"[{datetime.now()}] Starting data update...")
        data = scrape_mba_colleges()  # your function in main.py
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[{datetime.now()}] Data updated successfully!")
    except Exception as e:
        print(f"[{datetime.now()}] Error updating data: {e}")

# -------------------------
# 3️⃣ FastAPI Endpoints
# -------------------------
@app.get("/")
async def root():
    return {"message": "API is running! Go to /mba_colleges to see all colleges."}

@app.get("/mba_colleges")
async def get_all_colleges():
    return {"mba_colleges": load_data()}

@app.get("/mba_colleges/{college_id}")
async def get_college_by_id(college_id: int):
    data = load_data()
    idx = 1
    for section in data:
        for college in section.get("colleges", []):
            if idx == college_id:
                return college
            idx += 1
    raise HTTPException(status_code=404, detail="College not found")

# -------------------------
# 4️⃣ Scheduler to auto-update every 6 hours
# -------------------------
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_data, 'interval', hours=6)  # run every 6 hours
    scheduler.start()

# Run scheduler in a separate daemon thread
threading.Thread(target=start_scheduler, daemon=True).start()

# -------------------------
# 5️⃣ Optional: initial update at startup
# -------------------------
update_data()
