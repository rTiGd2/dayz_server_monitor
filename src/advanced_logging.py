# Project: DayZ Server Monitor
# File: advanced_logging.py
# Purpose: Advanced logging with configurable rotation, daily and size-based, compression, and retention per config/server.
#          Now skips rotation/archiving if the log file is empty.
#          Supports human-friendly size strings for max_bytes (e.g., 10K, 5M, 1G).
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging
from pathlib import Path
import shutil
import gzip
import bz2
import zipfile
from datetime import datetime, timedelta
import yaml

ROTATE_STATE_FMT = "{basename}.logrotate"

def parse_size(size):
    """
    Parse human-readable file size (e.g. '10K', '5M', '1G') into bytes.
    K = KiB = 1024, M = MiB, G = GiB.
    Accepts int or string. Returns integer bytes.
    """
    if isinstance(size, int):
        return size
    if isinstance(size, str):
        size = size.strip().upper()
        multiplier = 1
        if size.endswith('K'):
            multiplier = 1024
            size = size[:-1]
        elif size.endswith('M'):
            multiplier = 1024 ** 2
            size = size[:-1]
        elif size.endswith('G'):
            multiplier = 1024 ** 3
            size = size[:-1]
        try:
            return int(float(size) * multiplier)
        except Exception:
            raise ValueError(f"Invalid size format: {size}")
    raise ValueError(f"Invalid size type: {type(size)}")

def compress_file(src, method):
    """
    Compress the log file using the specified method.
    Supports 'gz', 'bz2', 'zip', or returns the original if method is None/unknown.
    """
    src_path = Path(src)
    if method == "gz":
        with src_path.open("rb") as f_in, gzip.open(str(src_path) + ".gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        src_path.unlink()
        return str(src_path) + ".gz"
    elif method == "bz2":
        with src_path.open("rb") as f_in, bz2.open(str(src_path) + ".bz2", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        src_path.unlink()
        return str(src_path) + ".bz2"
    elif method == "zip":
        zip_path = src_path.with_suffix(src_path.suffix + ".zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(str(src_path), arcname=src_path.name)
        src_path.unlink()
        return str(zip_path)
    return str(src_path)

def get_rotate_state_path(logfile):
    """
    Get the path for the file storing last rotation information.
    """
    logfile_path = Path(logfile)
    basename = logfile_path.stem
    dirname = logfile_path.parent
    return dirname / ROTATE_STATE_FMT.format(basename=basename)

def load_last_rotate(logfile):
    """
    Load the last rotation datetime from the rotation state file, if present.
    """
    statefile = get_rotate_state_path(logfile)
    if statefile.exists():
        try:
            with statefile.open("r") as f:
                d = yaml.safe_load(f)
                if d and 'last_rotate' in d:
                    return datetime.fromisoformat(d['last_rotate'])
        except Exception:
            pass
    return None

def save_last_rotate(logfile, dt):
    """
    Save the given datetime as the last rotation time for the logfile.
    """
    statefile = get_rotate_state_path(logfile)
    with statefile.open("w") as f:
        yaml.safe_dump({"last_rotate": dt.isoformat()}, f)

def should_rotate_daily(config, logfile):
    """
    Determine if the log should be rotated due to daily schedule.
    Do not rotate if the file is empty.
    """
    logfile_path = Path(logfile)
    if not logfile_path.exists() or logfile_path.stat().st_size == 0:
        return False
    rotate_time = config.get("log_rotation", {}).get("rotate_time", "00:00")
    rotate_hour, rotate_minute = map(int, rotate_time.split(":"))
    now = datetime.now()
    last_rotate = load_last_rotate(logfile)
    scheduled = now.replace(hour=rotate_hour, minute=rotate_minute, second=0, microsecond=0)
    if now < scheduled and last_rotate and last_rotate.date() == (now - timedelta(days=1)).date():
        return False
    if now >= scheduled:
        if not last_rotate or last_rotate.date() < now.date():
            return True
    return False

def should_rotate_size(config, logfile):
    """
    Determine if the log should be rotated due to max_bytes size limit.
    Only rotate if the log file exists and is not empty.
    """
    max_bytes_raw = config.get("log_rotation", {}).get("max_bytes")
    logfile_path = Path(logfile)
    if not max_bytes_raw or not logfile_path.exists():
        return False
    if logfile_path.stat().st_size == 0:
        # Don't rotate empty files
        return False
    max_bytes = parse_size(max_bytes_raw)
    size = logfile_path.stat().st_size
    return size >= max_bytes

def list_rotated_logs(logfile, compression_methods):
    """
    List all rotated logs, including compressed ones, for pruning.
    """
    logfile_path = Path(logfile)
    dirname = logfile_path.parent
    basename = logfile_path.name
    name = logfile_path.stem
    rotated = []
    for fname in dirname.iterdir():
        if fname.name.startswith(name) and fname.name != basename:
            if fname.name.endswith(".log") or any(fname.name.endswith("." + c) for c in compression_methods):
                rotated.append(fname)
    rotated.sort(key=lambda f: f.stat().st_ctime)
    return rotated

def prune_rotated_logs(logfile, config):
    """
    Prune oldest rotated logs according to backup_count and min_days.
    """
    rotation = config.get("log_rotation", {})
    backup_count = rotation.get("backup_count", 7)
    min_days = rotation.get("min_days", 3)
    compress_method = rotation.get("compress")
    rotated = list_rotated_logs(logfile, ["gz", "bz2", "zip"])
    now = datetime.now()
    keep = []
    for lf in rotated:
        ctime = datetime.fromtimestamp(lf.stat().st_ctime)
        age_days = (now - ctime).days
        if age_days < min_days:
            keep.append(lf)
        else:
            keep.append(lf)
    extra = len(keep) - backup_count
    if extra > 0:
        candidates = [f for f in keep if (now - datetime.fromtimestamp(f.stat().st_ctime)).days >= min_days]
        for f in sorted(candidates, key=lambda f: f.stat().st_ctime)[:extra]:
            try:
                f.unlink()
            except Exception:
                pass

class AdvancedLogger:
    """
    Advanced logger with daily/size rotation, compression, and per-server configuration.
    Now skips rotation/archiving if the log file is empty.
    This logger is intended for specialized logs (such as per-server run logs)
    and should not be used for global info/error logging (handled by logger.py).
    """
    def __init__(self, config, logtype="error"):
        self.config = config
        self.logtype = logtype
        self.enabled = config.get("log_rotation", {}).get("enabled", True)
        self.log_dir = Path(config.get("log_dir", "logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        config_file = config.get("_config_file", "monitor.yaml").replace(".yaml", "")
        self.config_file = config_file
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.logfile = self.log_dir / f"{config_file}.{logtype}.{self.date_str}.log"
        self._logger = None
        self.setup_logger()

    def get_configured_level(self):
        """
        Get the logger level from config. Defaults to INFO.
        """
        # Check for 'logging' section in config
        level_str = self.config.get("logging", {}).get("level", "INFO")
        return getattr(logging, level_str.upper(), logging.INFO)

    def setup_logger(self):
        """
        Set up the logger object and file handler, with log level from config.
        """
        self._logger = logging.getLogger(f"{self.config_file}_{self.logtype}")
        self._logger.propagate = False
        log_level = self.get_configured_level()
        self._logger.setLevel(log_level)
        handler = logging.FileHandler(self.logfile, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(log_level)  # Ensure handler also respects log level
        self._logger.handlers = []
        self._logger.addHandler(handler)

    def rotate_logs(self, force=False):
        """
        Perform log rotation if needed (by size, daily, or forced).
        Only rotate if the log file exists and is not empty.
        """
        rotation = self.config.get("log_rotation", {})
        compress_method = rotation.get("compress")
        backup_count = rotation.get("backup_count", 7)
        min_days = rotation.get("min_days", 3)
        daily = rotation.get("daily", False)
        rotated = False

        if not self.enabled:
            return

        # Only rotate if file exists and is not empty
        logfile_path = Path(self.logfile)
        if not logfile_path.exists() or logfile_path.stat().st_size == 0:
            return

        if should_rotate_size(self.config, self.logfile):
            rotated = True
        elif daily and should_rotate_daily(self.config, self.logfile):
            rotated = True
        elif force:
            rotated = True

        if rotated:
            now = datetime.now()
            rotate_suffix = now.strftime("%Y-%m-%d_%H%M%S")
            rotated_log = logfile_path.with_name(logfile_path.name.replace(".log", f".{rotate_suffix}.log"))
            self._logger.handlers[0].close()
            logfile_path.rename(rotated_log)
            rotated_log_path = rotated_log
            if compress_method in ("gz", "bz2", "zip"):
                rotated_log_path = Path(compress_file(str(rotated_log), compress_method))
            save_last_rotate(self.logfile, now)
            self.setup_logger()
            prune_rotated_logs(self.logfile, self.config)

    def info(self, msg):
        self.rotate_logs()
        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info(msg)

    def error(self, msg):
        self.rotate_logs()
        if self._logger.isEnabledFor(logging.ERROR):
            self._logger.error(msg)

    def warning(self, msg):
        self.rotate_logs()
        if self._logger.isEnabledFor(logging.WARNING):
            self._logger.warning(msg)

    def debug(self, msg):
        self.rotate_logs()
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(msg)
