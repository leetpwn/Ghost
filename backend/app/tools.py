# Defines the tools Ghost can use.

from datetime import datetime
from langchain_core.tools import tool
import subprocess #open_calculator
import platform   #open_calculator



@tool
def get_current_time() -> str:
    """Returns the current local time."""

    return datetime.now().strftime("%I:%M %p")

@tool
def open_calculator() -> str:
    """Opens the calculator application on the user's system."""
    try:
        if platform.system() == "Windows":
            subprocess.Popen("calc.exe")
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", "Calculator"])
        elif platform.system() == "Linux":
            subprocess.Popen(["gnome-calculator"])  # For GNOME desktop
        else:
            return "Unsupported operating system."
        return "Calculator opened successfully."
    except Exception as e:
        return f"Failed to open calculator: {e}"
    

TOOLS = [
    get_current_time,
    open_calculator
]