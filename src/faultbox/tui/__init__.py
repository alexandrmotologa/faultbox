"""Terminal user interface package."""

from faultbox.tui.app import run_dashboard
from faultbox.tui.widgets import make_dashboard_layout

__all__ = [
    "make_dashboard_layout",
    "run_dashboard",
]
