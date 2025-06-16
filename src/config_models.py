# Project: DayZ Server Monitor
# File: config_models.py
# Purpose: Pydantic configuration model for merged YAML config files.
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

from typing import Optional, Literal, Union
from pydantic import BaseModel, Field, IPvAnyAddress, validator

# ---------- LOGGING ----------
class LoggingFilesConfig(BaseModel):
    debug: str
    info: str
    error: str
    critical: str

class LoggingConfig(BaseModel):
    enabled: bool = True
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    files: LoggingFilesConfig

# ---------- LOG ROTATION ----------
class LogRotationConfig(BaseModel):
    enabled: bool = True
    max_bytes: Union[int, str] = "50M"
    min_days: int = 3
    backup_count: int = 10
    daily: bool = True
    rotate_time: str = "00:00"
    compress: Optional[Literal['gz', 'bz2', 'zip']] = "gz"

    @validator("max_bytes", pre=True)
    def validate_max_bytes(cls, v):
        """
        Accepts int (bytes) or string like '10K', '5M', '1G'.
        """
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            if v[-1].upper() in "KMG":
                num = int(v[:-1])
                suffix = v[-1].upper()
                return num * {"K":1024, "M":1024**2, "G":1024**3}[suffix]
            elif v.isdigit():
                return int(v)
            else:
                raise ValueError("Invalid max_bytes format")
        raise ValueError("max_bytes must be int or size string")

# ---------- OUTPUT ----------
class OutputConfig(BaseModel):
    to_console: bool = True
    to_file: bool = True
    to_discord: bool = True
    file_path: str
    show_removed_mods: bool = True
    silent_on_no_changes: bool = False
    show_island: bool = True
    show_platform: bool = True
    show_dedicated: bool = True
    show_mod_count: bool = True
    show_next_reboot: bool = True

# ---------- MODS ----------
class ModsConfig(BaseModel):
    mod_checking_enabled: bool = True
    mod_check_mode: Literal['async', 'threaded', 'serial'] = "async"
    show_mod_changelog: bool = True
    max_changelog_lines: int = 2
    show_mod_links: bool = True
    report_limit: int = 10

# ---------- THREADED MODE ----------
class ThreadedModeConfig(BaseModel):
    max_workers: int = 10

# ---------- STEAM ----------
class SteamConfig(BaseModel):
    api_key: Optional[str] = None

# ---------- DISCORD ----------
class DiscordConfig(BaseModel):
    enabled: Optional[bool] = None
    webhook_url: Optional[str] = None

# ---------- SERVER INFO ----------
class ServerInfoConfig(BaseModel):
    ip: Union[IPvAnyAddress, str]
    port: int

# ---------- REBOOT ----------
class RebootConfig(BaseModel):
    base_time: str
    interval_minutes: int

# ---------- TOP-LEVEL CONFIG ----------
class DayZServerMonitorConfig(BaseModel):
    """
    Unified config model for merged monitor/server/defaults YAML.
    """
    locale: str = "en_GB"
    log_dir: Optional[str] = "logs"
    server_name: Optional[str] = None
    ip: Optional[Union[IPvAnyAddress, str]] = None
    port: Optional[int] = None

    logging: Optional[LoggingConfig] = None
    log_rotation: Optional[LogRotationConfig] = None
    output: Optional[OutputConfig] = None
    mods: Optional[ModsConfig] = None
    threaded_mode: Optional[ThreadedModeConfig] = None
    steam: Optional[SteamConfig] = None
    discord: Optional[DiscordConfig] = None
    server: Optional[ServerInfoConfig] = None
    reboot: Optional[RebootConfig] = None
