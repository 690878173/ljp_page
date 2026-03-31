from dataclasses import dataclass


@dataclass
class PoolConfig:
    """连接池配置。"""

    max_connections: int = 100
    max_keepalive_connections: int = 20
    max_connections_per_host: int = 20
    extra: dict[str, Any] = field(default_factory=dict)