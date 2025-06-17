# DayZ Server Monitor

Monitor, track, and report on DayZ servers—with advanced config, changelog reporting, multi-server support, and persistent tracking.

---

## Features

- **Multi-server support:** Run checks and reporting on multiple DayZ servers with a single tool.
- **Configuration merging:** Supports defaults, per-server overrides, and required fields using YAML and Pydantic validation.
- **Change tracking:** Persists mod state and server performance to disk for reliable change detection.
- **Changelog fetching:** Reports mod changelogs (with formatting, truncation, BBCode/HTML stripping, etc).
- **Flexible output:** Console, file, and Discord notification support, with robust template-based formatting and locale support.
- **Robust logging:** Rotating file logs, colored console logs, per-level file splitting, and configurable verbosity.
- **Performance logging:** Tracks and summarizes run duration and stats per server.
- **Localization:** Localized output via customizable templates.

---

## Quick Start

### 1. Install requirements

Python 3.8+ is required.

```sh
pip install -r requirements.txt
```

### 2. Configure servers

Edit YAML files in the `config/` directory:

- `monitor.yaml` — Top-level/global config (required)
- `config.defaults.yaml` — Default values applied to all servers (optional)
- `config.required.yaml` — Required fields with metadata (optional)
- `*.yaml` — One file per server, overrides global/defaults

### 3. Run the monitor

```sh
python -m monitor
```

---

## Docker Usage

You can run DayZ Server Monitor in a containerized environment using Docker.

### Clone the Repository

```sh
git clone https://github.com/rTiGd2/dayz_server_monitor.git
cd dayz_server_monitor
```

### Build the Docker image

```sh
docker build -f docker/Dockerfile -t dayz-server-monitor .
```

### Start the Container in the Background

```sh
docker run -d \
  --name dayz-server-monitor \
  -v "$(pwd)/config:/app/config" \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/output:/app/output" \
  -e CRON_SCHEDULE="*/5 * * * *" \
  dayz-server-monitor
```

- The `-d` flag runs the container in detached/background mode.
- Use `docker logs dayz-server-monitor` to view logs.
- To stop: `docker stop dayz-server-monitor`
- To remove: `docker rm dayz-server-monitor`

### Using Docker Compose (Recommended)

You can use [Docker Compose](https://docs.docker.com/compose/) for easier multi-file management and secret handling.

```yaml
version: "3.9"
services:
  dayz-server-monitor:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: dayz-server-monitor
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
      - ./output:/app/output
    environment:
      # Set the schedule for cron job
      - CRON_SCHEDULE=*/5 * * * *
      # Optionally provide API keys via secrets or env (see below)
      # - STEAM_API_KEY=your_steam_api_key
      # - DISCORD_WEBHOOK_URL=your_discord_webhook_url
    secrets:
      - STEAM_API_KEY
      - DISCORD_WEBHOOK_URL
    restart: unless-stopped

secrets:
  STEAM_API_KEY:
    file: ./secrets/steam_api_key.txt
  DISCORD_WEBHOOK_URL:
    file: ./secrets/discord_webhook_url.txt
```

#### Build and run with Compose (in background):

```sh
docker compose up --build -d
```

#### Docker secrets and environment variables

- **Secrets:** Place your Steam API key and Discord webhook URL in the `secrets/` directory as text files (`steam_api_key.txt`, `discord_webhook_url.txt`).
  These will be used securely by the container if present.
- **Environment variables:**
  If Docker secrets are not provided, you can set `STEAM_API_KEY` and/or `DISCORD_WEBHOOK_URL` as environment variables.

**Order of precedence:**
Docker Secret > Environment Variable > Config File

---

## Directory Structure

```
dayz_server_monitor/
├── config/                 # All config YAMLs (see above)
├── data/
│   ├── performance/        # Performance logs per server
│   ├── tracking/           # Mod tracking state per server
│   └── previous_run.json   # Legacy state file
├── locales/                # Localized message templates
├── src/
│   ├── config_loader.py    # Config loading/validation/merging
│   ├── logger.py           # Logging setup
│   ├── mod_checker.py      # Main mod check logic
│   ├── output_handler.py   # Output to console/file/Discord
│   ├── server_monitor_tracker.py  # State/persistence utils
│   ├── state_manager.py    # Legacy state save/load
│   ├── templates.py        # TemplateLoader for localization
│   └── monitor.py          # Entrypoint
│   ⋮
├── requirements.txt
└── README.md
```

---

## Configuration

All configuration is placed in the `config/` directory.

- **Defaults:** `config.defaults.yaml` (optional)
- **Global/Monitor:** `monitor.yaml` (required for global/serverless mode)
- **Per-server:** `*.yaml` (one per server)
- **Required fields:** `config.required.yaml` (optional, for validation)

Each server config merges: `defaults` ← `monitor.yaml` ← `per-server.yaml`.

**Validation:** Uses Pydantic models and required metadata; errors are logged and faulty configs are skipped.

---

## Output Options

- **Console:** Prints summary and changelogs (configurable).
- **File:** Appends output to `output/last_run.txt` (or custom path).
- **Discord:** Dispatches via webhook (requires config).

Customize output via the `output` section in your config YAMLs.

---

## Logging

- Configurable logging setup (console, file, per-level splitting, rotating logs).
- Logs are stored in `logs/` by default.
- Adjust log level and files in your config's `logging` section.

---

## Templates & Localization

- Templates live in `locales/<locale>/<category>/<file>.txt`
- Select locale via the `locale` config field.
- Use `{placeholder}` syntax in templates for variables.

---

## Development & Contribution

- **Python best practices:** Uses `pathlib` everywhere for filesystem access.
- **Exception handling:** Catches and logs specific exceptions where possible.
- **Type safety:** Pydantic models for config validation.
- **Extendability:** Modular codebase, easy to add new output or processing modes.

### To contribute

1. Fork and branch.
2. Make PRs with clear description and context.
3. Add/adjust templates and config samples as needed.

---

## License

CC BY-NC 4.0
See [LICENSE](LICENSE) for details.

---

## Credits

- **Author:** Tig Campbell-Moore (firstname[at]lastname[dot]com)
- Community contributors: see GitHub contributors list.

---
