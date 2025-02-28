import requests
from bs4 import BeautifulSoup
import os
import json
import time
import re
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
TTD_LOGIN_URL             = "https://www.ttdsales.com/67bit/login.php"
TTD_USERNAME              = "REPLACE_WITH_USERNAME"
TTD_PASSWORD              = "REPLACE_WITH_PASSWORD"

# Replace this path with your own desired storage location
HUNTERS_STORAGE_PATH      = "REPLACE_WITH_HUNTERS_STORAGE_PATH"

# These two JSON files store the data:
TTD_COMPLETED_FILE        = os.path.join(HUNTERS_STORAGE_PATH, "TTD_minimal_completed.json")
TTD_SPEED_FILE            = os.path.join(HUNTERS_STORAGE_PATH, "TTD_minimal_speed.json")

# =============================================================================
# HELPER FUNCTIONS FOR FILE HANDLING & CLEANUP
# =============================================================================

def load_json(file_path):
    """
    Reads JSON data from a file and returns a default object if the file is 
    missing or the JSON is corrupted.
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
    Takes a list of (timestamp, value) and removes any entries older than 
    'days' days.
    Returns a new list with only the retained data points.
    """
    cutoff_time = time.time() - days * 86400
    return [(ts, val) for (ts, val) in history_list if ts >= cutoff_time]

# =============================================================================
# LOG IN AND FETCH HTML
# =============================================================================
def scrape_ttd_dashboard():
    """
    Logs in to TTD and returns the HTML.
    Returns None if something goes wrong.
    """
    session = requests.Session()
    payload = {
        "username": TTD_USERNAME,
        "password": TTD_PASSWORD
    }
    try:
        login_response = session.post(TTD_LOGIN_URL, data=payload, timeout=10)
        if not login_response.ok:
            print(f"TTD login request failed: {login_response.status_code}")
            return None

        if "Log Out" not in login_response.text and "logout.php" not in login_response.text:
            print("Did not find 'Log Out' in the response - login might have failed.")
            return None

        # Assumes that the same page directly contains "Percentage completed" and "BK/s"
        return login_response.text

    except requests.RequestException as e:
        print("Exception during login request:", e)
        return None

# =============================================================================
# PARSE PERCENTAGE & SPEED
# =============================================================================
def parse_percentage_and_speed(html):
    """
    Returns a tuple (percentage_completed, pool_speed).
    If something is missing in the HTML, it returns (0.0, 0.0).
    """
    percentage_completed = 0.0
    pool_speed = 0.0

    # 1) Percentage completed
    match_completion = re.search(
        r"Percentage completed:\s*([\d.]+)%",  # e.g. "Percentage completed: 3.516763%"
        html
    )
    if match_completion:
        percentage_completed = float(match_completion.group(1))

    # 2) Pool Speed (e.g. "234.0 BK/s")
    match_speed = re.search(
        r"(\d+\.\d+)\s*BK/s",  # extracts e.g. "234.0 BK/s"
        html
    )
    if match_speed:
        pool_speed = float(match_speed.group(1))

    return (percentage_completed, pool_speed)

# =============================================================================
# MAIN FUNCTION
# =============================================================================
def main():
    # 1) Load existing data
    completed_data = load_json(TTD_COMPLETED_FILE)  # { "history": [...], "current": ??? }
    speed_data     = load_json(TTD_SPEED_FILE)      # { "history": [...], "current": ??? }

    # Ensure that the required keys exist
    if "current" not in completed_data:
        completed_data["current"] = 0.0
    if "current" not in speed_data:
        speed_data["current"] = 0.0

    # 2) Scrape TTD
    html = scrape_ttd_dashboard()
    if not html:
        print("No HTML from TTD. Aborting.")
        return

    # 3) Parse
    percentage, speed = parse_percentage_and_speed(html)
    print(f"Parsed: Percentage completed = {percentage}%, Pool speed = {speed} BK/s")

    # 4) Update data and history
    now_ts = time.time()

    # Completed
    completed_data["current"] = percentage
    completed_data["history"].append((now_ts, percentage))

    # Speed
    speed_data["current"] = speed
    speed_data["history"].append((now_ts, speed))

    # 5) Clean data older than 30 days
    completed_data["history"] = clean_old_data(completed_data["history"], days=30)
    speed_data["history"]     = clean_old_data(speed_data["history"], days=30)

    # 6) Save data
    save_json(TTD_COMPLETED_FILE, completed_data)
    save_json(TTD_SPEED_FILE, speed_data)

    print("Saved TTD minimal data successfully.")

if __name__ == "__main__":
    main()
