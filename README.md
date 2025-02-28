# Hunters Stats Bot for Puzzle 67 (modifiable for other puzzles)

This repository contains a set of Python scripts that collect, analyze, and publish statistics from multiple mining pools (e.g., Hunters, TTD, and BTCPuzzle). In addition, there are Telegram bot scripts that either post daily summaries automatically or respond to user commands (on demand).

All scripts have been tested in a Windmill environment, which provides convenient scheduling, logging, and observation. However, they can be adapted to any standard Python environment.

---

## Table of Contents

1. [Overview](#overview)  
2. [File Descriptions](#file-descriptions)  
   - [1. `BTCPuzzle-Collector.py`](#1-btcpuzzle-collectorpy)  
   - [2. `Hunters-collector.py`](#2-hunters-collectorpy)  
   - [3. `TTD-Collector.py`](#3-ttd-collectorpy)  
   - [4. `Telegram-push-stats_daily.py`](#4-telegram-push-stats_dailypy)  
   - [5. `Telegram-send-user-stats_on_demand.py`](#5-telegram-send-user-stats_on_demandpy)  
3. [Configuration & Setup](#configuration--setup)  
4. [Running the Scripts](#running-the-scripts)  
5. [Windmill Environment Notes](#windmill-environment-notes)  
6. [License](#license)

---

## Overview

- **Collectors** (BTCPuzzle-Collector, Hunters-collector, TTD-Collector)  
  Each of these scripts fetches data from its respective source (completion percentage, pool speed, user ranges, etc.) and saves it into JSON files for later reference.

- **Telegram Bot Scripts**  
  - One script (`Telegram-push-stats_daily.py`) automatically posts daily stats and graphs (e.g., daily heroes, progress, speeds) to a Telegram group or topic.  
  - Another script (`Telegram-send-user-stats_on_demand.py`) responds to user commands (like `/stats <username>`) and posts user-specific graphs or data in a specified thread.

---

## File Descriptions

### 1. `BTCPuzzle-Collector.py`
**Purpose**  
- Fetches data from **btcpuzzle.info/puzzle67** to extract the current completion percentage and speed.  
- Stores these values in JSON files (e.g., `BTCPUZZLE_completed.json`, `BTCPUZZLE_speed.json`).

**Key Points**  
- Update the URL (`BTCPUZZLE_URL`) if it ever changes.  
- Replace `HUNTERS_STORAGE_PATH` with a path that suits your environment.  
- Make sure to keep the file paths (`BTCPUZZLE_completed.json` and `BTCPUZZLE_speed.json`) consistent with any other scripts that depend on them.

**How to Run**  
```bash
python BTCPuzzle-Collector.py
```  

---

### 2. `Hunters-collector.py`
**Purpose**  
- Logs into and scrapes the **Hunters** dashboard to obtain statistics such as completion percentage, pool speed, or user-submitted ranges.  
- Stores data in JSON files (e.g., `previous_completed.json`, `previous_speed.json`, `ranges_history.json`, etc.).

**Key Points**  
- Check for placeholders like `USERNAME`, `PASSWORD` and replace them with valid credentials.  
- Update the `HUNTERS_STORAGE_PATH` for storing JSON files.  
- This script create and/or update files `ranges_history.json` and `total_ranges.json`. If you rename them, also update references in the Telegram scripts.

**How to Run**  
```bash
python Hunters-collector.py
```

---

### 3. `TTD-Collector.py`
**Purpose**  
- Logs into **TTD** (e.g., `ttdsales.com/67bit`) to extract “Percentage completed” and “BK/s” speed.  
- Saves this data in JSON format (e.g., `TTD_minimal_completed.json` and `TTD_minimal_speed.json`).

**Key Points**  
- Replace any placeholder credentials (`TTD_USERNAME`, `TTD_PASSWORD`) with the real ones.  
- Confirm or adjust the JSON filenames if needed. If the Telegram scripts rely on these filenames, ensure they match exactly.

**How to Run**  
```bash
python TTD-Collector.py
```

---

### 4. `Telegram-push-stats_daily.py`
**Purpose**  
- A Telegram bot script that automatically posts a summary of daily stats, progress, milestones, and graphs to your Telegram group/topic.  
- Fetches data from the JSON files created by the three Collector scripts.

**Key Points**  
- Configure `BOT_TOKEN`, `CHAT_ID`, and `MESSAGE_THREAD_ID` with valid Telegram credentials for group and thread.  
- Paths to JSON files (e.g., `previous_completed.json`, `TTD_minimal_speed.json`) must match the ones used by your collector scripts.  
- If you’re using Windmill or Cron, schedule this script to run daily at a fixed time.

**How to Run**  
```bash
python Telegram-push-stats_daily.py
```
*(Optionally run in a loop or via a scheduling mechanism.)*

---

### 5. `Telegram-send-user-stats_on_demand.py`
**Purpose**  
- Another Telegram bot script that listens for user commands like `/stats <username>`.  
- When triggered, it generates user-specific graphs (daily speed, range progress, etc.) and sends them in the specified thread.

**Key Points**  
- Also requires valid `BOT_TOKEN`, `CHAT_ID`, and `MESSAGE_THREAD_ID`.  
- Must be running continuously or triggered in short intervals to detect new messages (via `getUpdates` or Telegram webhooks).  
- Relies on JSON data from the collectors (e.g., `ranges_history.json`, `previous_speed.json`, etc.). Make sure the paths line up.

**How to Run**  
```bash
python Telegram-send-user-stats_on_demand.py
```
*(Keep it running or schedule it so it can catch and respond to commands.)*

---

## Configuration & Setup

1. **Python Requirements**  
   - Python 3.7+ recommended.  
   - Libraries: `requests`, `beautifulsoup4`, `matplotlib`, `numpy`, `pytz`, `json`  
  
2. **Credentials & Environment Variables**  
   - **Telegram**:
     - `BOT_TOKEN`: Your Telegram bot token (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v...`).  
     - `CHAT_ID`: The ID of the group or channel where you want to post.  
     - `MESSAGE_THREAD_ID`: If using forum topics, this is the specific thread ID.  
   - **Login Credentials**:
     - For TTD or Hunters, replace placeholders (`USERNAME`, `PASSWORD`) with valid credentials.
   - **Paths**:
     - Ensure the `HUNTERS_STORAGE_PATH` is correct.  
     - Match JSON filenames in all scripts so they read from and write to the same files.

3. **File Paths**  
   - If you rename JSON files (e.g., `TTD_minimal_speed.json` → `TTD_speed.json`), update all references in the scripts and the Telegram bots accordingly.

---

## Running the Scripts

1. **Manual Execution**  
   - You can run each collector script on demand:
     ```bash
     python BTCPuzzle-Collector.py
     python Hunters-collector.py
     python TTD-Collector.py
     ```
   - Then run the Telegram scripts as needed:
     ```bash
     python Telegram-push-stats_daily.py
     python Telegram-send-user-stats_on_demand.py
     ```

2. **Automated Scheduling**  
   - **Windmill**: You can create flows to schedule each collector script at a specific interval or time, and also schedule the “push daily stats” script once per day.  
   - **Cron**: Example cron jobs:
  - Run the collector scripts every 10 minutes:
    ```cron
    */10 * * * * /usr/bin/python /path/to/BTCPuzzle-Collector.py
    */10 * * * * /usr/bin/python /path/to/Hunters-collector.py
    */10 * * * * /usr/bin/python /path/to/TTD-Collector.py
    ```
  - Run the Telegram-push-stats_daily.py script once a day:
    ```cron
    0 8 * * * /usr/bin/python /path/to/Telegram-push-stats_daily.py
    ```
    *(This example runs the script daily at 08:00. Adjust the time as needed.)*
   - For the “on demand” bot, consider running it continuously (or in short intervals) so it can respond to commands.

---

## Windmill Environment Notes

- Windmill is a great platform for scheduling these scripts and visually monitoring logs.  
- Set up each collector script as a “flow” or “task” that runs periodically.  
- For the daily push stats script, you can schedule a single daily task.  
- For the on-demand Telegram script, you may let it run continuously or set short-interval triggers (though continuous is usually preferred so it catches commands quickly).

---

## License

Mozilla Public License 2.0

---

Questions or improvements?  
Feel free to open an issue or submit a pull request! Happy puzzle-mining and analyzing stats :)
