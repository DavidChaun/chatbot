import os
import pytz
import time
from typing import Coroutine, Optional
from datetime import datetime

ISO_TIME_PATTERN = "%Y-%m-%dT%H:%M:%S%z"
DATE_TIME_PATTERN = "%Y-%m-%d %H:%M:%S"
DATE_PATTERN = "%Y-%m-%d"
_LOCAL_TIMEZONE = pytz.timezone("Asia/Shanghai")


def file_relative_path(dunderfile: str, relative_path: str) -> str:
    """Return the relative path of a file to another file."""
    return os.path.join(os.path.dirname(dunderfile), relative_path)


def sync(coroutine: Coroutine):
    """
    同步执行异步函数，使用可参考 [同步执行异步代码](https://nemo2011.github.io/bilibili-api/#/sync-executor)

    Args:
        coroutine (Coroutine): 异步函数

    Returns:
        该异步函数的返回值
    """
    import asyncio

    try:
        asyncio.get_event_loop()
    except:
        asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)


class Timer:
    def __init__(self, desc: str = None):
        self._start_time = None
        self._desc = desc

    def __enter__(self):
        self._start_time = time.perf_counter()

    def __exit__(self, type, value, traceback):
        from app.logging_ import logger

        elapsed_time = time.perf_counter() - self._start_time
        logger.info(f"{self._desc} elapsed time: {elapsed_time:0.4f} seconds")

        self._start_time = None


def datetime_string():
    # yyyyMMddHHmmSSsss
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def get_file_extension(file: str) -> str:
    return os.path.splitext(file)[1].lower()


def current_timestamp():
    return int(time.time() * 1000)


def to_date_string(
    unix_timestamp: Optional[int] = None, pattern: str = DATE_TIME_PATTERN
) -> Optional[str]:
    """
    将 unix 时间戳转换为指定格式的时间字符串
    :param unix_timestamp: unix时间戳
    :param pattern: 返回格式，默认为iso格式
    :return:
    """
    if unix_timestamp is None:
        return None

    dt = datetime.fromtimestamp(unix_timestamp / 1000, tz=_LOCAL_TIMEZONE)
    return dt.strftime(pattern)