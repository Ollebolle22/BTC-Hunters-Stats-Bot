#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 Emil Norrhage. All rights reserved.
#
# This file is part of Hunters Stats Bot.
#
# Licensed under the Mozilla Public License 2.0 (MPL-2.0); you may use, modify, and distribute
# this file freely as long as you comply with the terms of the MPL-2.0.
# You can obtain a copy of the License at:
# http://mozilla.org/MPL/2.0/.
#
# Author: Emil Norrhage <emil@norrhage.se>
#
# I kindly grant permission to anyone to use these files as they wish.



import json
import time
import os
import requests
from datetime import datetime, timedelta
import random
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import logging
import math

# Define the Stockholm timezone
STOCKHOLM = pytz.timezone('Europe/Stockholm')

# Hardcoded BOT_TOKEN and CHAT_ID (replace with your actual values or environment variables)
BOT_TOKEN = 'REPLACE_WITH_BOT_TOKEN'  # Replace with your actual BOT_TOKEN
CHAT_ID = 'REPLACE_WITH_CHAT_ID'       # Replace with your actual CHAT_ID
MESSAGE_THREAD_ID = 'REPLACE_WITH_MESSAGE_THREAD_ID'  # Specific thread ID

# Define file paths
HUNTERS_STORAGE_PATH = 'REPLACE_WITH_STORAGE_PATH'
PREVIOUS_COMPLETED_FILE = os.path.join(HUNTERS_STORAGE_PATH, 'previous_completed.json')
PREVIOUS_SPEED_FILE = os.path.join(HUNTERS_STORAGE_PATH, 'previous_speed.json')
RANGES_HISTORY_FILE = os.path.join(HUNTERS_STORAGE_PATH, 'ranges_history.json')
TOTAL_RANGES_FILE = os.path.join(HUNTERS_STORAGE_PATH, 'total_ranges.json')
ACHIEVED_MILESTONES_FILE = os.path.join(HUNTERS_STORAGE_PATH, 'achieved_milestones.json')

# === Pool lists (Hunters, TTD, BTCPuzzle) ===
POOLS_SPEED = [
    {
        "name": "Hunters",
        "speed_file": PREVIOUS_SPEED_FILE
    },
    {
        "name": "TTD",
        "speed_file": os.path.join(HUNTERS_STORAGE_PATH, 'TTD_minimal_speed.json')
    },
    {
        "name": "BTCPuzzle",
        "speed_file": os.path.join(HUNTERS_STORAGE_PATH, 'BTCPUZZLE_speed.json')
    }
]

POOLS_COMPLETION = [
    {
        "name": "Hunters",
        "completion_file": PREVIOUS_COMPLETED_FILE
    },
    {
        "name": "TTD",
        "completion_file": os.path.join(HUNTERS_STORAGE_PATH, 'TTD_minimal_completed.json')
    },
    {
        "name": "BTCPuzzle",
        "completion_file": os.path.join(HUNTERS_STORAGE_PATH, 'BTCPUZZLE_completed.json')
    }
]

# Define milestones (ordered from highest to lowest)
MILESTONES = [
    {"level": 1,  "name": "Diamond",   "threshold": 1000000, "emoji": "💎"},
    {"level": 2,  "name": "Pearl",     "threshold": 500001,  "emoji": "⚪️"},
    {"level": 3,  "name": "Sapphire",  "threshold": 250001,  "emoji": "🔹"},
    {"level": 4,  "name": "Ruby",      "threshold": 100001,  "emoji": "♦️"},
    {"level": 5,  "name": "Emerald",   "threshold": 50001,   "emoji": "🟢"},
    {"level": 6,  "name": "Platinum",  "threshold": 25001,   "emoji": "🪞"},
    {"level": 7,  "name": "Gold",      "threshold": 10001,   "emoji": "🥇"},
    {"level": 8,  "name": "Silver",    "threshold": 5001,    "emoji": "🥈"},
    {"level": 9,  "name": "Bronze",    "threshold": 1001,    "emoji": "🥉"},
    {"level": 10, "name": "Copper",    "threshold": 1,       "emoji": "🟤"},
]

APPROACHING_THRESHOLD_PERCENT = 0.10

# Total keys for Puzzle 67
TOTAL_KEYS = 7.3786976294838206463e19

# Comments dictionary, complete
COMMENTS = {
    "completion": [
        "Slow and steady progress!",
        "We're making consistent progress!",
        "Great progress, keep it up!",
        "We're getting closer!",
        "Every step counts!",
        "Keep pushing forward!",
        "Stable improvement!",
        "You're on the right track!",
        "Consistent effort pays off!",
        "Well done, keep it going!"
    ],
    "speed": [
        "Speed looks good!",
        "Excellent pace!",
        "Steady speed!",
        "Speed is top-notch!",
        "Maintaining a good tempo!",
        "Speed remains strong!",
        "Great momentum!",
        "Consistent speed!",
        "Speed stays stable!",
        "Perfect pace!"
    ],
    "speed_rocket": [
        "{user} is today's speed rocket!",
        "Watch out! {user} is zooming past everyone!",
        "Zoom! {user} is blasting to the top!",
        "{user} is soaring with incredible speed!",
        "Rocket speed achieved by {user}!",
        "{user} is flying high with top speed!",
        "Dazzling speed from {user}!",
        "{user} has ignited the speed barrier!",
        "Speedster {user} is unstoppable!",
        "{user} is breaking speed records today!"
    ],
    "milestones": {
        "Diamond": [
            "Amazing {user}! You've reached {milestone} ranges! {emoji}",
            "{user} has achieved the Diamond milestone with {milestone} ranges! 💎",
            "Outstanding work, {user}! {milestone} ranges reached! 💎",
            "{user} shines bright with {milestone} ranges! 💎",
            "Congrats {user}! {milestone} ranges achieved! 💎"
        ],
        "Pearl": [
            "Great job, {user}! You've reached {milestone} ranges! ⚪️",
            "{user} has hit the Pearl milestone with {milestone} ranges! ⚪️",
            "Well done, {user}! {milestone} ranges achieved! ⚪️",
            "{user} is shining with {milestone} ranges! ⚪️",
            "Congrats {user}! {milestone} ranges accomplished! ⚪️"
        ],
        "Sapphire": [
            "Excellent work, {user}! {milestone} ranges reached! 🔹",
            "{user} has achieved the Sapphire milestone with {milestone} ranges! 🔹",
            "Great progress, {user}! {milestone} ranges achieved! 🔹",
            "{user} is sparkling with {milestone} ranges! 🔹",
            "Well done, {user}! {milestone} ranges accomplished! 🔹"
        ],
        "Ruby": [
            "Fantastic {user}! You've reached {milestone} ranges! ♦️",
            "{user} has achieved the Ruby milestone with {milestone} ranges! ♦️",
            "Great job, {user}! {milestone} ranges achieved! ♦️",
            "{user} is blazing with {milestone} ranges! ♦️",
            "Congrats {user}! {milestone} ranges accomplished! ♦️"
        ],
        "Emerald": [
            "Awesome {user}! You've reached {milestone} ranges! 🟢",
            "{user} has achieved the Emerald milestone with {milestone} ranges! 🟢",
            "Great work, {user}! {milestone} ranges achieved! 🟢",
            "{user} is thriving with {milestone} ranges! 🟢",
            "Well done, {user}! {milestone} ranges accomplished! 🟢"
        ],
        "Platinum": [
            "Impressive {user}! You've reached {milestone} ranges! 🪞",
            "{user} has achieved the Platinum milestone with {milestone} ranges! 🪞",
            "Great effort, {user}! {milestone} ranges achieved! 🪞",
            "{user} is shining with {milestone} ranges! 🪞",
            "Congrats {user}! {milestone} ranges accomplished! 🪞"
        ],
        "Gold": [
            "Outstanding {user}! You've reached {milestone} ranges! 🥇",
            "{user} has achieved the Gold milestone with {milestone} ranges! 🥇",
            "Great job, {user}! {milestone} ranges achieved! 🥇",
            "{user} is golden with {milestone} ranges! 🥇",
            "Well done, {user}! {milestone} ranges accomplished! 🥇"
        ],
        "Silver": [
            "Excellent {user}! You've reached {milestone} ranges! 🥈",
            "{user} has achieved the Silver milestone with {milestone} ranges! 🥈",
            "Great progress, {user}! {milestone} ranges achieved! 🥈",
            "{user} is shining silver with {milestone} ranges! 🥈",
            "Congrats {user}! {milestone} ranges accomplished! 🥈"
        ],
        "Bronze": [
            "Good job, {user}! You've reached {milestone} ranges! 🥉",
            "{user} has achieved the Bronze milestone with {milestone} ranges! 🥉",
            "Well done, {user}! {milestone} ranges achieved! 🥉",
            "{user} is bronze strong with {milestone} ranges! 🥉",
            "Congrats {user}! {milestone} ranges accomplished! 🥉"
        ],
        "Copper": [
            "Fantastic {user}! You've reached {milestone} ranges! 🟤",
            "{user} has reached the Copper milestone with {milestone} ranges! 🟤",
            "Great job, {user}! {milestone} ranges achieved! 🟤",
            "{user} is a true Copper achiever with {milestone} ranges! 🟤",
            "Well done, {user}! {milestone} ranges achieved! 🟤"
        ],
        "approaching": [
            "{user} is approaching the {milestone} milestone! Only {remaining} ranges left! 😮🙏",
            "Heads up! {user} is nearing the {milestone} milestone with {remaining} ranges left! 😮🙏",
            "Almost there! {user} needs only {remaining} more ranges to reach {milestone}! 😮🙏",
            "Keep it up, {user}! Only {remaining} ranges left to reach {milestone}! 😮🙏",
            "You're almost there, {user}! {remaining} ranges left to achieve {milestone}! 😮🙏"
        ]
    },
    "no_milestones": [
        "No new milestones today, but the journey continues!",
        "No records broken today, better luck tomorrow!",
        "Keep striving for greatness!",
        "Stay focused and keep going!",
        "No milestones achieved today, but progress is progress!",
        "Another day, another step forward!",
        "No milestones reached today, but you're doing great!",
        "Keep up the good work!",
        "No milestones achieved today, keep pushing!",
        "Progress is being made, keep it up!"
    ],
    "shooting_star": [
        "{user} is today's shooting star! 🌠",
        "Incredible! {user} is soaring to the stars and beyond!",
        "Wow! {user} shines brightly as today's shooting star! 🌠",
        "Fantastic speed! {user} is today's shooting star! 🌠",
        "Dazzling trail! {user} is today's shooting star! 🌠",
        "Shining bright! {user} is today's shooting star! 🌠",
        "Stellar performance by {user} as today's shooting star! 🌠",
        "Sky-high speed! {user} is today's shooting star! 🌠",
        "Dazzling speed! {user} is today's shooting star! 🌠",
        "Radiant performance! {user} is today's shooting star! 🌠"
    ]
}

GOAL_PERCENTAGE_INCREASE = 0.07  # 0.07% daily increase goal

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)

def log_debug(message):
    logging.debug(message)

def log_warning(message):
    logging.warning(message)

def set_emoji_font():
    emoji_font_path = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
    if os.path.exists(emoji_font_path):
        plt.rcParams['font.family'] = 'Noto Color Emoji'
        log_debug("Emoji font set to 'Noto Color Emoji'.")
    else:
        log_warning("Emoji font not found. Emojis may not display correctly.")

def send_text_to_telegram(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'message_thread_id': MESSAGE_THREAD_ID
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        log_debug("Text message sent successfully.")
    except requests.exceptions.RequestException as e:
        response_text = response.text if 'response' in locals() else 'No response received'
        log_warning(f"Failed to send message: {e}")
        log_warning(f"Response: {response_text}")

def send_photo_to_telegram(photo_path, caption=""):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
    try:
        with open(photo_path, 'rb') as photo:
            payload = {
                'chat_id': CHAT_ID,
                'caption': caption,
                'parse_mode': 'HTML',
                'message_thread_id': MESSAGE_THREAD_ID
            }
            files = {'photo': photo}
            response = requests.post(url, data=payload, files=files, timeout=10)
            response.raise_for_status()
        log_debug("Photo sent successfully.")
    except requests.exceptions.RequestException as e:
        response_text = response.text if 'response' in locals() else 'No response received'
        log_warning(f"Failed to send photo: {e}")
        log_warning(f"Response: {response_text}")
    except FileNotFoundError:
        log_warning(f"Photo file not found: {photo_path}")

def send_long_message_in_parts(full_message, max_length=4000):
    parts = []
    current_part = ""
    for line in full_message.split("\n"):
        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line
        else:
            if current_part:
                current_part += "\n" + line
            else:
                current_part = line
    if current_part:
        parts.append(current_part)
    for part in parts:
        send_text_to_telegram(part)

def random_comment(category, level=None):
    if category == "milestones" and level:
        return random.choice(COMMENTS["milestones"].get(level, ["No comment available."]))
    return random.choice(COMMENTS.get(category, ["No comment available."]))

def load_json_file(file_path, default):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        log_debug(f"{file_path} not found. Initializing with default values.")
        return default
    except json.JSONDecodeError as e:
        log_warning(f"JSON decode error in {file_path}: {e}")
        return default
    except Exception as e:
        log_warning(f"Unexpected error loading {file_path}: {e}")
        return default

def get_stockholm_midnight_timestamp(days_ago=0):
    now = datetime.now(STOCKHOLM)
    target_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)
    target_date_utc = target_date.astimezone(pytz.UTC)
    timestamp = target_date_utc.timestamp()
    log_debug(f"Timestamp for {days_ago} days ago midnight Stockholm: {timestamp} ({datetime.fromtimestamp(timestamp, tz=pytz.UTC)})")
    return timestamp

def safe_change(now_val, past_val):
    if past_val is None:
        return "No data available"
    else:
        change = now_val - past_val
        log_debug(f"Calculating change: Now={now_val}%, Past={past_val}%, Change={change}%")
        return f"{change:.4f}%"

def resample_history(history_list, interval_seconds=600, aggregation='last'):
    if not history_list:
        return []
    sorted_history = sorted(history_list, key=lambda x: x[0])
    resampled = []
    start_time = sorted_history[0][0]
    current_bin_start = start_time
    current_bin_end = current_bin_start + interval_seconds
    current_values = []
    for (t, v) in sorted_history:
        while t >= current_bin_end:
            if current_values:
                if aggregation == 'last':
                    resampled.append((current_bin_start, current_values[-1]))
                elif aggregation == 'avg':
                    resampled.append((current_bin_start, sum(current_values)/len(current_values)))
            else:
                resampled.append((current_bin_start, None))
            current_bin_start += interval_seconds
            current_bin_end += interval_seconds
            current_values = []
        current_values.append(v)
    if current_values:
        if aggregation == 'last':
            resampled.append((current_bin_start, current_values[-1]))
        elif aggregation == 'avg':
            resampled.append((current_bin_start, sum(current_values)/len(current_values)))
    resampled = [item for item in resampled if item[1] is not None]
    return resampled

def filter_old_speed_data(history_list, days):
    cutoff = time.time() - days * 86400
    filtered = [entry for entry in history_list if entry[0] >= cutoff]
    log_debug(f"Filtered {len(filtered)} speed entries from the last {days} days.")
    return filtered

def get_value_at_utc_midnight(history_list, days_ago=0):
    if not history_list:
        return None
    ts_target = get_stockholm_midnight_timestamp(days_ago)
    closest_val = None
    closest_diff = None
    for (t, val) in history_list:
        diff = abs(t - ts_target)
        if closest_diff is None or diff < closest_diff:
            closest_diff = diff
            closest_val = val
    return closest_val

def calculate_heroes(history_data, time_range):
    current_time = time.time()
    range_differences = []
    for user, data in history_data.items():
        user_data = [(t, r, s) for t, r, s in data if current_time - t <= time_range]
        if len(user_data) > 1:
            user_data.sort(key=lambda x: x[0])
            initial_ranges = user_data[0][1]
            latest_ranges  = user_data[-1][1]
            latest_speed   = user_data[-1][2]
            range_diff     = latest_ranges - initial_ranges
            range_differences.append((user, range_diff, latest_speed))
            log_debug(f"User: {user}, Range Difference: {range_diff}, Latest Speed: {latest_speed} BK/s")
    range_differences.sort(key=lambda x: x[1], reverse=True)
    log_debug(f"Calculated heroes: {range_differences}")
    return range_differences

def calculate_speed_rocket(history_data):
    current_time = time.time()
    best_user = None
    best_speed = -1
    for user, data in history_data.items():
        for (t, r, s) in data:
            if current_time - t <= 86400:
                if s > best_speed:
                    best_speed = s
                    best_user = user
    if best_user is not None:
        log_debug(f"Speed Rocket: {best_user} with speed {best_speed}")
        return best_user, best_speed
    log_debug("No Speed Rocket found today.")
    return None

def calculate_shooting_star(history_data):
    current_time = time.time()
    candidates = []
    for user, data in history_data.items():
        user_data = [(t, s) for t, r, s in data if current_time - t <= 86400]
        if len(user_data) < 2:
            continue
        user_data.sort(key=lambda x: x[0])
        initial_speed = user_data[0][1]
        if initial_speed < 50:
            continue
        total_time_120 = 0.0
        reached_120 = False
        for i in range(len(user_data)-1):
            t1, s1 = user_data[i]
            t2, s2 = user_data[i+1]
            avg_speed_interval = (s1 + s2) / 2
            delta_t = t2 - t1
            if avg_speed_interval >= 120:
                total_time_120 += delta_t
                reached_120 = True
        if reached_120 and total_time_120 >= 21600:  # >=6 hours
            final_speed = user_data[-1][1]
            candidates.append((user, final_speed, total_time_120))
    candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
    shooting_star = candidates[0] if candidates else None
    if shooting_star:
        log_debug(f"Shooting Star: {shooting_star}")
    else:
        log_debug("No Shooting Star found today.")
    return shooting_star

def load_achieved_milestones():
    if not os.path.exists(ACHIEVED_MILESTONES_FILE):
        return {}
    try:
        with open(ACHIEVED_MILESTONES_FILE, 'r') as file:
            data = json.load(file)
            for user in data:
                data[user] = set(data[user])
            log_debug(f"Loaded achieved milestones: {data}")
            return data
    except Exception as e:
        log_warning(f"Error loading {ACHIEVED_MILESTONES_FILE}: {e}")
        return {}

def save_achieved_milestones(achieved_milestones):
    try:
        serializable_data = {user: list(ms) for user, ms in achieved_milestones.items()}
        with open(ACHIEVED_MILESTONES_FILE, 'w') as file:
            json.dump(serializable_data, file)
            log_debug(f"Saved achieved milestones: {serializable_data}")
    except Exception as e:
        log_warning(f"Error writing to {ACHIEVED_MILESTONES_FILE}: {e}")

def check_approaching_milestones(user, total_ranges):
    approaching_messages = []
    for milestone in MILESTONES:
        level = milestone["name"]
        threshold = milestone["threshold"]
        if total_ranges < threshold:
            distance = threshold - total_ranges
            if distance <= (APPROACHING_THRESHOLD_PERCENT * threshold):
                remaining = distance
                comment = random_comment("milestones", level="approaching").format(
                    user=f"<b>{user}</b>",
                    milestone=level,
                    remaining=f"{remaining:,}"
                )
                approaching_messages.append(comment)
    log_debug(f"Approaching milestones for {user}: {approaching_messages}")
    return approaching_messages

def highest_milestone(total_ranges):
    for m in MILESTONES:
        if total_ranges >= m["threshold"]:
            return m["emoji"]
    return ""

def get_top_users(ranges_data, top_n=10):
    user_totals = []
    for user, data in ranges_data.get("data", {}).items():
        if not data:
            continue
        latest_ranges = data[-1][1]
        user_totals.append((user, latest_ranges))
    user_totals.sort(key=lambda x: x[1], reverse=True)
    top_users = user_totals[:top_n]
    log_debug(f"Top {top_n} users: {top_users}")
    return top_users

def clean_old_ranges(history_data, days=30):
    current_time = time.time()
    cutoff = current_time - (days * 86400)
    for user in history_data:
        before = len(history_data[user])
        history_data[user] = [entry for entry in history_data[user] if entry[0] >= cutoff]
        after = len(history_data[user])
        log_debug(f"Cleaned user {user}: before={before}, after={after}")

def plot_active_users_30days(ranges_data):
    days = 30
    day_counts = []
    day_labels = []

    for d in range(days, 0, -1):
        start_of_day = get_stockholm_midnight_timestamp(d)
        end_of_day = get_stockholm_midnight_timestamp(d-1)
        active_users = set()
        for user, data in ranges_data.get("data", {}).items():
            for (t, r, s) in data:
                if start_of_day <= t < end_of_day:
                    active_users.add(user)
                    break
        day_counts.append(len(active_users))
        date_obj = datetime.now(STOCKHOLM) - timedelta(days=d)
        day_labels.append(date_obj)
        log_debug(f"Day: {date_obj.strftime('%Y-%m-%d')}, Active Users: {len(active_users)}")

    img_path = os.path.join(HUNTERS_STORAGE_PATH, "active_users_30days.png")
    plt.figure(figsize=(20, 10))
    plt.plot(day_labels, day_counts, marker='o', linestyle='-', color='purple')
    plt.title("👥 Active Users per Day (Last 30 Days)")
    plt.xlabel("Day")
    plt.ylabel("Number of Active Users")
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=90)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    log_debug(f"Saved active users graph to {img_path}")
    return img_path

def get_last_value_of_each_day(history_list, days=30, current_val=None):
    if not history_list:
        return []
    history_list = sorted(history_list, key=lambda x: x[0])

    results = []
    for d in range(days):
        start_of_day = get_stockholm_midnight_timestamp(d)
        if d == 0:
            end_of_day = time.time()
        else:
            end_of_day = get_stockholm_midnight_timestamp(d-1)
        day_data = [(t, v) for (t, v) in history_list if start_of_day <= t < end_of_day]
        log_debug(f"Processing day {d} - {len(day_data)} data points found")
        if day_data:
            day_data.sort(key=lambda x: x[0])
            last_val = day_data[-1][1]
        elif d == 0 and current_val is not None:
            last_val = current_val
        else:
            last_val = 0
        date_str = (datetime.now(STOCKHOLM) - timedelta(days=d)).strftime('%Y-%m-%d')
        results.append((date_str, last_val))

    results.reverse()
    return results

def plot_daily_percentage_increase(completion_data):
    days = 30
    history = completion_data.get("history", [])
    if not history:
        log_warning("No completion history available.")
        return None

    completion_now = completion_data.get("current", 0)
    daily_values = get_last_value_of_each_day(history, days=days, current_val=completion_now)
    if len(daily_values) < 2:
        log_warning("Not enough data points to calculate daily increases.")
        return None

    log_debug(f"Plotting Days: {[day for day, val in daily_values]}")
    percentage_increases = []
    day_labels = []

    for i, (current_day, current_val) in enumerate(daily_values):
        if i == 0:
            inc = 0
        else:
            prev_day, prev_val = daily_values[i-1]
            inc = current_val - prev_val if prev_val != 0 else 0
        percentage_increases.append(inc)
        date_obj = datetime.strptime(current_day, '%Y-%m-%d').replace(tzinfo=STOCKHOLM)
        day_labels.append(date_obj)
        log_debug(f"Day: {current_day}, Percentage Increase: {inc:.4f}%")

    if len(percentage_increases) > 1 and percentage_increases[1] > GOAL_PERCENTAGE_INCREASE:
        log_debug("Removing the first percentage increase as it exceeds the goal.")
        percentage_increases.pop(1)
        day_labels.pop(1)

    img_path = os.path.join(HUNTERS_STORAGE_PATH, "completion_percentage_increase_30days.png")
    plt.figure(figsize=(20, 10))
    colors = ['green' if inc >= GOAL_PERCENTAGE_INCREASE else 'red' for inc in percentage_increases]
    bars = plt.bar(day_labels, percentage_increases, color=colors, edgecolor='black', alpha=0.7)

    plt.axhline(y=GOAL_PERCENTAGE_INCREASE, color='blue', linestyle='--', linewidth=1, label=f'Goal: {GOAL_PERCENTAGE_INCREASE}%')
    plt.axhline(y=0, color='black', linewidth=0.8)

    plt.title("📈 Daily Percentage Increase of Puzzle Completion (Last 30 Days)")
    plt.xlabel("Day")
    plt.ylabel("Percentage Increase (%)")
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=90)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()

    mn, mx = min(percentage_increases), max(percentage_increases)
    plt.ylim(0, max(mx + 0.05, GOAL_PERCENTAGE_INCREASE + 0.1))

    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.2f}%',
                     xy=(bar.get_x() + bar.get_width()/2, height),
                     xytext=(0, 3),
                     textcoords="offset points",
                     ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(img_path, dpi=300)
    plt.close()
    log_debug(f"Saved percentage increase graph to {img_path}")
    return img_path

def compute_sma(values, window=600):
    sma_values = []
    for i in range(len(values)):
        if i < window:
            subset = values[:i+1]
        else:
            subset = values[i-window+1 : i+1]
        avg = sum(subset) / len(subset)
        sma_values.append(avg)
    return sma_values

def plot_pool_speed(speed_data):
    hist = speed_data.get("history", [])
    if not hist or len(hist) < 2:
        log_warning("No pool_speed history available.")
        return None
    hist = [h for h in hist if len(h) == 2]
    if not hist:
        log_warning("No valid pool_speed history after filtering.")
        return None
    
    resampled_hist = resample_history(hist, interval_seconds=600, aggregation='last')
    if not resampled_hist:
        log_warning("No resampled pool_speed history available.")
        return None
    resampled_hist.sort(key=lambda x: x[0])

    times = [datetime.fromtimestamp(t, tz=STOCKHOLM) for t, _ in resampled_hist]
    values = [v for _, v in resampled_hist]

    sma_window = 600
    sma_values = compute_sma(values, window=sma_window)

    img_path = os.path.join(HUNTERS_STORAGE_PATH, "pool_speed.png")
    plt.figure(figsize=(15, 7))
    plt.plot(times, values, linestyle='-', color='blue', label='Pool Speed')
    plt.plot(times, sma_values, linestyle='--', color='red', label=f'SMA{sma_window}')
    plt.title("🏊‍♂️ Pool Speed Over Time (10-Min Intervals + SMA600)")
    plt.xlabel("Time")
    plt.ylabel("Speed (BKeys/s)")
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=90)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    log_debug(f"Saved pool speed graph (with SMA600) to {img_path}")
    return img_path

def plot_user_speed_graph(user, ranges_data, days=1):
    user_data = ranges_data.get("data", {}).get(user, [])
    if not user_data:
        log_warning(f"No data found for user {user}")
        return None
    now = time.time()
    cutoff = now - days * 86400
    filtered_data = [(t, s) for (t, r, s) in user_data if t >= cutoff]
    if not filtered_data:
        log_warning(f"No data for user {user} in the last {days} days.")
        return None

    filtered_data.sort(key=lambda x: x[0])
    temp = resample_history(filtered_data, interval_seconds=600, aggregation='last')
    if not temp:
        log_warning(f"No resampled data for user {user}")
        return None

    times = [datetime.fromtimestamp(t, tz=STOCKHOLM) for t, _ in temp]
    speeds = [v for _, v in temp]

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(times, speeds, color='blue')
    ax.set_title(f"{user} - Speed last {days} day(s)")
    ax.set_xlabel("Time")
    ax.set_ylabel("Speed (BKeys/s)")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.tight_layout()

    file_name = f"user_speed_{user}_{days}d.png"
    img_path = os.path.join(HUNTERS_STORAGE_PATH, file_name)
    plt.savefig(img_path, dpi=100)
    plt.close()
    return img_path

def plot_completion(completion_data):
    hist = completion_data.get("history", [])
    if not hist or len(hist) < 2:
        log_warning("No completion history available for plotting.")
        return None
    hist.sort(key=lambda x: x[0])
    resampled_hist = resample_history(hist, interval_seconds=3600, aggregation='last')
    if not resampled_hist:
        log_warning("No resampled completion history available.")
        return None
    resampled_hist.sort(key=lambda x: x[0])
    times = [datetime.fromtimestamp(t, tz=STOCKHOLM) for t, _ in resampled_hist]
    values = [v for _, v in resampled_hist]

    quantized_values = [round(val/0.1)*0.1 for val in values]

    img_path = os.path.join(HUNTERS_STORAGE_PATH, "puzzle_completion.png")
    plt.figure(figsize=(15, 7))
    plt.step(times, quantized_values, where='post', color='green')
    plt.title("🧩 Puzzle 67 Completion Over Time (Hourly Steps)")
    plt.xlabel("Time")
    plt.ylabel("Completion (%)")
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=90)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    log_debug(f"Saved puzzle completion graph to {img_path}")
    return img_path

def plot_all_pools_speed(pools, days=3):
    plt.figure(figsize=(15, 7))
    now_time = time.time()
    for pool in pools:
        data = load_json_file(pool["speed_file"], {"current": 0, "history": []})
        hist = data.get("history", [])
        hist = [h for h in hist if len(h) == 2 and (now_time - h[0]) <= days * 86400]
        if not hist:
            continue
        hist.sort(key=lambda x: x[0])
        resampled = resample_history(hist, interval_seconds=600, aggregation='last')
        if not resampled:
            continue
        resampled.sort(key=lambda x: x[0])
        times = [datetime.fromtimestamp(t, tz=STOCKHOLM) for t, _ in resampled]
        speeds = [v for _, v in resampled]
        plt.plot(times, speeds, label=pool["name"])
    plt.title(f"Speeds of All Pools (Last {days} Days)")
    plt.xlabel("Time")
    plt.ylabel("Speed (BKeys/s)")
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    img_path = os.path.join(HUNTERS_STORAGE_PATH, "all_pools_speed.png")
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    log_debug(f"Saved multi-pool speed graph to {img_path}")
    return img_path

def plot_all_pools_completion_pacman(pools, days=7):
    now_time = time.time()
    pool_names = []
    pool_values = []

    for pool in pools:
        data = load_json_file(pool["completion_file"], {"current": 0, "history": []})
        hist = data.get("history", [])
        if not hist:
            continue
        hist = [h for h in hist if (now_time - h[0]) <= days * 86400]
        if not hist:
            continue
        hist.sort(key=lambda x: x[0])
        resampled = resample_history(hist, interval_seconds=1800, aggregation='last')
        if not resampled:
            continue
        resampled.sort(key=lambda x: x[0])
        latest_val = resampled[-1][1] if resampled else 0
        pool_names.append(pool["name"])
        pool_values.append(latest_val)

    if not pool_names or not pool_values:
        log_warning("No multi-pool completion data available to plot.")
        return None

    img_path = os.path.join(HUNTERS_STORAGE_PATH, "all_pools_completion_pacman.png")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

    ax1.bar(pool_names, pool_values, color='skyblue', edgecolor='black')
    ax1.set_title("Multi-Pool Completion - Bar Chart")
    ax1.set_xlabel("Pools")
    ax1.set_ylabel("Completion (%)")
    ax1.set_ylim([0, 20])
    for i, val in enumerate(pool_values):
        ax1.text(i, val + 0.5, f"{val:.2f}%", ha='center', va='bottom', fontsize=9)

    explode = [0] * len(pool_names)
    colors = [None] * len(pool_names)
    mouth_angle = 5

    hunters_index = None
    for i, name in enumerate(pool_names):
        if name.lower() == "hunters":
            hunters_index = i
            break

    if hunters_index is not None:
        explode[hunters_index] = 0.03
        colors[hunters_index] = "yellow"

    wedges, texts, autotexts = ax2.pie(
        pool_values,
        labels=pool_names,
        autopct='%1.1f%%',
        startangle=90,
        explode=explode,
        colors=colors,
        wedgeprops={'edgecolor': 'black'}
    )
    ax2.set_title("Multi-Pool Completion - Pac-Man Edition")

    if hunters_index is not None:
        hunters_patch = wedges[hunters_index]
        original_theta1 = hunters_patch.theta1
        original_theta2 = hunters_patch.theta2
        hunters_patch.set_theta1(original_theta1 + mouth_angle)
        hunters_patch.set_theta2(original_theta2 - mouth_angle)
        hunters_patch.set_facecolor("yellow")
        center_angle_deg = (hunters_patch.theta1 + hunters_patch.theta2) / 2.0
        offset_deg = -25
        adjusted_angle_deg = center_angle_deg + offset_deg
        adjusted_angle_rad = math.radians(adjusted_angle_deg)
        r_frac = 0.75
        eye_x = r_frac * math.cos(adjusted_angle_rad)
        eye_y = r_frac * math.sin(adjusted_angle_rad)
        ax2.plot(eye_x, eye_y, marker='o', markersize=7, color='black', zorder=10)

    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    log_debug(f"Saved multi-pool completion with Pac-Man to {img_path}")
    return img_path

def estimate_completion_time(completion_data, target_percentage=50, data_points=5):
    hist = completion_data.get("history", [])
    log_debug(f"Completion History: {hist}")
    if len(hist) < 2:
        log_warning("Not enough data to estimate completion time.")
        return None
    hist.sort(key=lambda x: x[0])
    relevant_history = hist[-data_points:] if len(hist) >= data_points else hist
    log_debug(f"Relevant History for Estimation (last {len(relevant_history)} points): {relevant_history}")
    time_deltas = []
    percentage_deltas = []
    for i in range(1, len(relevant_history)):
        t_prev, v_prev = relevant_history[i-1]
        t_curr, v_curr = relevant_history[i]
        delta_t = t_curr - t_prev
        delta_v = v_curr - v_prev
        if delta_t <= 0:
            log_warning(f"Invalid time delta between points {i-1} and {i}. Skipping.")
            continue
        if delta_v <= 0:
            log_warning(f"No progress detected between points {i-1} and {i}. Skipping.")
            continue
        time_deltas.append(delta_t)
        percentage_deltas.append(delta_v)
        log_debug(f"Point {i-1} to {i}: Δt={delta_t} sec, Δv={delta_v}%")
    if not time_deltas or not percentage_deltas:
        log_warning("Insufficient positive progress data to estimate completion time.")
        return None
    average_rate = sum(percentage_deltas) / sum(time_deltas)
    log_debug(f"Average Rate: {average_rate} % per second")
    if average_rate <= 0:
        log_warning("Average rate is non-positive. Cannot estimate completion time.")
        return None
    target = target_percentage
    current = completion_data.get("current", 0)
    remaining = target - current
    log_debug(f"Target: {target}%, Current: {current}%, Remaining: {remaining}%")
    if remaining <= 0:
        log_debug("Target already reached or exceeded.")
        return None
    seconds_to_target = remaining / average_rate
    log_debug(f"Seconds to target: {seconds_to_target}")
    if seconds_to_target < 0:
        log_warning("Calculated seconds_to_target is negative. Cannot estimate completion time.")
        return None
    future_time = datetime.fromtimestamp(time.time() + seconds_to_target, tz=STOCKHOLM)
    log_debug(f"Estimated completion time to {target}%: {future_time}")
    return future_time

def get_average_speed_for_day(history_list, days_ago=0):
    if not history_list:
        return None
    start_of_day = get_stockholm_midnight_timestamp(days_ago)
    if days_ago == 0:
        end_of_day = time.time()
    else:
        end_of_day = get_stockholm_midnight_timestamp(days_ago-1)
    speeds_that_day = [v for (t, v) in history_list if start_of_day <= t < end_of_day]
    log_debug(f"Average speed calculation for days_ago={days_ago}: Speeds={speeds_that_day}")
    if speeds_that_day:
        avg_speed = sum(speeds_that_day) / len(speeds_that_day)
        log_debug(f"Average speed for days_ago={days_ago}: {avg_speed}")
        return avg_speed
    else:
        log_debug(f"No speed data for days_ago={days_ago}")
        return None

def main():
    set_emoji_font()

    # Load data
    completion_data = load_json_file(PREVIOUS_COMPLETED_FILE, {"current": 0, "history": []})
    speed_data = load_json_file(PREVIOUS_SPEED_FILE, {"current": 0, "history": []})
    ranges_data = load_json_file(RANGES_HISTORY_FILE, {"data": {}})
    total_ranges_data = load_json_file(TOTAL_RANGES_FILE, {"current": 0})
    log_debug("Data files loaded successfully.")

    # Load achieved milestones and clean old range entries
    achieved_milestones = load_achieved_milestones()
    clean_old_ranges(ranges_data.get("data", {}), days=30)

    # Update completion
    completion_now = completion_data.get("current", 0)
    current_time = time.time()
    completion_hist = completion_data.get("history", [])
    completion_hist.append((current_time, completion_now))
    completion_data["history"] = completion_hist
    log_debug(f"Updated completion history: {completion_hist}")

    # Get 30 days history
    last_30d_values = get_last_value_of_each_day(completion_hist, days=30, current_val=completion_now)
    if len(last_30d_values) >= 2:
        _, completion_yesterday = last_30d_values[-2]
    else:
        completion_yesterday = None

    daily_change_str = safe_change(completion_now, completion_yesterday)
    completion_week_ago = get_value_at_utc_midnight(completion_hist, 7)
    completion_month_ago = get_value_at_utc_midnight(completion_hist, 30)
    weekly_change_str = safe_change(completion_now, completion_week_ago)
    monthly_change_str = safe_change(completion_now, completion_month_ago)

    completion_future = estimate_completion_time(completion_data, target_percentage=50, data_points=5)

    # Save completion data
    completion_data["previous_yesterday"] = completion_data.get("yesterday", completion_now)
    completion_data["yesterday"] = completion_now
    try:
        with open(PREVIOUS_COMPLETED_FILE, 'w') as f:
            json.dump(completion_data, f)
            log_debug("Saved completion data successfully.")
    except Exception as e:
        log_warning(f"Failed to save completion data: {e}")

    # Get pool speed
    hist = speed_data.get("history", [])
    hist = [item for item in hist if len(item) == 2]
    if hist:
        hist.sort(key=lambda x: x[0])
        pool_speed = hist[-1][1]
    else:
        pool_speed = speed_data.get("current", 0)

    log_debug(f"Pool Speed: {pool_speed} BKeys/s")

    # Average speed today/yesterday
    average_speed_today = get_average_speed_for_day(speed_data.get("history", []), days_ago=0)
    average_speed_yesterday = get_average_speed_for_day(speed_data.get("history", []), days_ago=1)

    if average_speed_today is not None:
        speed_now = average_speed_today
    else:
        speed_now = pool_speed

    if average_speed_yesterday is not None and average_speed_yesterday != 0:
        speed_diff = ((speed_now - average_speed_yesterday) / average_speed_yesterday) * 100
        speed_diff_str = f"({speed_diff:.2f}% {'increase' if speed_diff >= 0 else 'decrease'} compared to yesterday)"
    else:
        speed_diff_str = "(No data available)"

    if pool_speed < 500:
        speed_emoji = "🐢"
    elif pool_speed < 1000:
        speed_emoji = "⚡"
    else:
        speed_emoji = "🚀🚀🚀"

    completion_comment = random_comment("completion")
    speed_comment = random_comment("speed")

    last_30d_speed = filter_old_speed_data(speed_data.get("history", []), days=30)
    if last_30d_speed:
        last_30d_speed = [x for x in last_30d_speed if isinstance(x[1], (int, float))]
        max_30d_speed = max(v for _, v in last_30d_speed) if last_30d_speed else 0
        avg_30d_speed = sum(v for _, v in last_30d_speed) / len(last_30d_speed) if last_30d_speed else 0
    else:
        max_30d_speed, avg_30d_speed = 0, 0

    # Milestones
    achieved_milestones_changed = False
    milestone_lines = []
    approaching_lines = []

    for user, data in ranges_data.get("data", {}).items():
        if not data:
            continue
        total_user_ranges = data[-1][1]
        user_ach = achieved_milestones.get(user, set())
        for milestone in MILESTONES:
            level = milestone["name"]
            threshold = milestone["threshold"]
            emoji = milestone["emoji"]
            if total_user_ranges >= threshold and threshold not in user_ach:
                msg = random_comment("milestones", level=level)
                msg = msg.format(user=f"<b>{user}</b>", milestone=f"{threshold:,}", emoji=emoji)
                milestone_lines.append(msg)
                user_ach.add(threshold)
                achieved_milestones_changed = True
        achieved_milestones[user] = user_ach

        am = check_approaching_milestones(user, total_user_ranges)
        approaching_lines.extend(am)

    total_pool_ranges = total_ranges_data.get("current", 0)
    today_str = datetime.now(STOCKHOLM).strftime('%A %B %d, %Y')

    #
    # 1) Build the message text
    #
    message = f"<b>🌟 BTC Hunters Stats 🌟</b>\n{today_str}\n\n"

    message += "<b>🧩 Puzzle 67 Completion:</b>\n"
    message += f"{completion_now:.4f}% - {completion_comment}\n"
    message += f"📈 <b>Change since yesterday:</b> {daily_change_str}\n"
    message += f"📅 <b>Change since last week:</b> {weekly_change_str}\n"
    message += f"📆 <b>Change since last month:</b> {monthly_change_str}\n"
    if completion_future:
        message += f"⏳ <b>Estimated 50% completion:</b> {completion_future.strftime('%Y-%m-%d %H:%M:%S')}\n"
    else:
        message += f"⏳ <b>Estimated 50% completion:</b> Not available\n"
    message += "\n"

    message += "<b>🏊‍♂️ Pool Speed:</b>\n"
    message += f"{pool_speed:.2f} BKeys/s {speed_emoji} {speed_comment} {speed_diff_str}\n\n"

    # Daily Heroes (Top 3)
    daily_heroes = calculate_heroes(ranges_data.get("data", {}), 86400)
    message += "<b>🏅 Daily Heroes (Top 3):</b>\n"
    if daily_heroes:
        top3_daily = daily_heroes[:3]
        for rank, (u, rng, spd) in enumerate(top3_daily, start=1):
            medal = {1:"🥇", 2:"🥈", 3:"🥉"}.get(rank, "⭐")
            message += f"{rank}. <b>{u}</b> - +{rng} ranges, {spd:.2f} BK/s {medal}\n"
        message += "\n<b>Incredible daily heroes!</b> Keep it up and drive the puzzle forward!\n"
    else:
        message += "🚫 No daily heroes...\n"
    message += "\n"

    # Speed Rocket
    speed_rocket = calculate_speed_rocket(ranges_data.get("data", {}))
    if speed_rocket:
        u, top_speed = speed_rocket
        srocket_msg = random_comment("speed_rocket").format(user=f"<b>{u}</b>")
        message += "<b>🚀 Speed Rocket:</b>\n"
        message += f"<b>{u}</b> achieved the highest speed today: {top_speed:.2f} BK/s!\n{srocket_msg}\n\n"
        all_time_best_speed = speed_data.get("all_time_best_speed", 0)
        if top_speed > all_time_best_speed:
            speed_data["all_time_best_speed"] = top_speed
            speed_data["all_time_best_speed_holder"] = u
            try:
                with open(PREVIOUS_SPEED_FILE, 'w') as sp:
                    json.dump(speed_data, sp)
                    log_debug(f"Updated all-time best speed to {top_speed:.2f} BK/s (holder: {u}).")
            except Exception as e:
                log_warning(f"Failed to save all-time best speed data: {e}")
    else:
        message += "<b>🚀 Speed Rocket:</b>\nNo speed rocket today...\n\n"

    # Shooting Star
    shooting_star = calculate_shooting_star(ranges_data.get("data", {}))
    if shooting_star:
        u, final_speed, total_time_120 = shooting_star
        star_msg = random_comment("shooting_star").format(user=f"<b>{u}</b>")
        message += "<b>💫 Shooting Star:</b>\n"
        message += f"<b>{u}</b> maintained >=120 BK/s for 6+ hours!\n{star_msg}\n\n"
    else:
        message += "<b>💫 Shooting Star:</b>\nNo shooting star today...\n\n"

    # Milestones
    message += "<b>🎯 Milestones Achieved (Last 24 Hours):</b>\n"
    if milestone_lines:
        for line in milestone_lines:
            message += f"✅ {line}\n"
        message += "\n"
    else:
        no_ms = random_comment("no_milestones")
        message += f"{no_ms}\n\n"

    # Approaching Milestones
    message += "<b>⚠️ Approaching Milestones:</b>\n"
    if approaching_lines:
        for i, line in enumerate(approaching_lines, start=1):
            message += f"{i}. {line}\n"
        message += "\n"
    else:
        message += "No approaching milestones today...\n\n"

    # Milestone Explanation
    message += "<b>📜 Milestone Explanation:</b>\n"
    for i, m in enumerate(MILESTONES):
        if m["name"] != "Diamond":
            if i == 0:
                nxt = None
            else:
                nxt = MILESTONES[i-1]
            if nxt:
                upper = nxt["threshold"] - 1
                message += f"• {m['name']} - {m['threshold']:,} to {upper:,} ranges {m['emoji']}\n"
            else:
                message += f"• {m['name']} - {m['threshold']:,} ranges {m['emoji']}\n"
        else:
            message += f"• {m['name']} - {m['threshold']:,}+ ranges {m['emoji']}\n"
    message += "\n"

    # Top 10 Users
    top10_users = get_top_users(ranges_data, top_n=10)
    if top10_users:
        message += "<b>🥇 Top 10 Users:</b>\n"
        for rank, (usr, tot_r) in enumerate(top10_users, start=1):
            emj = highest_milestone(tot_r)
            message += f"{rank}. <b>{usr}</b>{(' ' + emj if emj else '')} - {tot_r:,} ranges\n"
        message += "\n"
    else:
        message += "<b>🥇 Top 10 Users:</b>\n🚫 No data available.\n\n"

    message += "<b>📊 Global Statistics (Last 30 Days):</b>\n"
    message += f"• <b>Total Pool Ranges:</b> {total_pool_ranges:,}\n"
    message += f"• <b>30 Day Top Speed Spike:</b> {max_30d_speed:.2f} BKeys/s\n"
    message += f"• <b>Avg Speed (BKeys/s) over Last 30 Days:</b> {avg_30d_speed:.2f}\n\n"

    # All-time Top Speed
    all_time_best_speed = speed_data.get("all_time_best_speed", 0)
    all_time_best_holder = speed_data.get("all_time_best_speed_holder")
    if all_time_best_holder and all_time_best_speed > 0:
        message += f"<b>🏆 All-Time Top Speed:</b> {all_time_best_speed:.2f} BKeys/s by <b>{all_time_best_holder}</b>\n\n"

    # Send the text message in parts
    send_long_message_in_parts(message)

    # Save new milestones if any changes occurred
    if achieved_milestones_changed:
        save_achieved_milestones(achieved_milestones)

    #
    # ORDER OF GRAPH SENDING:
    #

    # (1) Pool Speed
    graph_path_speed = plot_pool_speed(speed_data)
    if graph_path_speed:
        send_photo_to_telegram(graph_path_speed, caption="🏊‍♂️ Pool Speed History (SMA600)")

    # (2) Puzzle 67 Completion History
    graph_path_completion = plot_completion(completion_data)
    if graph_path_completion:
        send_photo_to_telegram(graph_path_completion, caption="🧩 Puzzle 67 Completion History (Hourly Steps)")

    # (3) Daily Percentage Increase
    graph_path_percentage_increase = plot_daily_percentage_increase(completion_data)
    if graph_path_percentage_increase:
        send_photo_to_telegram(graph_path_percentage_increase, caption="📈 Daily Percentage Increase of Puzzle Completion (Last 30 Days)")

    # (4) Active Users
    graph_path_active = plot_active_users_30days(ranges_data)
    if graph_path_active:
        send_photo_to_telegram(graph_path_active, caption="👥 Active Users Over Last 30 Days")

    # (5) Multi-Pool Speed
    multi_speed_path = plot_all_pools_speed(POOLS_SPEED, days=7)
    if multi_speed_path:
        send_photo_to_telegram(multi_speed_path, caption="🌐 Multi-Pool Speed (Last 7 Days)")

    # (6) Small graphs for daily heroes (top 3)
    if daily_heroes:
        top3_daily_heroes = daily_heroes[:3]
        for rank, (user, _, _) in enumerate(top3_daily_heroes, start=1):
            gpath = plot_user_speed_graph(user, ranges_data, days=1)
            if gpath:
                send_photo_to_telegram(gpath, caption=f"Unstoppable Daily Hero {rank}: {user} (Last 24h)\nKeep it up!")
    
    # (7) Multi-Pool Completion (Pac-Man)
    multi_completion_path = plot_all_pools_completion_pacman(POOLS_COMPLETION, days=7)
    if multi_completion_path:
        send_photo_to_telegram(multi_completion_path, caption="🧩 Multi-Pool Completion")

if __name__ == "__main__":
    main()
