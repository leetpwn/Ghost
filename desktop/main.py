import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import PySide6


# ============================================================
# PATHS
# ============================================================

DESKTOP_ROOT = (
    Path(__file__)
    .resolve()
    .parent
)

GHOST_ROOT = (
    DESKTOP_ROOT.parent
)

BACKEND_ROOT = (
    GHOST_ROOT / "backend"
)

BACKEND_PYTHON = (
    BACKEND_ROOT
    / ".venv"
    / "Scripts"
    / "python.exe"
)

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000


# ============================================================
# QT DLL / QML SETUP
# ============================================================

_qt_dll_directory = None

pyside_directory = (
    Path(PySide6.__file__)
    .resolve()
    .parent
)

if sys.platform == "win32":

    os.environ["PATH"] = (
        f"{pyside_directory}"
        f"{os.pathsep}"
        f"{os.environ['PATH']}"
    )

    _qt_dll_directory = (
        os.add_dll_directory(
            str(pyside_directory)
        )
    )


from PySide6.QtCore import (
    QEvent,
    QObject,
    Property,
    QThread,
    QTimer,
    QUrl,
    Signal,
    Slot,
)

from PySide6.QtGui import (
    QAction,
    QDesktopServices,
    QIcon,
    QPainter,
    QPixmap,
)

from PySide6.QtQml import (
    QQmlApplicationEngine,
)

from PySide6.QtQuickControls2 import (
    QQuickStyle,
)

from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QStyle,
    QSystemTrayIcon,
)

from api import ask


# ============================================================
# WINDOWS STARTUP
# ============================================================

def enable_windows_startup() -> bool:
    """
    Register Ghost under the current user's Windows Run key.

    Ghost will automatically start after the user signs into
    Windows.

    Uses pythonw.exe when possible so no console window appears.
    """

    if sys.platform != "win32":
        return False

    try:
        import winreg

        python_executable = (
            Path(sys.executable)
            .resolve()
        )

        pythonw_executable = (
            python_executable.parent
            / "pythonw.exe"
        )

        if pythonw_executable.exists():
            launcher = pythonw_executable
        else:
            launcher = python_executable

        main_file = (
            DESKTOP_ROOT / "main.py"
        )

        command = (
            f'"{launcher}" '
            f'"{main_file}"'
        )

        registry_path = (
            r"Software\Microsoft\Windows"
            r"\CurrentVersion\Run"
        )

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            registry_path,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:

            winreg.SetValueEx(
                key,
                "Ghost",
                0,
                winreg.REG_SZ,
                command,
            )

        return True

    except Exception as error:

        print(
            "[Ghost Startup] "
            f"Could not enable startup: {error}"
        )

        return False


# ============================================================
# BACKEND MANAGER
# ============================================================

class BackendManager(QObject):
    """
    Ensures Ghost's FastAPI backend is available.

    If another backend is already listening on 127.0.0.1:8000,
    Ghost leaves it alone.

    If Ghost starts the backend itself, Ghost also terminates
    that child process during a full application shutdown.
    """

    def __init__(self):
        super().__init__()

        self._process = None

        self._health_timer = QTimer(
            self
        )

        self._health_timer.setInterval(
            10000
        )

        self._health_timer.timeout.connect(
            self.ensure_running
        )

    def start(
        self,
    ) -> None:

        self.ensure_running()

        self._health_timer.start()

    def _port_open(
        self,
    ) -> bool:

        try:

            with socket.create_connection(
                (
                    BACKEND_HOST,
                    BACKEND_PORT,
                ),
                timeout=0.25,
            ):
                return True

        except OSError:
            return False

    @Slot()
    def ensure_running(
        self,
    ) -> None:

        if self._port_open():
            return

        if (
            self._process is not None
            and self._process.poll()
            is None
        ):
            return

        if not BACKEND_PYTHON.exists():

            print(
                "[Ghost Backend] "
                "Backend Python was not found at:"
            )

            print(
                BACKEND_PYTHON
            )

            return

        print(
            "[Ghost Backend] "
            "Starting FastAPI backend..."
        )

        creation_flags = 0

        if sys.platform == "win32":
            creation_flags = (
                subprocess.CREATE_NO_WINDOW
            )

        try:

            self._process = subprocess.Popen(
                [
                    str(BACKEND_PYTHON),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    BACKEND_HOST,
                    "--port",
                    str(BACKEND_PORT),
                ],

                cwd=str(
                    BACKEND_ROOT
                ),

                stdout=subprocess.DEVNULL,

                stderr=subprocess.DEVNULL,

                creationflags=
                    creation_flags,
            )

        except Exception as error:

            print(
                "[Ghost Backend] "
                f"Could not start backend: {error}"
            )

    @Slot()
    def shutdown(
        self,
    ) -> None:

        self._health_timer.stop()

        if self._process is None:
            return

        if (
            self._process.poll()
            is not None
        ):
            return

        try:

            self._process.terminate()

            self._process.wait(
                timeout=3
            )

        except Exception:

            try:
                self._process.kill()

            except Exception:
                pass


# ============================================================
# CHAT WORKER
# ============================================================

class ChatWorker(QObject):

    responseReady = Signal(str)

    requestFailed = Signal(str)

    finished = Signal()


    def __init__(
        self,
        message: str,
    ):
        super().__init__()

        self._message = message


    @Slot()
    def run(
        self,
    ) -> None:

        try:

            self.responseReady.emit(
                ask(
                    self._message
                )
            )

        except Exception as error:

            self.requestFailed.emit(
                str(error)
                or
                "The request could not be completed."
            )

        finally:

            self.finished.emit()


# ============================================================
# CHAT CONTROLLER
# ============================================================

class ChatController(QObject):

    messageReceived = Signal(str)

    requestFailed = Signal(str)

    busyChanged = Signal(bool)


    def __init__(
        self,
    ):
        super().__init__()

        self._busy = False

        self._threads: set[
            QThread
        ] = set()

        self._workers: dict[
            QThread,
            ChatWorker,
        ] = {}


    @Property(
        bool,
        notify=busyChanged,
    )
    def busy(
        self,
    ) -> bool:

        return self._busy


    @Slot(str)
    def send(
        self,
        message: str,
    ) -> None:

        message = message.strip()

        if (
            not message
            or self._busy
        ):
            return

        self._set_busy(
            True
        )

        thread = QThread(
            self
        )

        worker = ChatWorker(
            message
        )

        worker.moveToThread(
            thread
        )

        self._threads.add(
            thread
        )

        self._workers[
            thread
        ] = worker

        thread.started.connect(
            worker.run
        )

        worker.responseReady.connect(
            self.messageReceived
        )

        worker.requestFailed.connect(
            self.requestFailed
        )

        worker.finished.connect(
            self._finish_request
        )

        worker.finished.connect(
            thread.quit
        )

        worker.finished.connect(
            worker.deleteLater
        )

        thread.finished.connect(
            thread.deleteLater
        )

        thread.finished.connect(
            lambda:
                self._cleanup_thread(
                    thread
                )
        )

        thread.start()


    @Slot()
    def _finish_request(
        self,
    ) -> None:

        self._set_busy(
            False
        )


    def _set_busy(
        self,
        busy: bool,
    ) -> None:

        if self._busy == busy:
            return

        self._busy = busy

        self.busyChanged.emit(
            busy
        )


    def _cleanup_thread(
        self,
        thread: QThread,
    ) -> None:

        self._threads.discard(
            thread
        )

        self._workers.pop(
            thread,
            None,
        )


    @Slot()
    def shutdown(
        self,
    ) -> None:

        for thread in list(
            self._threads
        ):
            thread.quit()

        for thread in list(
            self._threads
        ):
            thread.wait(
                1000
            )


# ============================================================
# NETWORK WORKER
# ============================================================

class NetworkWorker(QObject):

    connectionsReady = Signal(
        list
    )

    alertsReady = Signal(
        list
    )

    requestFailed = Signal(
        str
    )

    finished = Signal()


    CONNECTIONS_URL = (
        "http://127.0.0.1:8000/"
        "network/connections"
        "?scope=PUBLIC"
        "&lifecycle=ACTIVE"
    )


    ALERTS_URL = (
        "http://127.0.0.1:8000/"
        "network/alerts"
    )


    @staticmethod
    def _get_json(
        url: str,
    ) -> dict:

        request = (
            urllib.request.Request(
                url,

                method="GET",

                headers={
                    "Accept":
                        "application/json",
                },
            )
        )

        with urllib.request.urlopen(
            request,
            timeout=3,
        ) as response:

            raw_data = (
                response.read()
            )

        return json.loads(
            raw_data.decode(
                "utf-8"
            )
        )


    @Slot()
    def run(
        self,
    ) -> None:

        try:

            connection_payload = (
                self._get_json(
                    self.CONNECTIONS_URL
                )
            )

            connections = (
                connection_payload.get(
                    "connections",
                    [],
                )
            )

            if not isinstance(
                connections,
                list,
            ):
                connections = []

            self.connectionsReady.emit(
                connections
            )


            alert_payload = (
                self._get_json(
                    self.ALERTS_URL
                )
            )

            alerts = (
                alert_payload.get(
                    "alerts",
                    [],
                )
            )

            if not isinstance(
                alerts,
                list,
            ):
                alerts = []

            self.alertsReady.emit(
                alerts
            )


        except urllib.error.URLError as error:

            self.requestFailed.emit(
                "Backend unavailable: "
                f"{error}"
            )


        except Exception as error:

            self.requestFailed.emit(
                str(error)
                or
                "Unable to retrieve network activity."
            )


        finally:

            self.finished.emit()


# ============================================================
# NETWORK CONTROLLER
# ============================================================

class NetworkController(QObject):

    connectionsReceived = Signal(
        list
    )

    alertReceived = Signal(
        dict
    )

    requestFailed = Signal(
        str
    )

    busyChanged = Signal(
        bool
    )

    connectionCountChanged = Signal(
        int
    )


    def __init__(
        self,
    ):
        super().__init__()

        self._busy = False

        self._connection_count = 0

        self._threads: set[
            QThread
        ] = set()

        self._workers: dict[
            QThread,
            NetworkWorker,
        ] = {}


        self._timer = QTimer(
            self
        )

        self._timer.setInterval(
            3000
        )

        self._timer.timeout.connect(
            self.refresh
        )

        self._timer.start()


        QTimer.singleShot(
            1200,
            self.refresh,
        )


    @Property(
        bool,
        notify=busyChanged,
    )
    def busy(
        self,
    ) -> bool:

        return self._busy


    @Property(
        int,
        notify=connectionCountChanged,
    )
    def connectionCount(
        self,
    ) -> int:

        return self._connection_count


    @Slot()
    def refresh(
        self,
    ) -> None:

        if self._busy:
            return

        self._set_busy(
            True
        )

        thread = QThread(
            self
        )

        worker = NetworkWorker()

        worker.moveToThread(
            thread
        )

        self._threads.add(
            thread
        )

        self._workers[
            thread
        ] = worker


        thread.started.connect(
            worker.run
        )

        worker.connectionsReady.connect(
            self._handle_connections
        )

        worker.alertsReady.connect(
            self._handle_alerts
        )

        worker.requestFailed.connect(
            self.requestFailed
        )

        worker.finished.connect(
            self._finish_request
        )

        worker.finished.connect(
            thread.quit
        )

        worker.finished.connect(
            worker.deleteLater
        )

        thread.finished.connect(
            thread.deleteLater
        )

        thread.finished.connect(
            lambda:
                self._cleanup_thread(
                    thread
                )
        )

        thread.start()


    @Slot(list)
    def _handle_connections(
        self,
        connections: list,
    ) -> None:

        count = len(
            connections
        )

        if (
            count
            != self._connection_count
        ):

            self._connection_count = count

            self.connectionCountChanged.emit(
                count
            )

        self.connectionsReceived.emit(
            connections
        )


    @Slot(list)
    def _handle_alerts(
        self,
        alerts: list,
    ) -> None:

        if not alerts:
            return

        for alert in alerts:

            if not isinstance(
                alert,
                dict,
            ):
                continue

            print(
                "[Ghost Desktop] "
                "Displaying network alert: "
                f"{alert.get('process_name')} -> "
                f"{alert.get('remote_ip')}"
            )

            self.alertReceived.emit(
                alert
            )


    def emit_test_alert(
        self,
    ) -> None:

        test_alert = {
            "type":
                "TEST_NETWORK_ALERT",

            "severity":
                "WARNING",

            "title":
                "Ghost notification test",

            "process_name":
                "powershell.exe",

            "process_path":
                (
                    r"C:\Windows\System32"
                    r"\WindowsPowerShell\v1.0"
                    r"\powershell.exe"
                ),

            "pid":
                12345,

            "remote_ip":
                "203.0.113.10",

            "remote_port":
                443,

            "organization":
                "Ghost Test Network",

            "isp":
                "Ghost Test",

            "domain":
                "example.test",

            "asn":
                64500,

            "message":
                (
                    "Desktop notification "
                    "system is working."
                ),

            "virustotal_url":
                "",

            "created_at":
                "",
        }

        print(
            "[Ghost Desktop] "
            "Emitting test notification."
        )

        self.alertReceived.emit(
            test_alert
        )


    @Slot()
    def _finish_request(
        self,
    ) -> None:

        self._set_busy(
            False
        )


    def _set_busy(
        self,
        busy: bool,
    ) -> None:

        if self._busy == busy:
            return

        self._busy = busy

        self.busyChanged.emit(
            busy
        )


    def _cleanup_thread(
        self,
        thread: QThread,
    ) -> None:

        self._threads.discard(
            thread
        )

        self._workers.pop(
            thread,
            None,
        )


    @Slot(str)
    def openUrl(
        self,
        url: str,
    ) -> None:

        if not url:
            return

        QDesktopServices.openUrl(
            QUrl(url)
        )


    @Slot()
    def shutdown(
        self,
    ) -> None:

        self._timer.stop()

        for thread in list(
            self._threads
        ):
            thread.quit()

        for thread in list(
            self._threads
        ):
            thread.wait(
                1000
            )


# ============================================================
# MAIN-WINDOW CLOSE BEHAVIOR
# ============================================================

class MainWindowCloseFilter(QObject):
    """
    Clicking X hides Ghost instead of terminating it.

    This keeps the network monitor and notification system
    running in the tray.
    """

    def __init__(
        self,
        main_window,
    ):
        super().__init__()

        self._main_window = (
            main_window
        )


    def eventFilter(
        self,
        watched,
        event,
    ):

        if (
            watched
            is self._main_window
            and
            event.type()
            == QEvent.Close
        ):

            self._main_window.hide()

            return True

        return super().eventFilter(
            watched,
            event,
        )


# ============================================================
# TRAY CONTROLLER
# ============================================================

class TrayController(QObject):

    def __init__(
        self,
        app,
        main_window,
    ):
        super().__init__()

        self._app = app

        self._main_window = (
            main_window
        )

        self._tray = (
            QSystemTrayIcon(
                self
            )
        )

        self._tray.setIcon(
            self._create_icon()
        )

        self._tray.setToolTip(
            "Ghost — Running"
        )


        menu = QMenu()


        open_action = QAction(
            "Open Ghost",
            self,
        )

        open_action.triggered.connect(
            self.show_main_window
        )

        menu.addAction(
            open_action
        )


        status_action = QAction(
            "● Ghost is running",
            self,
        )

        status_action.setEnabled(
            False
        )

        menu.addAction(
            status_action
        )


        network_action = QAction(
            "● Network monitor active",
            self,
        )

        network_action.setEnabled(
            False
        )

        menu.addAction(
            network_action
        )


        startup_action = QAction(
            "✓ Start with Windows",
            self,
        )

        startup_action.setEnabled(
            False
        )

        menu.addAction(
            startup_action
        )


        menu.addSeparator()


        quit_action = QAction(
            "Quit Ghost",
            self,
        )

        quit_action.triggered.connect(
            self.quit_ghost
        )

        menu.addAction(
            quit_action
        )


        self._tray.setContextMenu(
            menu
        )

        self._tray.activated.connect(
            self._on_tray_activated
        )

        self._tray.show()


    def _create_icon(
        self,
    ) -> QIcon:

        # Use a built-in Windows/Qt icon so Ghost works
        # immediately without requiring an asset file.

        icon = (
            QApplication.style()
            .standardIcon(
                QStyle.SP_ComputerIcon
            )
        )

        return icon


    @Slot()
    def show_main_window(
        self,
    ) -> None:

        self._main_window.show()

        self._main_window.raise_()

        self._main_window.requestActivate()


    @Slot()
    def quit_ghost(
        self,
    ) -> None:

        self._tray.hide()

        self._app.quit()


    def _on_tray_activated(
        self,
        reason,
    ) -> None:

        if (
            reason
            == QSystemTrayIcon.DoubleClick
        ):

            self.show_main_window()


# ============================================================
# APPLICATION
# ============================================================

QQuickStyle.setStyle(
    "Basic"
)


app = QApplication(
    sys.argv
)

# Critical for tray applications:
#
# hiding the main window must not terminate Ghost.
app.setQuitOnLastWindowClosed(
    False
)


# ------------------------------------------------------------
# Enable Windows startup
# ------------------------------------------------------------

startup_enabled = (
    enable_windows_startup()
)

if startup_enabled:

    print(
        "[Ghost Startup] "
        "Ghost will start with Windows."
    )


# ------------------------------------------------------------
# Start / maintain backend
# ------------------------------------------------------------

backend_manager = (
    BackendManager()
)

backend_manager.start()


# ------------------------------------------------------------
# QML
# ------------------------------------------------------------

engine = (
    QQmlApplicationEngine()
)

engine.addImportPath(
    str(
        pyside_directory
        / "qml"
    )
)


chat_controller = (
    ChatController()
)

network_controller = (
    NetworkController()
)


engine.rootContext().setContextProperty(
    "chat",
    chat_controller,
)

engine.rootContext().setContextProperty(
    "network",
    network_controller,
)


main_qml = (
    DESKTOP_ROOT
    / "ui"
    / "Main.qml"
)

alert_qml = (
    DESKTOP_ROOT
    / "ui"
    / "NetworkAlert.qml"
)


# Load main window first so we can keep a direct reference.
engine.load(
    main_qml.as_uri()
)


root_objects = (
    engine.rootObjects()
)

if not root_objects:

    sys.exit(
        -1
    )


main_window = (
    root_objects[0]
)


# Prevent X from actually terminating Ghost.
close_filter = (
    MainWindowCloseFilter(
        main_window
    )
)

main_window.installEventFilter(
    close_filter
)


# Load always-on-top alert window.
engine.load(
    alert_qml.as_uri()
)


# ------------------------------------------------------------
# TRAY
# ------------------------------------------------------------

tray_controller = (
    TrayController(
        app,
        main_window,
    )
)


# ------------------------------------------------------------
# SHUTDOWN
# ------------------------------------------------------------

app.aboutToQuit.connect(
    chat_controller.shutdown
)

app.aboutToQuit.connect(
    network_controller.shutdown
)

app.aboutToQuit.connect(
    backend_manager.shutdown
)


# ------------------------------------------------------------
# OPTIONAL ALERT TEST
# ------------------------------------------------------------

if (
    os.environ.get(
        "GHOST_TEST_ALERT",
        "",
    )
    == "1"
):

    QTimer.singleShot(
        2000,
        network_controller.emit_test_alert,
    )


sys.exit(
    app.exec()
)