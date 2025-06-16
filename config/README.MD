# DayZ Server Monitor — Configuration Directory

This directory contains all YAML configuration files for the DayZ Server Monitor, including monitor-wide settings, per-server overrides, custom defaults, and required field definitions.

---

## Configuration Files Overview

- **monitor.yaml**
  Project-wide default configuration (applies to all servers unless overridden).
- **server.yaml**
  Per-server configuration (overrides monitor.yaml for that server).
- **config.defaults.yaml**
  Default fallback values for any missing configuration options.
- **config.required.yaml**
  List of configuration options that must be present in every final merged config.

---

## Configuration Options

Below is a detailed explanation of each configuration option, their purpose, valid formats, and (where relevant) possible or recommended values.

---

### Top-Level Options

#### `locale`
- **Description:** Controls language/locale for messages and templates.
- **Possible Values:**
  - `"en_GB"` (British English, default)
  - `"en_US"` (American English)
  - Other locales as supported by your template set

#### `log_dir`
- **Description:** Directory where log files are stored.
- **Possible Values:**
  - Any valid directory name (e.g., `"logs"`)

#### `server_name`
- **Description:** Display name for the server (used in logs and notifications).
- **Possible Values:**
  - Any string

#### `ip`
- **Description:** IP address of the DayZ server.
- **Possible Values:**
  - Any valid IPv4 or IPv6 address or hostname (e.g., `127.0.0.1`)

#### `port`
- **Description:** Port number the DayZ server is listening on.
- **Possible Values:**
  - Any valid TCP port (integer, e.g., `2302`)

---

### Logging Options

#### `logging`
- **Description:** (Optional) Controls basic logging features.
- **Sub-options:**
  - `enabled` (bool): Enable or disable logging entirely.
  - `level` (string): Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
  - `files` (dict): Filenames for each log level (e.g., `debug.log`, `error.log`)

#### `log_rotation`
- **Description:** Advanced log file rotation, retention, and compression.
- **Sub-options:**
  - `enabled`:
    - **Type:** Boolean
    - **Default:** `true`
    - **Description:** Master switch for log rotation.
  - `max_bytes`:
    - **Type:** String or integer
    - **Default:** `50M` (recommended)
    - **Description:** Maximum size before log file is rotated. **Accepts human-friendly strings:**
      - Examples:
        - `10K` = 10 * 1024 bytes
        - `5M` = 5 * 1024 * 1024 bytes
        - `1G` = 1 * 1024 * 1024 * 1024 bytes
        - Or just an integer byte count (e.g., `5000000`)
  - `min_days`:
    - **Type:** Integer
    - **Default:** `3`
    - **Description:** Minimum days to retain a rotated log before it becomes eligible for deletion.
  - `backup_count`:
    - **Type:** Integer
    - **Default:** `10`
    - **Description:** Maximum number of rotated logs to keep (oldest pruned after `min_days`).
  - `daily`:
    - **Type:** Boolean
    - **Default:** `true`
    - **Description:** Enable daily log rotation at a specific time.
  - `rotate_time`:
    - **Type:** String (format: `HH:MM`)
    - **Default:** `"00:00"`
    - **Description:** Time of day for daily rotation.
  - `compress`:
    - **Type:** String or null
    - **Default:** `gz` (recommended)
    - **Description:** Compression method for rotated logs.
    - **Possible Values:**
      - `gz`: gzip compression
        - **Pros:** Fast, widely supported, good compression ratio
        - **Cons:** Slightly larger than bz2, slower than zip for decompression
      - `bz2`: bzip2 compression
        - **Pros:** Best compression ratio, smallest files
        - **Cons:** Slower compression/decompression, less common
      - `zip`: ZIP format
        - **Pros:** Compatible with Windows, quick to open
        - **Cons:** Slightly larger files, slower than gzip
      - `null`: No compression
        - **Pros:** Fastest operation, no dependency
        - **Cons:** Larger disk usage

---

### Output Options

#### `output`
- **Description:** Controls where and how output is sent.
- **Sub-options:**
  - `to_console`:
    - **Type:** Boolean
    - **Description:** Output to console (terminal)
  - `to_file`:
    - **Type:** Boolean
    - **Description:** Output to a file (see `file_path`)
  - `to_discord`:
    - **Type:** Boolean
    - **Description:** Post results to Discord webhook
  - `file_path`:
    - **Type:** String
    - **Description:** Path for output file if `to_file` is enabled
  - `show_removed_mods`, `silent_on_no_changes`, `show_island`, `show_platform`, `show_dedicated`, `show_mod_count`, `show_next_reboot`:
    - **Type:** Boolean
    - **Description:** Controls specific details in output

---

### Mod Checking Options

All mod-related options **must be placed under a `mods:` block** in each per-server config.

#### `mods.mod_checking_enabled`
- **Description:** Enable/disable mod checking.
- **Type:** Boolean
- **Example:**
  ```yaml
  mods:
    mod_checking_enabled: true
  ```

#### `mods.mod_check_mode`
- **Description:** Processing model for mod checks.
- **Possible Values:**
  - `async`: (Recommended for most) Asynchronous, fastest, best for many servers
  - `threaded`: Uses threads, good for I/O-bound tasks
  - `serial`: One at a time, slowest but simplest
- **Example:**
  ```yaml
  mods:
    mod_check_mode: async
  ```

#### `mods.show_mod_changelog`
- **Description:** Show the changelog for mods when they are updated (if available).
- **Type:** Boolean
- **Default:** `true`
- **Example:**
  ```yaml
  mods:
    show_mod_changelog: true
  ```

#### `mods.max_changelog_lines`
- **Description:** Maximum number of lines of changelog to display for a mod update. If the changelog is longer, it will be truncated.
- **Type:** Integer
- **Default:** `2`
- **Example:**
  ```yaml
  mods:
    max_changelog_lines: 2
  ```

#### `mods.show_mod_links`
- **Description:** Show clickable Steam Workshop links for mods in Discord output.
- **Type:** Boolean
- **Default:** `true`
- **Example:**
  ```yaml
  mods:
    show_mod_links: true
  ```

#### `mods.report_limit`
- **Description:** Maximum number of mod additions/updates to report to Discord in a single detailed post.
    If the total is greater than this value, a summary message is sent instead.
    This prevents hitting the Discord 2000-character message limit and keeps notifications readable.
- **Type:** Integer
- **Default:** `10`
- **Example:**
  ```yaml
  mods:
    report_limit: 10
  ```

---

### Threaded Mode Options

#### `threaded_mode`
- **Sub-options:**
  - `max_workers`: Maximum number of threads if using `mod_check_mode: threaded`
- **Example:**
  ```yaml
  threaded_mode:
    max_workers: 10
  ```

---

### Steam API Options

#### `steam.api_key`
- **Type:** String (optional)
- **Description:** Used for authenticated Steam API requests
- **Example:**
  ```yaml
  steam:
    api_key: "YOUR_STEAM_API_KEY"
  ```

---

### Discord Options

#### `discord`
- **Sub-options:**
  - `enabled`:
    - **Type:** Boolean
    - **Description:** Enable/disable Discord integration
  - `webhook_url`:
    - **Type:** String
    - **Description:** Discord webhook for notifications (per-server)
- **Example:**
  ```yaml
  discord:
    enabled: true
    webhook_url: "https://discord.com/api/webhooks/..."
  ```

---

## Custom Defaults and Required Fields

- **config.defaults.yaml**
  - Provides fallback values for any missing config options.
  - Should also include a `mods:` block for mod-checking defaults.
- **config.required.yaml**
  - Any option listed here (using dot notation for nested fields) **must be present** in the final merged config for each server, or that server will not be processed.

---

## Example: Full Log Rotation Block

```yaml
log_rotation:
  enabled: true
  max_bytes: 10M         # Accepts size strings (K = KiB, M = MiB, G = GiB, all powers of 1024)
  min_days: 2
  backup_count: 10
  daily: true
  rotate_time: "03:00"
  compress: gz           # gz, bz2, zip, or null
```

---

## Example: Full Mods Block

```yaml
mods:
  mod_checking_enabled: true
  mod_check_mode: async
  show_mod_changelog: true
  max_changelog_lines: 2
  report_limit: 10
```

---

## Notes

- **Size Strings:** For `max_bytes`, use integer (bytes) or a string like `10K`, `5M`, or `1G` (powers of 1024).
- **Nested Options:** Use dot notation in `config.required.yaml` for nested fields (e.g., `log_rotation.max_bytes` or `mods.max_changelog_lines`).
- **Overrides:** Server configs can override any option from monitor.yaml or config.defaults.yaml.
- **Placement:** All mod-related settings must be under a `mods:` block in each per-server config (not at the top level).
- **Compression Pros/Cons:** See above for guidance on `log_rotation.compress`.
- **Discord Message Limit:** If there are more than `mods.report_limit` mod changes, or the message would exceed 2000 characters, a summary will be sent to Discord instead of detailed output.
- **Changelog Display:** If a changelog is too long, it will be truncated to `max_changelog_lines`, and a link will be provided to the full changelog if available.

---

For further help, see the sample configs or open an issue!
