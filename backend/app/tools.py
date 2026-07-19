# Defines the tools Ghost can use.

from datetime import datetime
import csv
from io import StringIO
import json
from langchain_core.tools import tool
import subprocess #open_calculator
import platform   #open_calculator
import os

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


@tool
def list_running_processes(filter_text: str = "", max_results: int = 50) -> str:
    """Lists running Windows processes with their PID, name, and memory use.

    Use this to investigate processes before ending one. filter_text optionally
    filters by process name, and max_results is limited to 1-100.
    """
    if platform.system() != "Windows":
        return "Process investigation is currently supported on Windows only."

    max_results = max(1, min(max_results, 100))
    try:
        completed = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=True,
        )
        needle = filter_text.casefold().strip()
        processes = []
        for row in csv.reader(StringIO(completed.stdout)):
            if len(row) < 5 or not row[1].isdigit():
                continue
            if needle and needle not in row[0].casefold():
                continue
            processes.append({
                "name": row[0],
                "pid": int(row[1]),
                "memory": row[4],
            })
            if len(processes) >= max_results:
                break

        return json.dumps({
            "filter": filter_text,
            "count": len(processes),
            "processes": processes,
        })
    except subprocess.CalledProcessError as error:
        return f"Failed to list processes: {error.stderr.strip() or error}"
    except Exception as error:
        return f"Failed to list processes: {error}"


@tool
def terminate_process(pid: int, force: bool = False) -> str:
    """Ends one exact Windows process by PID.

    Only use after the user has explicitly confirmed the PID from a process
    listing. Set force to true only when the user explicitly asks to force it.
    Never use this for PID 0, PID 4, or Ghost's own process.
    """
    if platform.system() != "Windows":
        return "Process termination is currently supported on Windows only."
    if pid in (0, 4, os.getpid()):
        return "Refusing to terminate a protected system process or Ghost itself."
    if pid < 1:
        return "A process PID must be a positive integer."

    try:
        check = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=True,
        )
        rows = list(csv.reader(StringIO(check.stdout)))
        if not rows or len(rows[0]) < 2 or not rows[0][1].isdigit():
            return f"No running process was found with PID {pid}."
        process_name = rows[0][0]

        command = ["taskkill", "/PID", str(pid)]
        if force:
            command.append("/F")
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode == 0:
            return f"Ended {process_name} (PID {pid})."
        return f"Could not end {process_name} (PID {pid}): {completed.stderr.strip() or completed.stdout.strip()}"
    except subprocess.CalledProcessError as error:
        return f"Failed to inspect PID {pid}: {error.stderr.strip() or error}"
    except Exception as error:
        return f"Failed to end PID {pid}: {error}"

TOOLS = [
    get_current_time,
    open_calculator,
    open_browser,
    list_running_processes,
    terminate_process,
]
