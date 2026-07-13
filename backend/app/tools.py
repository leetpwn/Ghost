# Defines the tools Ghost can use.

from datetime import datetime
from langchain_core.tools import tool
import subprocess #open_calculator
import platform   #open_calculator

DEFAULT_URL = "https://www.google.com"  # Default URL for the open_browser tool

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
    
@tool
def open_browser(url: str = DEFAULT_URL) -> str:
    """Opens the default web browser to a specified URL."""
    try:
        subprocess.Popen(["start", url], shell=True)

        return f"Browser opened to {url}."
    
    except Exception as e:
        return f"Failed to open browser: {e}"
    

TOOLS = [
    get_current_time,
    open_calculator,
    open_browser
]