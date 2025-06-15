
# DayZ Server Mod Monitor

## WARNINGS/ISSUES

This is currently out of date, most of the information is correct but know the following

Discord integration has switched from BOT to Webhook (makes more sense) amd the example config.yaml in the project reflects this but this file does not.

Docker is a work in progress, with little progress. It still uses the old Discord bot method, so either fix this (and feel free to contribute) or wait for my lazy ass to get around to it

## 🎯 Overview

A robust, extensible system to monitor DayZ server mods, detect changes, and notify administrators via logs and Discord.

----------

## 🚀 Key Features

-   ✅ Queries live DayZ server (via  dayzquery)
-   ✅ Detects mod additions, removals, and updates
-   ✅ Pulls Steam Workshop metadata and changelogs
-   ✅ Sends summary messages to Discord (optional)
-   ✅ Full i18n localization support (template-driven)
-   ✅ Supports async, threaded, or serial concurrency
-   ✅ Detailed logging (with rotation & per-level files)
-   ✅ State tracking across runs
-   ✅ CLI and Docker support
-   ✅ Unit-tested and extensible

----------

## 🗂 Project Structure

DayZ_Server_Monitor/
├── monitor.py
├── cli.py
├── config_loader.py
├── logger.py
├── mod_checker.py
├── output_handler.py
├── server_query.py
├── state_manager.py
├── steam_api.py
├── templates.py
├── discord_notifyer.py
├── changelog_fetcher.py
│
├── modes/
│ ├── serial_mode.py
│ ├── threaded_mode.py
│ └── async_mode.py
│
├── locales/
│ └── en_UK/
│ ├── output/
│ ├── logging/
│ └── discord/
│
├── tests/
├── output/
├── logs/
├── data/
│
├── docker/
│ ├── Dockerfile.oneoff
│ ├── Dockerfile.cron
│ ├── entrypoint.sh
│ ├── crontab.template
│ └── secrets/
│ ├── discord_token
│ └── steam_api_key
│
├── config.yaml
├── requirements.txt
├── LICENSE
└── README.md

----------

## ⚙️ Configuration

Edit config.yaml:

    server:
       ip:  "your.server.ip"
       port:  2302
    reboot:
       base_time:  "00:00"
       interval_minutes:  240
    locale:  "en_UK"
    logging:
       enabled:  true
       level: DEBUG
       log_dir: logs
       files:
          debug: debug.log
          info: info.log
          error: error.log
          critical: critical.log
    output:
       to_console:  true
       to_file:  true
       to_discord:  true
       file_path:  "output/last_run.txt"
       show_removed_mods:  true
       silent_on_no_changes:  false
       show_island:  true
       show_platform:  true
       show_dedicated:  true
       show_mod_count:  true
       show_next_reboot:  true
    mod_checking_enabled:  true
    mod_check_mode: async # Options: async, threaded, serial
    threaded_mode:
       max_workers:  10
    steam:
       api_key:  "your_steam_api_key"
    discord:
       enabled:  true
       token:  "YOUR_DISCORD_BOT_TOKEN"
       channel_id:  123456789012345678`

----------

## 🔐 Secrets, Environment, and Config Resolution

This project supports multiple methods for passing sensitive data such as:

-   STEAM_API_KEY
-   DISCORD_TOKEN

They are resolved in the following priority:

Docker Secret > config.yaml > Environment Variable

----------

## 📁 Docker Secrets Setup

For sensitive values, mount secret files to /run/secrets/:

    echo  "your-discord-token"  > discord_token
    echo  "your-steam-api-key"  > steam_api_key
    docker run -d \\
      --secret source=discord_token,target=discord_token \\
        --secret source=steam_api_key,target=steam_api_key \\
          dayz_monitor_cron

Or with Docker Compose:

    services:
       dayzmonitor:
          image: dayz_monitor_cron
          secrets:
             - discord_token
             - steam_api_key
            environment:
               - CRON_SCHEDULE=*/10 * * * *

    secrets:
       discord_token:
          file: ./docker/secrets/discord_token
       steam_api_key:
          file: ./docker/secrets/steam_api_key

----------

## 🌍 Environment Variables

You can also provide these if secrets are not used:

    export  DISCORD_TOKEN="your-discord-token"
    export  STEAM_API_KEY="your-steam-api-key"
    python monitor.py

----------

## 🧪 Testing

Run all unit tests:

    python -m unittest discover tests

Simulated test cases include:

-   ✅ Server unreachable (via port override)
-   ✅ Mod update detection
-   ✅ Output generation
-   ✅ Template integrity

----------

## 🖥 Supported Modes

|Mode  | Config Value | Notes
|--|--|--|
|Serial  | serial |Slow but simple |
|Threaded |threaded | Fast, CPU-friendly|
|Async |async |Fastest, scalable |

----------

## 🤖 Discord Integration

1.  Create a bot at:  [https://discord.com/developers/applications](https://discord.com/developers/applications "https://discord.com/developers/applications")
2.  Enable  **Message Content Intent**
3.  Invite bot to your server
4.  Use Developer Mode to get the channel ID

----------

## 🐳 Docker Support

### One-Time Run

    docker build -f docker/Dockerfile.oneoff -t dayz_monitor .
    docker run --rm -v $PWD:/app dayz_monitor

### Cron-Enabled Image

This version includes a flexible schedule.

    docker build -f docker/Dockerfile.cron -t dayz_monitor_cron .
    docker run -d -e CRON_SCHEDULE="*/10 * * * *" dayz_monitor_cron

**Default:** */5 * * * * (every 5 minutes)

-   ✅ Only the frequency is user-configurable
-   ✅ The monitored command cannot be changed
-   ✅ Environment variable  CRON_SCHEDULE  is injected into a crontab template

----------

## 📝 Performance Logging

Performance logs written to data/performance_log.csv. Summary displayed after each run:

Mod check completed in 3.27 seconds using mode 'async'
Recent Performance Summary (last 20 runs):
Mode: serial | Avg: 25.38 sec
Mode: threaded | Avg: 7.92 sec
Mode: async | Avg: 3.27 sec

----------

## 📄 License

Licensed under **Creative Commons BY-NC 4.0**
Commercial use requires written permission.

More info: [https://creativecommons.org/licenses/by-nc/4.0/](https://creativecommons.org/licenses/by-nc/4.0/ "https://creativecommons.org/licenses/by-nc/4.0/")

**Author:** Tig Campbell-Moore
**Contact:** firstname[at]lastname[dot]com

----------
