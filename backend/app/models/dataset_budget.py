import os
import re
from dataclasses import dataclass


DEFAULT_MAX_SINGLE_DATASET_BYTES = 5 * 1024 ** 3
DEFAULT_MAX_TOTAL_DOWNLOAD_BYTES = 20 * 1024 ** 3


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
        return value if value > 0 else default
    except Exception:
        return default


def max_single_dataset_bytes() -> int:
    return _env_int("MAX_SINGLE_DATASET_BYTES", DEFAULT_MAX_SINGLE_DATASET_BYTES)


def max_total_download_bytes() -> int:
    return _env_int("MAX_TOTAL_DOWNLOAD_BYTES", DEFAULT_MAX_TOTAL_DOWNLOAD_BYTES)


def parse_size_to_bytes(size_text: str):
    if not size_text:
        return None
    txt = str(size_text).strip().upper().replace(",", "")
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([KMGTP]?B)", txt)
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2)
    factor = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
        "PB": 1024 ** 5,
    }.get(unit, 1)
    return int(value * factor)


@dataclass
class DownloadBudgetTracker:
    single_limit_bytes: int
    total_limit_bytes: int
    total_used_bytes: int = 0

    def can_add(self, add_bytes: int) -> bool:
        if add_bytes < 0:
            return False
        return (self.total_used_bytes + add_bytes) <= self.total_limit_bytes

    def consume(self, add_bytes: int) -> None:
        if add_bytes > 0:
            self.total_used_bytes += add_bytes
