"""Domain-level errors."""


class RoutifyError(Exception):
    """Base exception for Routify."""


class GraphLoadError(RoutifyError):
    """Failed to load road network data."""


class RoutingError(RoutifyError):
    """No valid route between endpoints."""
