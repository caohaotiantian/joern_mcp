"""应用配置管理"""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # Joern Server配置
    joern_server_host: str = Field(default="localhost", description="Joern服务器地址")
    joern_server_port: int = Field(default=8080, description="Joern服务器端口")
    joern_server_username: Optional[str] = Field(default=None, description="认证用户名")
    joern_server_password: Optional[str] = Field(default=None, description="认证密码")
    
    # Joern路径配置
    joern_home: Optional[Path] = Field(default=None, description="Joern安装路径")
    joern_workspace: Path = Field(
        default=Path.home() / ".joern_mcp" / "workspace",
        description="工作空间路径"
    )
    joern_cpg_cache: Path = Field(
        default=Path.home() / ".joern_mcp" / "cpg_cache",
        description="CPG缓存路径"
    )
    
    # MCP配置
    mcp_server_host: str = Field(default="localhost", description="MCP服务器地址")
    mcp_server_port: int = Field(default=3000, description="MCP服务器端口")
    
    # 性能配置
    max_concurrent_queries: int = Field(default=5, description="最大并发查询数")
    query_timeout: int = Field(default=300, description="查询超时时间(秒)")
    query_cache_size: int = Field(default=1000, description="查询缓存大小")
    query_cache_ttl: int = Field(default=3600, description="缓存TTL(秒)")
    
    # 安全配置
    allowed_paths: List[Path] = Field(default_factory=list, description="允许访问的路径")
    enable_custom_queries: bool = Field(default=True, description="是否允许自定义查询")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file_path: Path = Field(
        default=Path.home() / ".joern_mcp" / "logs",
        description="日志文件路径"
    )
    log_file_size: int = Field(default=500, description="日志文件大小限制(MB)")
    log_retention_days: int = Field(default=10, description="日志保留天数")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# 全局配置实例
settings = Settings()

