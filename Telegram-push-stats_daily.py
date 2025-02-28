#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import json
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

# =============================================================================
# CONFIGURATION
# =============================================================================
BOT_TOKEN = "REPLACE_WITH_BOT_TOKEN"  # Preferably use an environment variable!
OFFICIAL_CHAT_ID = "REPLACE_WITH_OFFICIAL_CHAT_ID"  # Your official group chat ID
OFFICIAL_THREAD_ID = "REPLACE_WITH_OFFICIAL_THREAD_ID"  # Specific forum thread ID

# Replace with your desired storage location
HUNTERS_STORAGE_PATH = "REPLACE_WITH_STORAGE_PATH"
RANGES_HISTORY_FILE = os.path.join(HUNTERS_STORAGE_PATH, "ranges_history.json")
LAST_UPDATE_FILE = os.path.join(HUNTERS_STORAGE_PATH, "last_update_id.txt")


# =============================================================================
# TELEGRAM API FUNCTIONS
# =============================================================================
def get_updates(offset=None, timeout=2):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=timeout+5)
        r.raise_for_status()
        data = r.json()
        if not data["ok"]:
            print(f"getUpdates ok=False: {data}")
            return []
        return data.get("result", [])
    except Exception as e:
        print(f"Error in get_updates: {e}")
        return []


def send_message(chat_id, text, thread_id=None):
    """
    Sends a text message to a Telegram chat.
    If thread_id is provided, sends the message in the specific forum thread.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if thread_id is not None:
        payload["message_thread_id"] = thread_id

    try:
        r = requests.post(url, data=payload, timeout=2)
        r.raise_for_status()
    except Exception as e:
        print(f"Error in send_message: {e}")


def send_photo(chat_id, photo_path, caption="", thread_id=None):
    """
    Sends a photo to a Telegram chat.
    If thread_id is provided, sends the photo in the specific forum thread.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as img:
            payload = {
                "chat_id": chat_id,
                "caption": caption
            }
            if thread_id is not None:
                payload["message_thread_id"] = thread_id

            files = {"photo": img}
            r = requests.post(url, data=payload, files=files, timeout=30)
            r.raise_for_status()
    except Exception as e:
        print(f"Error in send_photo: {e}")


# =============================================================================
# LOAD AND PLOT DATA
# =============================================================================
def load_ranges_history():
    if not os.path.exists(RANGES_HISTORY_FILE):
        print(f"{RANGES_HISTORY_FILE} does not exist.")
        return {}
    try:
        with open(RANGES_HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("data", {})
    except Exception as e:
        print(f"Error loading {RANGES_HISTORY_FILE}: {e}")
        return {}


def calculate_overall_avg_speed(all_data, thirty_days_ago_ts):
    """
    Calculates the average speed across all users for the last 30 days,
    excluding speeds <= 1.
    Returns the overall average speed and the number of contributing users.
    """
    total_speed = 0
    count = 0
    contributing_users = set()
    for user, entries in all_data.items():
        user_contributed = False
        for e in entries:
            if len(e) != 3:
                print(f"Invalid entry for user {user}: {e}")
                continue
            ts, r, s = e
            if not isinstance(ts, (int, float)) or not isinstance(r, int) or not isinstance(s, (int, float)):
                print(f"Incorrect data types for user {user}: {e}")
                continue
            if s <= 1:
                continue
            if ts >= thirty_days_ago_ts:
                total_speed += s
                count += 1
                user_contributed = True
        if user_contributed:
            contributing_users.add(user)
    return (total_speed / count) if count > 0 else 0, len(contributing_users)


def calculate_daily_overall_avg_speed(all_data, start_date, end_date):
    """
    Calculates the daily overall average speed across all users for the given date range.
    Returns a list of daily average speeds.
    """
    daily_speed = defaultdict(list)
    for user, entries in all_data.items():
        for e in entries:
            ts, r, s = e
            entry_date = datetime.fromtimestamp(ts).date()
            if start_date <= entry_date <= end_date and s > 1:
                daily_speed[entry_date].append(s)

    daily_avg_speed = []
    date_range = [start_date + timedelta(days=i) for i in range(30)]
    for date in date_range:
        speeds = daily_speed.get(date, [])
        avg = sum(speeds) / len(speeds) if speeds else 0
        daily_avg_speed.append(avg)

    return daily_avg_speed


def moving_average(data, window_size=7):
    """Calculates the moving average with the specified window size."""
    if len(data) < window_size:
        return np.full(len(data), np.nan)
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')


def format_full_number(x, pos):
    """Formatter to display full numbers without abbreviations."""
    return f'{int(x)}'


def calculate_daily_ranges(entries, start_date, end_date):
    """
    Calculates daily ranges by computing the difference between the first and last 'r' of each day.
    """
    daily_first_r = {}
    daily_last_r = {}

    # Sort entries by timestamp
    sorted_entries = sorted(entries, key=lambda x: x[0])

    for e in sorted_entries:
        ts, r, s = e
        entry_date = datetime.fromtimestamp(ts).date()
        if not (start_date <= entry_date <= end_date):
            continue

        if entry_date not in daily_first_r:
            daily_first_r[entry_date] = r
        daily_last_r[entry_date] = r

    daily_ranges = {}
    for date in daily_first_r:
        daily_ranges[date] = daily_last_r[date] - daily_first_r[date]

    return daily_ranges


def plot_user_stats(username, entries, overall_avg_speed, overall_user_count, daily_overall_avg_speed):
    """
    Plots the user's speed as a line chart and "Average Speed" as a moving average line.
    Also plots ranges as a bar chart with a moving average.
    Includes the number of contributing users in the legend title.
    Ensures each day within the last 30 days is represented on the x-axis.
    """
    if not entries:
        return None

    # Sort entries by timestamp
    entries = sorted(entries, key=lambda x: x[0])

    # Define the time interval for the last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)
    date_range = [start_date + timedelta(days=i) for i in range(30)]

    # Initialize dictionaries for daily data
    daily_speed = defaultdict(list)
    daily_ranges_calculated = calculate_daily_ranges(entries, start_date, end_date)

    for e in entries:
        ts, r, s = e
        entry_date = datetime.fromtimestamp(ts).date()
        if start_date <= entry_date <= end_date:
            if s > 1:
                daily_speed[entry_date].append(s)

    # Calculate daily average speed
    avg_speed_per_day = []
    for date in date_range:
        speeds = daily_speed.get(date, [])
        avg = sum(speeds) / len(speeds) if speeds else 0
        avg_speed_per_day.append(avg)

    # Calculate daily total ranges
    total_ranges_per_day = [daily_ranges_calculated.get(date, 0) for date in date_range]

    # Calculate moving average for ranges
    ranges_moving_avg = moving_average(total_ranges_per_day, window_size=7)
    ranges_moving_avg = np.concatenate((
        np.full(len(total_ranges_per_day) - len(ranges_moving_avg), np.nan),
        ranges_moving_avg
    ))

    # Calculate moving average for overall average speed
    overall_moving_avg = moving_average(daily_overall_avg_speed, window_size=7)
    overall_moving_avg = np.concatenate((
        np.full(len(daily_overall_avg_speed) - len(overall_moving_avg), np.nan),
        overall_moving_avg
    ))

    times = [datetime.combine(date, datetime.min.time()) for date in date_range]

    plt.figure(figsize=(15, 14), dpi=150)

    # Subplot 1: Speed (user + overall avg)
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(
        times,
        avg_speed_per_day,
        color="blue",
        linestyle='-',
        linewidth=2,
        label="Your Speed (BK/s)"
    )
    ax1.plot(
        times,
        overall_moving_avg,
        color="red",
        linewidth=2,
        linestyle='--',
        label="Overall Average Speed (7-Day MA)"
    )
    ax1.set_title(f"{username} - Speed (Last 30 Days)")
    ax1.set_ylabel("BK/s")
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator())
    ax1.legend(title=f"Contributing Users: {overall_user_count}")
    plt.setp(ax1.get_xticklabels(), visible=False)

    # Subplot 2: Ranges (bar + moving average)
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    bars = ax2.bar(
        times,
        total_ranges_per_day,
        color="green",
        label="Ranges"
    )
    ax2.plot(
        times,
        ranges_moving_avg,
        color="orange",
        linewidth=2,
        linestyle='-',
        label="7-Day Moving Average"
    )
    # Add labels to each bar
    for bar, range_value in zip(bars, total_ranges_per_day):
        height = bar.get_height()
        if height > 0:
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f'{range_value}',
                ha='center',
                va='bottom',
                fontsize=8,
                color='black',
                rotation=90
            )

    ax2.set_title(f"{username} - Ranges (Last 30 Days)")
    ax2.set_ylabel("Ranges")
    ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax2.xaxis.set_major_locator(mdates.DayLocator())
    ax2.tick_params(axis='x', rotation=90)
    ax2.legend()
    ax2.yaxis.set_major_formatter(FuncFormatter(format_full_number))

    plt.tight_layout()
    filename = f"/tmp/{username}_stats_{int(time.time())}.png"
    plt.savefig(filename)
    plt.close()
    return filename


# =============================================================================
# COMMAND HANDLING
# =============================================================================
def handle_stats_command(incoming_chat_id, full_user, data, incoming_thread_id=None):
    """
    Handles the /stats command.
    incoming_chat_id and incoming_thread_id are kept for compatibility.
    """
    short_user = full_user[:10].lower()
    found_key = None

    # Try to match user using startswith (case-insensitive)
    for k in data.keys():
        if k.lower().startswith(short_user):
            found_key = k
            break

    if not found_key:
        message = (
            f"Hello! We couldn't find the user '{full_user}'.\n"
            "Make sure you're using the exact username/nickname from the website."
        )
        send_message(OFFICIAL_CHAT_ID, message, thread_id=OFFICIAL_THREAD_ID)
        
        if (incoming_chat_id != OFFICIAL_CHAT_ID) or (incoming_thread_id != OFFICIAL_THREAD_ID):
            send_message(
                incoming_chat_id,
                "We couldn't find that user. See info posted in the official stats thread.",
                thread_id=incoming_thread_id
            )
        return

    entries = data[found_key]
    if not entries:
        send_message(OFFICIAL_CHAT_ID, f"No entries found for {found_key}", thread_id=OFFICIAL_THREAD_ID)
        
        if (incoming_chat_id != OFFICIAL_CHAT_ID) or (incoming_thread_id != OFFICIAL_THREAD_ID):
            send_message(
                incoming_chat_id,
                "No entries found",
                thread_id=incoming_thread_id
            )
        return

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)

    thirty_days_ago_ts = time.time() - (30 * 86400)
    overall_avg_speed, overall_user_count = calculate_overall_avg_speed(data, thirty_days_ago_ts)
    daily_overall_avg_speed = calculate_daily_overall_avg_speed(data, start_date, end_date)

    png_path = plot_user_stats(found_key, entries, overall_avg_speed, overall_user_count, daily_overall_avg_speed)
    if not png_path:
        send_message(OFFICIAL_CHAT_ID, f"No recent data (within 30 days) for {found_key}", thread_id=OFFICIAL_THREAD_ID)

        if (incoming_chat_id != OFFICIAL_CHAT_ID) or (incoming_thread_id != OFFICIAL_THREAD_ID):
            send_message(
                incoming_chat_id,
                "No recent data for that user. See info posted in the official stats thread.",
                thread_id=incoming_thread_id
            )
        return

    # Send the statistics to the OFFICIAL_THREAD
    send_photo(OFFICIAL_CHAT_ID, png_path, caption=f"Stats for {found_key} (Last 30 Days)", thread_id=OFFICIAL_THREAD_ID)

    if (incoming_chat_id != OFFICIAL_CHAT_ID) or (incoming_thread_id != OFFICIAL_THREAD_ID):
        send_message(
            incoming_chat_id,
            "Your stats have been posted in the official stats topic",
            thread_id=incoming_thread_id
        )


def handle_message(update, data):
    msg = update.get("message", {})
    text = msg.get("text", "")
    chat_id = msg.get("chat", {}).get("id")
    thread_id = msg.get("message_thread_id")

    if text.startswith("/stats"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(OFFICIAL_CHAT_ID, "Usage: /stats <username on website>", thread_id=OFFICIAL_THREAD_ID)
            
            if (chat_id != OFFICIAL_CHAT_ID) or (thread_id != OFFICIAL_THREAD_ID):
                send_message(
                    chat_id,
                    "Please provide a username",
                    thread_id=thread_id
                )
            return

        full_user = parts[1].strip()
        handle_stats_command(chat_id, full_user, data, thread_id)


# =============================================================================
# OFFSET HANDLING
# =============================================================================
def get_last_update_id():
    if not os.path.exists(LAST_UPDATE_FILE):
        return None
    try:
        with open(LAST_UPDATE_FILE, 'r') as f:
            return int(f.read().strip())
    except Exception as e:
        print(f"Error reading {LAST_UPDATE_FILE}: {e}")
        return None


def set_last_update_id(update_id):
    try:
        with open(LAST_UPDATE_FILE, 'w') as f:
            f.write(str(update_id))
    except Exception as e:
        print(f"Error writing to {LAST_UPDATE_FILE}: {e}")


# =============================================================================
# MAIN FUNCTION
# =============================================================================
def main():
    # Get the latest offset
    last_update_id = get_last_update_id()

    # Fetch new updates
    updates = get_updates(offset=last_update_id, timeout=30)

    if not updates:
        print("No new updates.")
        return

    # Load ranges history
    data = load_ranges_history()

    for upd in updates:
        update_id = upd.get("update_id")
        message = upd.get("message", {})

        # Check if message contains text; handle commands
        if "text" in message:
            handle_message(upd, data)

        # Update offset
        if update_id is not None:
            last_update_id = update_id + 1

    # Save latest offset
    set_last_update_id(last_update_id)

    # Example: Automatically post to a designated thread (optional)
    # send_message(OFFICIAL_CHAT_ID, "Automated greeting in specific thread", thread_id=OFFICIAL_THREAD_ID)


if __name__ == "__main__":
    main()
