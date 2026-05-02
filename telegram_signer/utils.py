import os
import pathlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE_NAME = "Asia/Shanghai"
DEFAULT_TIMEZONE = timezone(timedelta(hours=8), name=DEFAULT_TIMEZONE_NAME)


def numbering(num: int, lang: str = "arabic") -> str:
    return str(num)


def _load_timezone_from_file(path: str | os.PathLike[str]):
    path = pathlib.Path(path).expanduser()
    if not path.is_file():
        return None
    try:
        with path.open("rb") as fp:
            return ZoneInfo.from_file(fp)
    except (OSError, ValueError, ZoneInfoNotFoundError):
        return None


def _load_timezone(name: str | None):
    if not name:
        return None
    candidate = name.strip()
    if not candidate:
        return None
    if candidate.startswith(":"):
        candidate = candidate[1:].strip()
        if not candidate:
            return None
    if candidate.startswith(("/", ".", "~")):
        tz = _load_timezone_from_file(candidate)
        if tz is not None:
            return tz
    try:
        return ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        return None


def _get_local_timezone():
    local_tz = datetime.now().astimezone().tzinfo
    if local_tz is not None:
        return local_tz
    return None


def get_timezone():
    tz = _load_timezone(os.environ.get("TZ"))
    if tz is not None:
        return tz
    tz = _get_local_timezone()
    if tz is not None:
        return tz
    return _load_timezone(DEFAULT_TIMEZONE_NAME) or DEFAULT_TIMEZONE


def get_now():
    return datetime.now(tz=get_timezone())


class UserInput:
    def __init__(self, index: int = 1, numbering_lang: str = "arabic"):
        self.index = index
        self.numbering_lang = numbering_lang

    def incr(self, n: int = 1):
        self.index += n

    def decr(self, n: int = 1):
        self.index -= n

    @property
    def index_str(self):
        return f"{numbering(self.index, self.numbering_lang)}. "

    def __call__(self, prompt: str = None):
        result = input(f"{self.index_str}{prompt}")
        self.incr(1)
        return result


def print_to_user(*args, sep=" ", end="\n", flush=False, **kwargs):
    return print(*args, sep=sep, end=end, flush=flush, **kwargs)
