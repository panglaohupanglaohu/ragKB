#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marine Channel Base Class - 船舶 Channel 统一基类

为所有船舶工程 Channel 提供统一接口和通用功能。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class ChannelStatus(Enum):
    """Channel 运行状态."""
    OK = "ok"           # 正常运行
    WARN = "warn"       # 警告状态
    ERROR = "error"     # 错误状态
    OFF = "off"         # 未启用


class ChannelPriority(Enum):
    """Channel 优先级."""
    P0 = 0  # 核心功能
    P1 = 1  # 重要功能
    P2 = 2  # 辅助功能


@dataclass
class ChannelHealth:
    """Channel 健康状态."""
    status: ChannelStatus
    message: str
    last_check: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0.0
    error_count: int = 0
    warning_count: int = 0


@dataclass
class ChannelMetrics:
    """Channel 性能指标."""
    calls_total: int = 0
    calls_success: int = 0
    calls_failed: int = 0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    last_call_time: Optional[datetime] = None


class MarineChannel(ABC):
    """船舶工程 Channel 统一基类。
    
    所有船舶 Channel 应继承此类，实现统一接口规范。
    
    Attributes:
        name: Channel 内部标识符 (e.g., "weather_routing").
        description: 人类可读描述 (e.g., "气象导航与航线优化").
        version: Channel 版本号 (e.g., "1.0.0").
        priority: 优先级 (P0/P1/P2).
        dependencies: 依赖的其他 Channel 列表.
    
    Example:
        >>> class WeatherRoutingChannel(MarineChannel):
        ...     name = "weather_routing"
        ...     description = "气象导航与航线优化"
        ...     version = "1.0.0"
        ...     priority = ChannelPriority.P0
        ...     
        ...     def initialize(self) -> bool:
        ...         # 初始化逻辑
        ...         return True
        ...     
        ...     def get_status(self) -> Dict[str, Any]:
        ...         # 返回状态报告
        ...         return {"status": "ok"}
    """
    
    # 类属性 (子类必须覆盖)
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    priority: ChannelPriority = ChannelPriority.P2
    dependencies: List[str] = None
    
    def __init__(self, **kwargs):
        """初始化 Channel.
        
        Args:
            **kwargs: 配置参数.
        """
        # 实例属性
        self._initialized: bool = False
        self._health: ChannelHealth = ChannelHealth(
            status=ChannelStatus.OFF,
            message="Not initialized"
        )
        self._metrics: ChannelMetrics = ChannelMetrics()
        self._config: Dict[str, Any] = {}
        self._config.update(kwargs)
        self._created_at = datetime.now()
        
        # 实例化依赖列表，避免修改类属性
        self.dependencies = list(self.dependencies or [])
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化 Channel.
        
        Returns:
            True 如果初始化成功，否则 False.
        """
        ...
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """获取 Channel 当前状态.
        
        Returns:
            状态字典，包含运行状态、配置信息等.
        """
        ...
    
    @abstractmethod
    def shutdown(self) -> bool:
        """关闭 Channel，释放资源.
        
        Returns:
            True 如果关闭成功，否则 False.
        """
        ...
    
    def check(self) -> Tuple[str, str]:
        """检查 Channel 是否可用.
        
        Returns:
            (status, message) 元组，status 为 'ok'/'warn'/'error'/'off'.
        """
        if not self._initialized:
            return ("off", "Channel not initialized")
        
        if self._health.status == ChannelStatus.OK:
            return ("ok", self._health.message)
        elif self._health.status == ChannelStatus.WARN:
            return ("warn", self._health.message)
        else:
            return ("error", self._health.message)
    
    def get_health(self) -> ChannelHealth:
        """获取 Channel 健康状态.
        
        Returns:
            ChannelHealth 对象.
        """
        return self._health
    
    def get_metrics(self) -> ChannelMetrics:
        """获取 Channel 性能指标.
        
        Returns:
            ChannelMetrics 对象.
        """
        return self._metrics
    
    def reset_metrics(self) -> None:
        """重置性能指标."""
        self._metrics = ChannelMetrics()
    
    def _record_call(self, success: bool, latency_ms: float) -> None:
        """记录一次调用.
        
        Args:
            success: 调用是否成功.
            latency_ms: 调用耗时 (毫秒).
        """
        self._metrics.calls_total += 1
        if success:
            self._metrics.calls_success += 1
        else:
            self._metrics.calls_failed += 1
        
        self._metrics.last_call_time = datetime.now()
        
        # 更新延迟统计
        total_calls = self._metrics.calls_total
        old_avg = self._metrics.avg_latency_ms
        self._metrics.avg_latency_ms = (
            (old_avg * (total_calls - 1) + latency_ms) / total_calls
        )
        
        if latency_ms > self._metrics.max_latency_ms:
            self._metrics.max_latency_ms = latency_ms
        if latency_ms < self._metrics.min_latency_ms:
            self._metrics.min_latency_ms = latency_ms
    
    def _set_health(self, status: ChannelStatus, message: str) -> None:
        """设置 Channel 健康状态.
        
        Args:
            status: 状态枚举.
            message: 状态描述.
        """
        self._health.status = status
        self._health.message = message
        self._health.last_check = datetime.now()
        
        if status == ChannelStatus.ERROR:
            self._health.error_count += 1
        elif status == ChannelStatus.WARN:
            self._health.warning_count += 1
    
    def get_uptime(self) -> float:
        """获取运行时间 (秒).
        
        Returns:
            运行时间 (秒).
        """
        if not self._initialized:
            return 0.0
        return (datetime.now() - self._created_at).total_seconds()
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """验证配置参数.
        
        Returns:
            (is_valid, errors) 元组.
        """
        errors = []
        
        if not self.name:
            errors.append("Channel name is required")
        if not self.description:
            errors.append("Channel description is required")
        
        return (len(errors) == 0, errors)
    
    def get_info(self) -> Dict[str, Any]:
        """获取 Channel 基本信息.
        
        Returns:
            信息字典.
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "priority": self.priority.name,
            "dependencies": self.dependencies,
            "initialized": self._initialized,
            "uptime_seconds": self.get_uptime(),
        }


class ChannelRegistry:
    """Channel 注册表。
    
    管理所有已注册的 Marine Channel，提供统一的访问接口。
    
    Example:
        >>> registry = ChannelRegistry()
        >>> registry.register(weather_channel)
        >>> registry.register(engine_channel)
        >>> status = registry.get_all_status()
        >>> healthy = registry.get_healthy_channels()
    """
    
    def __init__(self):
        """初始化注册表."""
        self._channels: Dict[str, MarineChannel] = {}
        self._initialized = False
    
    def register(self, channel: MarineChannel) -> bool:
        """注册一个 Channel.
        
        Args:
            channel: 要注册的 Channel 实例.
        
        Returns:
            True 如果注册成功.
        
        Raises:
            ValueError: 如果 Channel 名称已存在.
        """
        if not channel.name:
            raise ValueError("Channel must have a name")
        
        if channel.name in self._channels:
            raise ValueError(f"Channel '{channel.name}' already registered")
        
        self._channels[channel.name] = channel
        return True
    
    def unregister(self, name: str) -> bool:
        """注销一个 Channel.
        
        Args:
            name: Channel 名称.
        
        Returns:
            True 如果注销成功.
        """
        if name in self._channels:
            del self._channels[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[MarineChannel]:
        """获取指定的 Channel.
        
        Args:
            name: Channel 名称.
        
        Returns:
            Channel 实例，如果不存在则返回 None.
        """
        return self._channels.get(name)
    
    def list_channels(self) -> List[str]:
        """列出所有已注册的 Channel 名称.
        
        Returns:
            名称列表.
        """
        return list(self._channels.keys())
    
    def initialize_all(self) -> Dict[str, bool]:
        """初始化所有 Channel.
        
        Returns:
            字典 {channel_name: success}.
        """
        results = {}
        for name, channel in self._channels.items():
            try:
                results[name] = channel.initialize()
            except Exception as e:
                results[name] = False
                channel._set_health(ChannelStatus.ERROR, str(e))
        
        self._initialized = True
        return results
    
    def shutdown_all(self) -> Dict[str, bool]:
        """关闭所有 Channel.
        
        Returns:
            字典 {channel_name: success}.
        """
        results = {}
        for name, channel in self._channels.items():
            try:
                results[name] = channel.shutdown()
            except Exception as e:
                results[name] = False
        
        self._initialized = False
        return results
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有 Channel 的状态.
        
        Returns:
            字典 {channel_name: status_dict}.
        """
        return {
            name: channel.get_status()
            for name, channel in self._channels.items()
        }
    
    def get_healthy_channels(self) -> List[MarineChannel]:
        """获取所有健康的 Channel.
        
        Returns:
            健康 Channel 列表.
        """
        return [
            channel for channel in self._channels.values()
            if channel.get_health().status == ChannelStatus.OK
        ]
    
    def get_unhealthy_channels(self) -> List[MarineChannel]:
        """获取所有不健康的 Channel.
        
        Returns:
            不健康 Channel 列表.
        """
        return [
            channel for channel in self._channels.values()
            if channel.get_health().status != ChannelStatus.OK
        ]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取所有 Channel 的性能指标汇总.
        
        Returns:
            汇总字典.
        """
        total_calls = 0
        total_success = 0
        total_failed = 0
        
        for channel in self._channels.values():
            metrics = channel.get_metrics()
            total_calls += metrics.calls_total
            total_success += metrics.calls_success
            total_failed += metrics.calls_failed
        
        return {
            "total_channels": len(self._channels),
            "total_calls": total_calls,
            "total_success": total_success,
            "total_failed": total_failed,
            "success_rate": total_success / total_calls if total_calls > 0 else 0.0,
        }


# 便捷函数
def create_registry() -> ChannelRegistry:
    """创建新的 Channel 注册表.
    
    Returns:
        新的 ChannelRegistry 实例.
    """
    return ChannelRegistry()


# 模块级默认注册表
_default_registry: Optional[ChannelRegistry] = None


def get_default_registry() -> ChannelRegistry:
    """获取默认注册表.
    
    Returns:
        默认 ChannelRegistry 实例.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = ChannelRegistry()
    return _default_registry


def register_channel(channel: MarineChannel) -> bool:
    """注册 Channel 到默认注册表.
    
    Args:
        channel: 要注册的 Channel.
    
    Returns:
        True 如果注册成功.
    """
    return get_default_registry().register(channel)


def get_channel(name: str) -> Optional[MarineChannel]:
    """从默认注册表获取 Channel.
    
    Args:
        name: Channel 名称.
    
    Returns:
        Channel 实例或 None.
    """
    return get_default_registry().get(name)
