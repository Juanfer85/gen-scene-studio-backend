"""
Performance monitoring and metrics collection system
with Redis-based storage and real-time analytics
"""
import asyncio
import json
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from core.config import settings
from core.cache import cache_manager, CacheError

log = logging.getLogger(__name__)

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Metric:
    """Metric data structure"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = None
    unit: str = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['metric_type'] = self.metric_type.value
        return result

@dataclass
class Alert:
    """Alert data structure"""
    name: str
    level: AlertLevel
    message: str
    timestamp: datetime
    value: Union[int, float] = None
    threshold: Union[int, float] = None
    tags: Dict[str, str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['level'] = self.level.value
        return result

class MetricsCollector:
    """
    High-performance metrics collector with Redis storage
    and real-time alerting capabilities
    """

    def __init__(self):
        self._metrics: Dict[str, List[Metric]] = {}
        self._alerts: List[Alert] = []
        self._alerts_rules: Dict[str, Dict[str, Any]] = {}
        self._enabled = settings.METRICS_ENABLED
        self._prefix = settings.METRICS_REDIS_PREFIX
        self._retention_hours = settings.METRICS_RETENTION_HOURS
        self._batch_size = 100
        self._flush_interval = 60  # seconds
        self._last_flush = time.time()

    async def initialize(self):
        """Initialize metrics collector"""
        if not self._enabled:
            log.info("📊 Metrics collection disabled")
            return

        try:
            # Ensure cache manager is initialized
            if not cache_manager._redis:
                await cache_manager.initialize()

            # Setup default alert rules
            await self._setup_default_alerts()

            # Start background tasks
            asyncio.create_task(self._periodic_flush())
            asyncio.create_task(self._system_monitoring())
            asyncio.create_task(self._cleanup_old_metrics())

            log.info("📊 Metrics collector initialized")

        except Exception as e:
            log.error(f"❌ Failed to initialize metrics collector: {e}")
            raise

    async def _setup_default_alerts(self):
        """Setup default alerting rules"""
        default_rules = {
            "slow_queries": {
                "threshold": 5,
                "level": "warning",
                "message": "High number of slow queries detected",
                "check_interval": 300,  # 5 minutes
            },
            "memory_usage": {
                "threshold": 80,
                "level": "warning",
                "message": "High memory usage detected",
                "check_interval": 60,  # 1 minute
            },
            "cpu_usage": {
                "threshold": 85,
                "level": "error",
                "message": "High CPU usage detected",
                "check_interval": 60,  # 1 minute
            },
            "error_rate": {
                "threshold": 10,
                "level": "critical",
                "message": "High error rate detected",
                "check_interval": 300,  # 5 minutes
            },
            "database_connections": {
                "threshold": 90,
                "level": "warning",
                "message": "High database connection usage",
                "check_interval": 120,  # 2 minutes
            },
            "queue_size": {
                "threshold": 1000,
                "level": "error",
                "message": "Large job queue detected",
                "check_interval": 120,  # 2 minutes
            },
            "redis_memory": {
                "threshold": 85,
                "level": "warning",
                "message": "High Redis memory usage",
                "check_interval": 300,  # 5 minutes
            },
        }

        for rule_name, rule_config in default_rules.items():
            self.add_alert_rule(rule_name, rule_config)

    def add_alert_rule(self, name: str, rule: Dict[str, Any]):
        """Add an alert rule"""
        rule.setdefault("enabled", True)
        rule.setdefault("check_interval", 300)
        rule.setdefault("consecutive_checks", 1)
        rule.setdefault("cooldown", 600)  # 10 minutes cooldown

        self._alerts_rules[name] = rule

    def remove_alert_rule(self, name: str):
        """Remove an alert rule"""
        self._alerts_rules.pop(name, None)

    async def increment(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Increment a counter metric"""
        if not self._enabled:
            return

        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp or datetime.utcnow(),
            tags=tags or {}
        )

        await self._add_metric(metric)

    async def gauge(
        self,
        name: str,
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Set a gauge metric"""
        if not self._enabled:
            return

        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp or datetime.utcnow(),
            tags=tags or {}
        )

        await self._add_metric(metric)

    async def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Record a histogram metric"""
        if not self._enabled:
            return

        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            timestamp=timestamp or datetime.utcnow(),
            tags=tags or {}
        )

        await self._add_metric(metric)

    async def timer(
        self,
        name: str,
        duration: float,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Record a timer metric"""
        if not self._enabled:
            return

        metric = Metric(
            name=f"{name}_duration",
            value=duration,
            metric_type=MetricType.TIMER,
            timestamp=timestamp or datetime.utcnow(),
            tags=tags or {}
        )

        await self._add_metric(metric)

        # Also increment the counter
        await self.increment(f"{name}_count", tags=tags, timestamp=timestamp)

    async def _add_metric(self, metric: Metric):
        """Add a metric to the collection"""
        try:
            # Add to local buffer
            if metric.name not in self._metrics:
                self._metrics[metric.name] = []

            self._metrics[metric.name].append(metric)

            # Flush if batch size reached
            if len(self._metrics[metric.name]) >= self._batch_size:
                await self._flush_metric(metric.name)

            # Check if it's time to flush all metrics
            if time.time() - self._last_flush >= self._flush_interval:
                await self._flush_all_metrics()

        except Exception as e:
            log.error(f"❌ Failed to add metric {metric.name}: {e}")

    async def _flush_metric(self, metric_name: str):
        """Flush a specific metric to Redis"""
        if metric_name not in self._metrics or not self._metrics[metric_name]:
            return

        try:
            metrics = self._metrics[metric_name]
            redis_key = f"{self._prefix}metrics:{metric_name}"

            # Store metrics in Redis sorted set by timestamp
            pipe = cache_manager._redis.pipeline()
            for metric in metrics:
                metric_data = json.dumps(metric.to_dict())
                timestamp = metric.timestamp.timestamp()
                pipe.zadd(redis_key, {metric_data: timestamp})

            # Trim old metrics
            cutoff_time = time.time() - (self._retention_hours * 3600)
            pipe.zremrangebyscore(redis_key, 0, cutoff_time)

            await pipe.execute()

            # Clear local buffer
            self._metrics[metric_name].clear()

            log.debug(f"📊 Flushed {len(metrics)} metrics for {metric_name}")

        except Exception as e:
            log.error(f"❌ Failed to flush metric {metric_name}: {e}")

    async def _flush_all_metrics(self):
        """Flush all metrics to Redis"""
        for metric_name in list(self._metrics.keys()):
            await self._flush_metric(metric_name)

        self._last_flush = time.time()

    async def _periodic_flush(self):
        """Periodic flush task"""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_all_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"❌ Error in periodic flush: {e}")

    async def _system_monitoring(self):
        """System monitoring task"""
        while True:
            try:
                await asyncio.sleep(60)  # Monitor every minute

                # System metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                await self.gauge("system_cpu_percent", cpu_percent, {"unit": "percent"})
                await self.gauge("system_memory_percent", memory.percent, {"unit": "percent"})
                await self.gauge("system_memory_bytes", memory.used, {"unit": "bytes"})
                await self.gauge("system_disk_percent", (disk.used / disk.total) * 100, {"unit": "percent"})

                # Process metrics
                process = psutil.Process()
                await self.gauge("process_memory_rss", process.memory_info().rss, {"unit": "bytes"})
                await self.gauge("process_memory_vms", process.memory_info().vms, {"unit": "bytes"})
                await self.gauge("process_cpu_percent", process.cpu_percent(), {"unit": "percent"})

                # Check alerts
                await self._check_alerts()

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"❌ Error in system monitoring: {e}")

    async def _check_alerts(self):
        """Check alert conditions and generate alerts"""
        try:
            # Get recent metrics for alert checking
            recent_metrics = await self.get_recent_metrics(minutes=5)

            for rule_name, rule in self._alerts_rules.items():
                if not rule.get("enabled", True):
                    continue

                alert_triggered = await self._evaluate_alert_rule(rule_name, rule, recent_metrics)
                if alert_triggered:
                    await self._create_alert(alert_triggered)

        except Exception as e:
            log.error(f"❌ Error checking alerts: {e}")

    async def _evaluate_alert_rule(
        self,
        rule_name: str,
        rule: Dict[str, Any],
        recent_metrics: Dict[str, List[Metric]]
    ) -> Optional[Alert]:
        """Evaluate an alert rule"""
        try:
            threshold = rule["threshold"]
            level = AlertLevel(rule["level"])
            message = rule["message"]

            # Different evaluation logic for different rules
            if rule_name == "slow_queries":
                slow_queries = [
                    m for m in recent_metrics.get("slow_queries", [])
                    if m.value > 0
                ]
                if len(slow_queries) >= threshold:
                    return Alert(
                        name=rule_name,
                        level=level,
                        message=message,
                        timestamp=datetime.utcnow(),
                        value=len(slow_queries),
                        threshold=threshold
                    )

            elif rule_name == "memory_usage":
                memory_metrics = recent_metrics.get("system_memory_percent", [])
                if memory_metrics and memory_metrics[-1].value >= threshold:
                    return Alert(
                        name=rule_name,
                        level=level,
                        message=message,
                        timestamp=datetime.utcnow(),
                        value=memory_metrics[-1].value,
                        threshold=threshold
                    )

            elif rule_name == "cpu_usage":
                cpu_metrics = recent_metrics.get("system_cpu_percent", [])
                if cpu_metrics and cpu_metrics[-1].value >= threshold:
                    return Alert(
                        name=rule_name,
                        level=level,
                        message=message,
                        timestamp=datetime.utcnow(),
                        value=cpu_metrics[-1].value,
                        threshold=threshold
                    )

            elif rule_name == "error_rate":
                total_requests = len([
                    m for m in recent_metrics.get("http_requests_total", [])
                ])
                total_errors = len([
                    m for m in recent_metrics.get("http_requests_error", [])
                ])

                if total_requests > 0:
                    error_rate = (total_errors / total_requests) * 100
                    if error_rate >= threshold:
                        return Alert(
                            name=rule_name,
                            level=level,
                            message=message,
                            timestamp=datetime.utcnow(),
                            value=error_rate,
                            threshold=threshold
                        )

            return None

        except Exception as e:
            log.error(f"❌ Error evaluating alert rule {rule_name}: {e}")
            return None

    async def _create_alert(self, alert: Alert):
        """Create and store an alert"""
        try:
            # Check cooldown
            recent_alerts = await self.get_recent_alerts(minutes=10)
            similar_alerts = [
                a for a in recent_alerts
                if a.name == alert.name and a.level == alert.level
            ]

            if similar_alerts:
                log.info(f"📊 Alert {alert.name} in cooldown period, skipping")
                return

            # Store alert
            self._alerts.append(alert)

            # Store in Redis
            redis_key = f"{self._prefix}alerts"
            alert_data = json.dumps(alert.to_dict())
            await cache_manager._redis.zadd(
                redis_key,
                {alert_data: alert.timestamp.timestamp()}
            )

            # Trim old alerts
            cutoff_time = time.time() - (24 * 3600)  # Keep 24 hours of alerts
            await cache_manager._redis.zremrangebyscore(redis_key, 0, cutoff_time)

            log.warning(f"🚨 Alert created: {alert.name} - {alert.message}")

            # Here you could also send notifications (email, Slack, etc.)

        except Exception as e:
            log.error(f"❌ Failed to create alert: {e}")

    async def _cleanup_old_metrics(self):
        """Cleanup old metrics from Redis"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                cutoff_time = time.time() - (self._retention_hours * 3600)

                # Get all metric keys
                pattern = f"{self._prefix}metrics:*"
                keys = await cache_manager._redis.keys(pattern)

                for key in keys:
                    try:
                        await cache_manager._redis.zremrangebyscore(key, 0, cutoff_time)
                    except Exception as e:
                        log.error(f"❌ Error cleaning up key {key}: {e}")

                log.debug(f"🧹 Cleaned up old metrics (older than {self._retention_hours}h)")

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"❌ Error in metrics cleanup: {e}")

    async def get_metrics(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Metric]:
        """Get metrics for a specific name"""
        try:
            redis_key = f"{self._prefix}metrics:{name}"

            if start_time or end_time:
                start_timestamp = start_time.timestamp() if start_time else 0
                end_timestamp = end_time.timestamp() if end_time else time.time()

                metric_data = await cache_manager._redis.zrangebyscore(
                    redis_key,
                    start_timestamp,
                    end_timestamp,
                    start=0,
                    num=limit,
                    withscores=True
                )
            else:
                metric_data = await cache_manager._redis.zrevrange(
                    redis_key,
                    0,
                    limit - 1,
                    withscores=True
                )

            metrics = []
            for data, timestamp in metric_data:
                try:
                    metric_dict = json.loads(data.decode('utf-8'))
                    metrics.append(Metric.from_dict(metric_dict))
                except Exception as e:
                    log.error(f"❌ Error parsing metric data: {e}")

            return metrics

        except Exception as e:
            log.error(f"❌ Error getting metrics for {name}: {e}")
            return []

    async def get_recent_metrics(self, minutes: int = 60) -> Dict[str, List[Metric]]:
        """Get recent metrics for all types"""
        try:
            start_time = datetime.utcnow() - timedelta(minutes=minutes)
            end_time = datetime.utcnow()

            # Get all metric keys
            pattern = f"{self._prefix}metrics:*"
            keys = await cache_manager._redis.keys(pattern)

            result = {}
            for key in keys:
                try:
                    metric_name = key.decode('utf-8').replace(f"{self._prefix}metrics:", "")
                    metrics = await self.get_metrics(metric_name, start_time, end_time)
                    if metrics:
                        result[metric_name] = metrics
                except Exception as e:
                    log.error(f"❌ Error getting metrics from {key}: {e}")

            return result

        except Exception as e:
            log.error(f"❌ Error getting recent metrics: {e}")
            return {}

    async def get_recent_alerts(self, minutes: int = 60) -> List[Alert]:
        """Get recent alerts"""
        try:
            redis_key = f"{self._prefix}alerts"
            start_time = time.time() - (minutes * 60)

            alert_data = await cache_manager._redis.zrangebyscore(
                redis_key,
                start_time,
                time.time(),
                withscores=True
            )

            alerts = []
            for data, timestamp in alert_data:
                try:
                    alert_dict = json.loads(data.decode('utf-8'))
                    alerts.append(Alert.from_dict(alert_dict))
                except Exception as e:
                    log.error(f"❌ Error parsing alert data: {e}")

            return alerts

        except Exception as e:
            log.error(f"❌ Error getting recent alerts: {e}")
            return []

    async def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            recent_metrics = await self.get_recent_metrics(minutes=hours * 60)
            recent_alerts = await self.get_recent_alerts(minutes=hours * 60)

            summary = {
                "time_range_hours": hours,
                "total_metrics": sum(len(metrics) for metrics in recent_metrics.values()),
                "metric_types": len(recent_metrics),
                "total_alerts": len(recent_alerts),
                "alert_levels": {
                    level.value: len([a for a in recent_alerts if a.level == level])
                    for level in AlertLevel
                },
                "metrics_by_type": {
                    name: {
                        "count": len(metrics),
                        "latest": metrics[-1].timestamp.isoformat() if metrics else None,
                        "avg_value": sum(m.value for m in metrics) / len(metrics) if metrics else 0
                    }
                    for name, metrics in recent_metrics.items()
                },
                "alerts": [alert.to_dict() for alert in recent_alerts[-10:]]  # Last 10 alerts
            }

            return summary

        except Exception as e:
            log.error(f"❌ Error getting metrics summary: {e}")
            return {"error": str(e)}

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data with metrics and system info"""
        try:
            # Get recent metrics
            recent_metrics = await self.get_recent_metrics(minutes=30)

            # Get system info
            system_info = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
            }

            # Get cache stats
            cache_stats = await cache_manager.get_cache_stats()

            # Get recent alerts
            recent_alerts = await self.get_recent_alerts(minutes=60)

            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": system_info,
                "cache": cache_stats,
                "metrics": {
                    name: {
                        "count": len(metrics),
                        "latest_value": metrics[-1].value if metrics else 0,
                        "avg_value": sum(m.value for m in metrics) / len(metrics) if metrics else 0,
                        "unit": metrics[0].unit if metrics else None
                    }
                    for name, metrics in recent_metrics.items()
                    if metrics
                },
                "alerts": {
                    "total": len(recent_alerts),
                    "by_level": {
                        level.value: len([a for a in recent_alerts if a.level == level])
                        for level in AlertLevel
                    },
                    "recent": [alert.to_dict() for alert in recent_alerts[-5:]]
                },
                "settings": {
                    "metrics_enabled": self._enabled,
                    "retention_hours": self._retention_hours,
                    "flush_interval": self._flush_interval,
                    "alert_rules_count": len(self._alerts_rules),
                }
            }

            return dashboard_data

        except Exception as e:
            log.error(f"❌ Error getting dashboard data: {e}")
            return {"error": str(e)}

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Decorator for timing function execution
def track_time(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator to track function execution time"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    await metrics_collector.timer(metric_name, duration, tags)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    await metrics_collector.timer(f"{metric_name}_error", duration, tags)
                    raise
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    # For sync functions, we need to run async
                    asyncio.create_task(metrics_collector.timer(metric_name, duration, tags))
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    asyncio.create_task(metrics_collector.timer(f"{metric_name}_error", duration, tags))
                    raise
            return sync_wrapper

        return decorator