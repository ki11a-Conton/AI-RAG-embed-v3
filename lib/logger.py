"""
logger.py
统一日志模块，同时输出到控制台和 logs/app.log。
logs/ 目录始终位于本文件所在的项目根目录下。
"""
import logging
import os

# 始终把日志写到项目根目录的 logs/，无论从哪里启动
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_LOGS_DIR = os.path.join(_PROJECT_DIR, "..", "logs")


def get_logger(name: str = "ai-rag-embed") -> logging.Logger:
    os.makedirs(_LOGS_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    log_file = os.path.join(_LOGS_DIR, "app.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
