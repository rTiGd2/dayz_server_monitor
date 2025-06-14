#!/bin/bash

# DayZ Server Monitor Bootstrap Build Script

echo "⚙️ Creating project skeleton..."

# Main structure
mkdir -p dayz_server_monitor/{modes,locales/en_US,locales/en_UK,data,logs,output}

cd dayz_server_monitor

# Create core module files
touch monitor.py config_loader.py logger.py templates.py output_handler.py
touch server_query.py steam_api.py changelog_fetcher.py discord_notifier.py
touch mod_checker.py

# Create mode files
touch modes/serial_mode.py modes/threaded_mode.py modes/async_mode.py

# Create templates for en_US
echo "- New mod detected: {title}" > locales/en_US/mod_new.txt
echo "- UPDATED: {title} ({timestamp} UTC)" > locales/en_US/mod_updated.txt
echo "- REMOVED: {title}" > locales/en_US/mod_removed.txt
echo "No mod changes detected." > locales/en_US/no_changes.txt
echo "Fatal error occurred: {error}" > locales/en_US/fatal_error.txt

# Create templates for en_UK
echo "- New mod spotted: {title}" > locales/en_UK/mod_new.txt
echo "- UPDATED: {title} (on {timestamp} UTC)" > locales/en_UK/mod_updated.txt
echo "- REMOVED: {title}" > locales/en_UK/mod_removed.txt
echo "No changes detected to mods." > locales/en_UK/no_changes.txt
echo "A fatal error has occurred: {error}" > locales/en_UK/fatal_error.txt

# Default requirements.txt
cat <<EOF > requirements.txt
git+https://github.com/Yepoleb/dayzquery.git
git+https://github.com/Yepoleb/python-a2s.git
requests==2.31.0
beautifulsoup4==4.12.3
pyyaml==6.0.1
discord.py==2.3.2
aiohttp==3.9.3
EOF

# Create empty config.yaml for user to fill
cat <<EOF > config.yaml
server:
  ip: "your.server.ip"
  port: 2303

reboot:
  base_time: "00:00"
  interval_minutes: 180

locale: "en_US"

logging:
  enabled: true
  file: "logs/monitor.log"

output:
  to_console: true
  to_file: true
  to_discord: true
  file_path: "output/last_run.txt"
  show_removed_mods: true
  silent_on_no_changes: false
  show_island: true
  show_platform: true
  show_dedicated: true
  show_mod_count: true
  show_next_reboot: true

mod_checking_enabled: true
mod_check_mode: async   # serial | threaded | async

steam:
  api_key: "your_steam_api_key"

discord:
  enabled: true
  token: "YOUR_DISCORD_BOT_TOKEN"
  channel_id: 123456789012345678
EOF

echo "✅ DayZ Server Monitor bootstrap complete."