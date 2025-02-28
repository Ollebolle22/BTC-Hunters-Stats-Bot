import requests
from bs4 import BeautifulSoup
import os
import json
import time
from datetime import datetime

# =============================================================================
# CONFIGURATIONS
# =============================================================================
LOGIN_URL        = 'https://btc-hunters.com/login'
DASHBOARD_URL    = 'https://btc-hunters.com/dashboard'
USERNAME         = 'REPLACE_WITH_USERNAME'
PASSWORD         = 'REPLACE_WITH_PASSWORD'

# Replace with your desired storage location
HUNTERS_STORAGE_PATH = 'REPLACE_WITH_STORAGE_PATH'

PREVIOUS_COMPLETED_FILE = os.path.join(HUNTERS_STORAGE_PATH, 'previous_completed.json')
PREVIOUS_SPEED_FILE     = os.path.join(HUNTERS_STORAGE_PATH, 'previous_speed.json')
RANGES_HISTORY_FILE     = os.path.join(HUNTERS_STORAGE_PATH, 'ranges_history.json')
TOTAL_RANGES_FILE       = os.path.join(HUNTERS_STORAGE_PATH, 'total_ranges.json')

# =============================================================================
# LOAD JSON DATA
# =============================================================================
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

# =============================================================================
# SAVE JSON DATA
# =============================================================================
def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# =============================================================================
# CLEAN OLD DATA
# =============================================================================
def clean_old_data(data, cutoff_time):
    """
    Removes entries older than the cutoff_time.
    Expects data as a dictionary with user as key and list of (timestamp, ranges, speed) tuples.
    """
    return {user: [(t, r, s) for t, r, s in entries if t >= cutoff_time] for user, entries in data.items()}

# =============================================================================
# SCRAPE DASHBOARD
# =============================================================================
def scrape_dashboard():
    session = requests.Session()
    payload = {'Name': USERNAME, 'Password': PASSWORD}
    login_response = session.post(LOGIN_URL, data=payload)

    if not login_response.ok or "Dashboard" not in login_response.text:
        print(f"Login failed: {login_response.status_code}")
        return None

    dashboard_response = session.get(DASHBOARD_URL)
    if dashboard_response.ok:
        return dashboard_response.text
    else:
        print(f"Failed to fetch dashboard: {dashboard_response.status_code}")
        return None

# =============================================================================
# PROCESS DASHBOARD DATA
# =============================================================================
def process_dashboard(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Progress
    progress_div = soup.find('div', class_='completed')
    progress_str = progress_div.text.strip('%').replace(',', '') if progress_div else "0"
    progress = float(progress_str)

    # Pool Speed
    speed_div = soup.find('div', class_='text-block-10')
    if not speed_div:
        pool_speed = 0.0
    else:
        speed_text = speed_div.text.strip()  # e.g. "1234 Bk/s" or "1.618 Tk/s"
        splitted = speed_text.split()
        pool_speed_str = splitted[0].replace(',', '')
        pool_speed = float(pool_speed_str)

        # Check if speed is in "TKeys/s" and multiply by 1000 if needed
        if "TKeys/s" in speed_text:
            pool_speed *= 1000

    # Total Ranges
    total_ranges_div = soup.find('div', class_='total-pool-scanned-ranges')
    total_ranges = int(total_ranges_div.text.replace(',', '')) if total_ranges_div else 0

    # Ranges per User (Top 10 and All Active)
    user_rows = soup.find_all('tr', class_='user-row')
    user_data = {}
    for row in user_rows:
        columns = row.find_all('td')
        if len(columns) >= 3:
            username = columns[0].text.strip()
            submitted_ranges = int(columns[1].text.strip().replace(',', ''))

            # Example text: "1234 Bk/s" or "1.618 Tk/s"
            speed_text_user = columns[2].text.strip()   # e.g. "1.618 Tk/s", possibly " Bk/s"
            
            # Check if speed is in TKeys/s
            speed_is_tk = "TKeys/s" in speed_text_user
            # Remove potential units and commas to get the raw number
            raw_speed_str = speed_text_user.replace(' BKeys/s', '').replace(' TKeys/s', '').replace(',', '')
            
            speed_value = float(raw_speed_str)
            if speed_is_tk:
                speed_value *= 1000

            user_data[username] = (submitted_ranges, speed_value)

    return progress, pool_speed, total_ranges, user_data

# =============================================================================
# MAIN FUNCTION
# =============================================================================
def main():
    current_time = time.time()
    cutoff_time = current_time - (30 * 86400)  # 30 days ago

    # Load existing data
    ranges_history   = load_json(RANGES_HISTORY_FILE).get("data", {})
    completion_data  = load_json(PREVIOUS_COMPLETED_FILE)
    speed_data       = load_json(PREVIOUS_SPEED_FILE)
    total_ranges_data= load_json(TOTAL_RANGES_FILE)

    # Scrape and process dashboard data
    html = scrape_dashboard()
    if not html:
        return

    progress, pool_speed, total_ranges, user_data = process_dashboard(html)

    # Update ranges_history
    for user, (submitted_ranges, speed) in user_data.items():
        if user not in ranges_history:
            ranges_history[user] = []
        ranges_history[user].append((current_time, submitted_ranges, speed))

    ranges_history = clean_old_data(ranges_history, cutoff_time)

    # Update completion_data
    if "history" not in completion_data:
        completion_data["history"] = []
    completion_data["current"] = progress
    completion_data["history"].append((current_time, progress))

    # Update speed_data
    if "history" not in speed_data:
        speed_data["history"] = []
    speed_data["current"] = pool_speed
    speed_data["history"].append((current_time, pool_speed))

    # Update total_ranges_data
    if "history" not in total_ranges_data:
        total_ranges_data["history"] = []
    total_ranges_data["current"] = total_ranges
    total_ranges_data["history"].append((current_time, total_ranges))

    # Save all updates
    save_json(RANGES_HISTORY_FILE, {"data": ranges_history})
    save_json(PREVIOUS_COMPLETED_FILE, completion_data)
    save_json(PREVIOUS_SPEED_FILE, speed_data)
    save_json(TOTAL_RANGES_FILE, total_ranges_data)

    print("Data collection complete and saved.")

if __name__ == "__main__":
    main()
