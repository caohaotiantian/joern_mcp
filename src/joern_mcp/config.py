"""应用配置管理"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # Joern Server配置
    joern_server_host: str = Field(default="localhost", description="Joern服务器地址")
    joern_server_port: int = Field(default=8080, description="Joern服务器端口")
    joern_server_username: str | None = Field(default=None, description="认证用户名")
    joern_server_password: str | None = Field(default=None, description="认证密码")

    # Joern路径配置
    joern_home: Path | None = Field(default=None, description="Joern安装路径")
    joern_workspace: Path = Field(
        default=Path.home() / ".joern_mcp" / "workspace", description="工作空间路径"
    )
    joern_cpg_cache: Path = Field(
        default=Path.home() / ".joern_mcp" / "cpg_cache", description="CPG缓存路径"
    )

    # MCP配置
    mcp_server_host: str = Field(default="localhost", description="MCP服务器地址")
    mcp_server_port: int = Field(default=3000, description="MCP服务器端口")

    # 性能配置
    max_concurrent_queries: int = Field(default=5, description="基础并发查询数")
    query_timeout: int = Field(default=300, description="查询超时时间(秒)")
    query_cache_size: int = Field(default=1000, description="查询缓存大小")
    query_cache_ttl: int = Field(default=3600, description="缓存TTL(秒)")

    # 高级性能配置
    enable_adaptive_concurrency: bool = Field(
        default=True, description="启用自适应并发控制"
    )
    min_concurrent_queries: int = Field(default=3, description="最小并发数")
    max_concurrent_limit: int = Field(default=20, description="最大并发限制")
    target_response_time: float = Field(default=1.0, description="目标响应时间(秒)")

    # 缓存优化配置
    enable_hybrid_cache: bool = Field(default=True, description="启用混合缓存(LRU+TTL)")
    hot_cache_size: int = Field(default=100, description="热缓存大小")
    cache_compression_threshold: int = Field(
        default=10240, description="缓存压缩阈值(字节)"
    )

    # 监控配置
    enable_slow_query_log: bool = Field(default=True, description="启用慢查询日志")
    slow_query_threshold: float = Field(default=5.0, description="慢查询阈值(秒)")
    enable_performance_metrics: bool = Field(
        default=True, description="启用性能指标收集"
    )

    # 安全配置
    allowed_paths: list[Path] = Field(
        default_factory=list, description="允许访问的路径"
    )
    enable_custom_queries: bool = Field(default=True, description="是否允许自定义查询")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file_path: Path = Field(
        default=Path.home() / ".joern_mcp" / "logs", description="日志文件路径"
    )
    log_file_size: int = Field(default=500, description="日志文件大小限制(MB)")
    log_retention_days: int = Field(default=10, description="日志保留天数")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# 全局配置实例
settings = Settings()
