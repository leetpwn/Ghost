from .monitor import NetworkMonitor


network_monitor = NetworkMonitor(
    poll_interval_seconds=2.0 #Can be adjusted to a different value if needed
)