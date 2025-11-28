"""Joern管理器"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
from joern_mcp.config import settings


class JoernNotFoundError(Exception):
    """Joern未找到异常"""
    pass


class JoernManager:
    """Joern安装和版本管理"""
    
    def __init__(self) -> None:
        self.joern_path: Optional[Path] = None
        self.version: Optional[str] = None
        self._detect_joern()
    
    def _detect_joern(self) -> None:
        """检测Joern安装"""
        # 1. 检查配置的路径
        if settings.joern_home and (settings.joern_home / "joern").exists():
            self.joern_path = settings.joern_home / "joern"
            logger.info(f"Found Joern at configured path: {self.joern_path}")
            return
        
        # 2. 检查环境变量
        if joern_home := os.getenv("JOERN_HOME"):
            path = Path(joern_home) / "joern"
            if path.exists():
                self.joern_path = path
                logger.info(f"Found Joern from JOERN_HOME: {self.joern_path}")
                return
        
        # 3. 检查PATH
        if joern_path := shutil.which("joern"):
            self.joern_path = Path(joern_path)
            logger.info(f"Found Joern in PATH: {self.joern_path}")
            return
        
        # 4. 检查默认安装路径
        default_paths = [
            Path("/usr/local/bin/joern"),
            Path("/opt/joern/joern"),
            Path.home() / ".local/bin/joern",
        ]
        for path in default_paths:
            if path.exists():
                self.joern_path = path
                logger.info(f"Found Joern at default path: {self.joern_path}")
                return
        
        logger.error("Joern not found")
        raise JoernNotFoundError(
            "Joern not found. Please install Joern or set JOERN_HOME environment variable."
        )
    
    def get_version(self) -> str:
        """获取Joern版本"""
        if self.version:
            return self.version
        
        if not self.joern_path:
            raise JoernNotFoundError("Joern not found")
        
        try:
            result = subprocess.run(
                [str(self.joern_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 解析版本号
            output = result.stdout.strip()
            # 版本号通常在输出中，格式如 "Joern 2.0.1" 或 "2.0.1"
            version_line = output.split('\n')[0]
            # 提取版本号
            import re
            match = re.search(r'(\d+\.\d+\.\d+)', version_line)
            if match:
                self.version = match.group(1)
                logger.info(f"Joern version: {self.version}")
                return self.version
            
            logger.warning(f"Could not parse version from: {output}")
            return "unknown"
            
        except Exception as e:
            logger.error(f"Failed to get Joern version: {e}")
            return "unknown"
    
    def validate_installation(self) -> Dict[str, bool]:
        """验证Joern安装完整性"""
        result = {
            "joern_found": self.joern_path is not None,
            "joern_executable": False,
            "version_retrieved": False,
        }
        
        if not self.joern_path:
            return result
        
        # 检查可执行权限
        result["joern_executable"] = os.access(self.joern_path, os.X_OK)
        
        # 检查版本
        version = self.get_version()
        result["version_retrieved"] = version != "unknown"
        
        return result
    
    def ensure_directories(self) -> None:
        """确保必要的目录存在"""
        settings.joern_workspace.mkdir(parents=True, exist_ok=True)
        settings.joern_cpg_cache.mkdir(parents=True, exist_ok=True)
        logger.info("Joern directories created")

