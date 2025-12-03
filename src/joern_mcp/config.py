"""应用配置管理"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置

    所有配置项都可以通过环境变量或 .env 文件设置。
    环境变量名称为配置项名称的大写形式，例如：
    - joern_server_host -> JOERN_SERVER_HOST
    - query_timeout -> QUERY_TIMEOUT
    """

    # ==========================================
    # Joern Server 配置
    # ==========================================
    joern_server_host: str = Field(
        default="localhost",
        description="Joern 服务器地址",
    )
    joern_server_port: int = Field(
        default=8080,
        description="Joern 服务器端口",
    )
    joern_server_username: str | None = Field(
        default=None,
        description="Joern 服务器认证用户名（可选）",
    )
    joern_server_password: str | None = Field(
        default=None,
        description="Joern 服务器认证密码（可选）",
    )

    # ==========================================
    # Joern 路径配置
    # ==========================================
    joern_home: Path | None = Field(
        default=None,
        description="Joern 安装路径，默认从 PATH 查找",
    )
    joern_workspace: Path = Field(
        default=Path.home() / ".joern_mcp" / "workspace",
        description="工作空间路径，存放临时文件",
    )
    joern_cpg_cache: Path = Field(
        default=Path.home() / ".joern_mcp" / "cpg_cache",
        description="CPG 缓存路径",
    )

    # ==========================================
    # 性能配置
    # ==========================================
    max_concurrent_queries: int = Field(
        default=5,
        description="最大并发查询数",
    )
    query_timeout: int = Field(
        default=300,
        description="查询超时时间（秒）",
    )
    query_cache_size: int = Field(
        default=1000,
        description="查询结果缓存大小（条目数）",
    )
    query_cache_ttl: int = Field(
        default=3600,
        description="查询结果缓存 TTL（秒）",
    )

    # ==========================================
    # 安全配置
    # ==========================================
    enable_custom_queries: bool = Field(
        default=True,
        description="是否允许执行自定义 CPGQL 查询",
    )

    # ==========================================
    # 日志配置
    # ==========================================
    log_level: str = Field(
        default="INFO",
        description="日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_file_path: Path = Field(
        default=Path.home() / ".joern_mcp" / "logs",
        description="日志文件路径",
    )
    log_file_size: int = Field(
        default=500,
        description="日志文件大小限制（MB）",
    )
    log_retention_days: int = Field(
        default=10,
        description="日志文件保留天数",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# 全局配置实例
settings = Settings()
