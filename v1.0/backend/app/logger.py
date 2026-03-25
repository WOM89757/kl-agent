import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import os

from app.config import BASE_DIR


def setup_logger(
    name: str = __name__,
    level: int = None,
    log_to_file: bool = None,
    log_to_console: bool = None,
    log_dir: Path = None,
) -> logging.Logger:
    """
    创建并配置统一的日志记录器
    
    Args:
        name: 日志器名称，默认为模块名
        level: 日志级别，默认从环境变量读取或使用 INFO
        log_to_file: 是否写入文件，默认 True
        log_to_console: 是否输出到终端，默认 True
        log_dir: 日志文件目录，默认为 backend/logs
        
    Returns:
        配置好的 Logger 实例
    """
    # 从环境变量读取配置
    if level is None:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
    
    if log_to_file is None:
        log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    
    if log_to_console is None:
        log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    
    if log_dir is None:
        log_dir = BASE_DIR.parent / "logs"
    
    # 确保日志目录存在
    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取或创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 如果已经有处理器，不再重复添加
    if logger.handlers:
        return logger
    
    logger.propagate = False
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加文件处理器
    if log_to_file:
        log_file = log_dir / f"{name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 创建默认的根日志器
root_logger = setup_logger("root")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        Logger 实例
    """
    return setup_logger(name)
