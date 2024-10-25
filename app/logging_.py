import logging
import os
from logging.handlers import RotatingFileHandler

import coloredlogs

from app import APP_NAME
from app.utils import file_relative_path


def _default_format_string():
    return "%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(filename)s:%(funcName)s:%(lineno)s - %(message)s"


def _default_date_format_string():
    return "%Y-%m-%d %H:%M:%S %z"


logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)

root_log_path = (
    os.getenv("HOME", file_relative_path(__file__, "../..")) + f"/logs/{APP_NAME}"
)
if not os.path.exists(root_log_path):
    os.makedirs(root_log_path)

# 创建一个输出到文件的 handler
file_handler = RotatingFileHandler(
    os.getenv("HOME", file_relative_path(__file__, "../.."))
    + f"/logs/{APP_NAME}/{APP_NAME}.log",
    mode="a",
    maxBytes=1024 * 1024 * 100,
    backupCount=7,
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter(
        fmt=_default_format_string(), datefmt=_default_date_format_string()
    )
)

# 创建一个输出到终端的 handler
terminal_handler = logging.StreamHandler()
terminal_handler.setLevel(logging.DEBUG)
terminal_handler.setFormatter(
    coloredlogs.ColoredFormatter(
        fmt=_default_format_string(),
        datefmt=_default_date_format_string(),
        field_styles={"levelname": {"color": "blue"}, "asctime": {"color": "green"}},
        level_styles={"debug": {}, "error": {"color": "red"}},
    )
)

# 将两个 handler 添加到 logger 中
logger.addHandler(file_handler)
logger.addHandler(terminal_handler)

# if PROFILE == "local":
#     logging.basicConfig(encoding="utf-8")
#     logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
