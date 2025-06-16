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
python -m src.monitor
```

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
