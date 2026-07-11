# Defines the tools Ghost can use.

from datetime import datetime
from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """Returns the current local time."""

    return datetime.now().strftime("%I:%M %p")