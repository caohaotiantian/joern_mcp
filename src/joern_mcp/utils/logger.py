"""日志配置"""
import sys
from pathlib import Path
from loguru import logger
from joern_mcp.config import settings


def setup_logging() -> None:
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 确保日志目录存在
    settings.log_file_path.mkdir(parents=True, exist_ok=True)
    
    # 文件输出 - 所有日志
    logger.add(
        settings.log_file_path / "joern_mcp_{time}.log",
        rotation=f"{settings.log_file_size} MB",
        retention=f"{settings.log_retention_days} days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    # 错误日志单独文件
    logger.add(
        settings.log_file_path / "error_{time}.log",
        rotation=f"{settings.log_file_size} MB",
        retention=f"{settings.log_retention_days} days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    logger.info("Logging system initialized")


# 自动初始化
setup_logging()

