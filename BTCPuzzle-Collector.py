import requests
import os
import json
import time
import re
from datetime import datetime

# =============================================================================
# CONFIGURATIONS
# =============================================================================
BTCPUZZLE_URL = "https://btcpuzzle.info/puzzle67"  # URL to fetch puzzle info
# Replace with your desired storage location
HUNTERS_STORAGE_PATH = "REPLACE_WITH_STORAGE_PATH"

# Filenames for storing data
BTCPUZZLE_COMPLETED_FILE = os.path.join(HUNTERS_STORAGE_PATH, "BTCPUZZLE_completed.json")
BTCPUZZLE_SPEED_FILE     = os.path.join(HUNTERS_STORAGE_PATH, "BTCPUZZLE_speed.json")

# =============================================================================
# HELPER FUNCTIONS FOR FILE HANDLING & CLEANUP
# =============================================================================
def load_json(file_path):
    """
    Reads JSON data from a file.
    Returns a default object if the file is missing or the JSON is invalid.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "history": []
    }

def save_json(file_path, data):
    """Saves data to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def clean_old_data(history_list, days=30):
    """
    Removes entries older than 'days' days.
    Each entry in history_list is expected to be (timestamp, value).
    """
    cutoff_time = time.time() - days * 86400
    return [(ts, val) for (ts, val) in history_list if ts >= cutoff_time]

# =============================================================================
# FUNCTION TO FETCH HTML
# =============================================================================
def fetch_btcpuzzle_html():
    """
    Makes a simple GET request to the Puzzle 67 page on btcpuzzle.info.
    Returns the HTML string or None if an error occurs.
    """
    try:
        response = requests.get(BTCPUZZLE_URL, timeout=10)
        if response.ok:
            return response.text
        else:
            print(f"Failed to fetch {BTCPUZZLE_URL} (status {response.status_code})")
            return None
    except requests.RequestException as e:
        print("Exception while fetching btcpuzzle.info/puzzle67:", e)
        return None

# =============================================================================
# PARSE COMPLETED PERCENTAGE & SPEED
# =============================================================================
def parse_completed_and_speed(html):
    """
    Extracts:
      1) "Percentage completed" (e.g. 3.005195)
      2) "Current speed" (e.g. 730.09 Bkeys/s)
    Returns (completed, speed). If not found, returns (0.0, 0.0).
    """
    completed_val = 0.0
    speed_val = 0.0

    # 1) Find "Percentage completed" in the pattern:
    #    <div class="Template_progressbar__c36LG"><p>%<!-- -->3.005195</p>
    #    Regex pattern: >%<!-- -->XXXXXX</p>
    match_completed = re.search(r">%<!-- -->([\d.]+)</p>", html)
    if match_completed:
        try:
            completed_val = float(match_completed.group(1))
        except ValueError:
            pass

    # 2) Find "current speed" in the pattern:
    #    <p style="..."><strong style="...">730.09 Bkeys<!-- -->/s</strong><span>current speed</span></p>
    #    Regex: "([\d.]+)\s*Bkeys<!-- -->/s"
    match_speed = re.search(r"([\d.]+)\s*Bkeys<!-- -->/s", html)
    if match_speed:
        try:
            speed_val = float(match_speed.group(1))
        except ValueError:
            pass

    return (completed_val, speed_val)

# =============================================================================
# MAIN FUNCTION
# =============================================================================
def main():
    # 1) Load existing data
    completed_data = load_json(BTCPUZZLE_COMPLETED_FILE)  # { "history": [...], "current": ??? }
    speed_data = load_json(BTCPUZZLE_SPEED_FILE)          # { "history": [...], "current": ??? }

    # Ensure "current" key exists
    if "current" not in completed_data:
        completed_data["current"] = 0.0
    if "current" not in speed_data:
        speed_data["current"] = 0.0

    # 2) Fetch HTML from Puzzle 67 page
    html = fetch_btcpuzzle_html()
    if not html:
        print("No HTML returned from btcpuzzle.info. Aborting.")
        return

    # 3) Parse "percentage completed" and "current speed"
    completed, speed = parse_completed_and_speed(html)
    print(f"btcpuzzle.info/puzzle67 parsed -> Completed: {completed:.6f}%, Speed: {speed:.2f} Bkeys/s")

    # 4) Update data and add to history
    now_ts = time.time()

    completed_data["current"] = completed
    completed_data["history"].append((now_ts, completed))

    speed_data["current"] = speed
    speed_data["history"].append((now_ts, speed))

    # 5) Clean old data (older than 30 days)
    completed_data["history"] = clean_old_data(completed_data["history"], days=30)
    speed_data["history"]     = clean_old_data(speed_data["history"], days=30)

    # 6) Save results
    save_json(BTCPUZZLE_COMPLETED_FILE, completed_data)
    save_json(BTCPUZZLE_SPEED_FILE, speed_data)

    print("BTCPUZZLE data successfully collected and saved.")

if __name__ == "__main__":
    main()
