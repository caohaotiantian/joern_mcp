"""测试日志系统"""
import pytest
from pathlib import Path
from loguru import logger
from joern_mcp.utils.logger import setup_logging


def test_logger_works():
    """测试日志功能"""
    setup_logging()
    
    # 这些应该不抛出异常
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")


def test_log_file_created(tmp_path, monkeypatch):
    """测试日志文件创建"""
    from joern_mcp import config
    monkeypatch.setattr(config.settings, "log_file_path", tmp_path)
    
    setup_logging()
    logger.info("Test message")
    
    # 检查日志文件是否创建
    log_files = list(tmp_path.glob("*.log"))
    assert len(log_files) > 0


def test_logger_initialization():
    """测试日志初始化"""
    # setup_logging会在import时自动调用
    # 这里只是验证logger可用
    assert logger is not None

