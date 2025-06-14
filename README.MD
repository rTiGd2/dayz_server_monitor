# DayZ Server Mod Monitor

---

## 🎯 Overview

A simple DayZ server mod monitoring system.

---

## TODO

- This file looks like a 5 year old wrote it, needs work
- Some display toggle functionality not implemented (the thought is there, somewhat)
- Actually test (and debug, and pray for luck) the Discord BOT
-- There are many thousands of Discord BOTS, you're better off using one of those!
- Perhaps comment some code (and complete the comments already added
- Stop doing initial commits at 5am, after 3 days awake!
- Add functionality to create a Global Message XML to warn of upcoming mod update(s)
- Fully integrate ALL text output as i18n (some errors still hardcoded!)
- ReLearn Python, and the changes in the past 5 years since I last used it
- Get Sleep
- Get a Job
- Touch Grass and Make Friends

---

## 🚀 Key Features

- ✅ Queries DayZ server directly (using dayzquery)
- ✅ Detects installed mods, version changes, new mods, and removed mods
- ✅ Steam Workshop version checks
- ✅ Changelog fetching via Steam scraping
- ✅ Discord notifications
- ✅ i18n translation system (fully localizable)
- ✅ Multiple concurrency modes (serial / threaded / async)
- ✅ State persistence across runs
- ✅ Fully observable with logs & performance tracking
- ✅ Fully automated unit test suite

---

## 🗂 Project Structure
dayz_mod_monitor_rc9/
├── monitor.py
├── config_loader.py
├── logger.py
├── output_handler.py
├── server_query.py
├── steam_api.py
├── changelog_fetcher.py
├── discord_notifier.py
├── state_manager.py
├── mod_checker.py
│
├── modes/
│ ├── serial_mode.py
│ ├── threaded_mode.py
│ └── async_mode.py
│
├── locales/
│ ├── en_US/
│ └── en_UK/
│
├── data/
├── logs/
├── output/
│
├── tests/
│ ├── test_server_connectivity.py
│ ├── test_mod_update_detection.py
│ └── test_server_unreachable.py
│
├── rc9_bootstrap.sh
├── requirements.txt
├── README.md
├── init_git_repo.sh
├── git_commit_helper.sh
└── git_checkout_helper.sh


---

## 🚀 Installation

### 1️⃣ Clone your repository (or generate files using dsm_bootstrap.sh)

### 2️⃣ Create virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
3️⃣ Install dependencies:
bash
Copy code
pip install -r requirements.txt
⚙️ Configuration
Edit your config.yaml file.

yaml
Copy code
server:
  ip: "your.server.ip"
  port: 2303

reboot:
  base_time: "00:00"
  interval_minutes: 240

locale: "en_US"

logging:
  enabled: true
  file: "logs/monitor.log"

output:
  to_console: true
  to_file: true
  to_discord: false
  file_path: "output/last_run.txt"
  show_removed_mods: true
  silent_on_no_changes: false
  show_island: true
  show_platform: true
  show_dedicated: true
  show_mod_count: true
  show_next_reboot: true

mod_checking_enabled: true
mod_check_mode: async  # serial | threaded | async

steam:
  api_key: "your_steam_api_key"

discord:
  enabled: false
  token: "YOUR_DISCORD_BOT_TOKEN"
  channel_id: 123456789012345678
🔑 Steam API Key
Get your key from: https://steamcommunity.com/dev/apikey
🤖 Discord Bot Setup
Create a Discord bot at: https://discord.com/developers/applications
Enable Message Content Intent
Invite bot to server with required permissions
Get your channel ID by enabling Developer Mode in Discord
🖥 Supported Modes
Mode	Config	Speed
Serial	serial	Slowest
Threaded	threaded	Recommended
Async	async	Fastest
🚀 Running the Monitor
bash
Copy code
python monitor.py
✅ Fully self-contained.

✅ Performance is logged automatically.

🔬 Running Unit Tests
1️⃣ From inside your virtual environment:

bash
Copy code
python -m unittest discover tests
2️⃣ ✅ Tests include:

Server connectivity test
Mod update detection test
Server failure handling test
🚀 Performance Logging
After every run, you'll see log entries like:

2025-06-14 10:32:01 - INFO - Mod check completed in 7.91 seconds using mode 'threaded'
2025-06-14 10:32:01 - INFO - Recent Performance Summary (last 20 runs):
2025-06-14 10:32:01 - INFO - Mode: serial | Avg: 25.38 sec over 5 runs
2025-06-14 10:32:01 - INFO - Mode: threaded | Avg: 7.92 sec over 8 runs
2025-06-14 10:32:01 - INFO - Mode: async | Avg: 3.27 sec over 7 runs

---

## 📄 License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)**.

- ✅ You are free to use, modify, and redistribute this code for non-commercial purposes.
- ✅ Commercial use requires prior written permission from the author.

Full license text is provided in the `LICENSE` file.

For commercial licensing requests or legal inquiries, please contact:

**Author:** Tig Campbell-Moore  
**Email:** firstname[at]surname[dot]com

License URL: [https://creativecommons.org/licenses/by-nc/4.0/](https://creativecommons.org/licenses/by-nc/4.0/)

---# DayZ_Server_Monitor
