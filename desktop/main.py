import os
import sys
from pathlib import Path

import PySide6
from PySide6.QtCore import QObject, Property, QThread, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from api import ask


# QML plugins live below PySide6/qml while their Qt DLL dependencies live in
# the package root. Windows does not search that parent directory by default.
_qt_dll_directory = None
if sys.platform == "win32":
    pyside_directory = Path(PySide6.__file__).resolve().parent
    os.environ["PATH"] = f"{pyside_directory}{os.pathsep}{os.environ['PATH']}"
    _qt_dll_directory = os.add_dll_directory(str(pyside_directory))


class ChatWorker(QObject):
    responseReady = Signal(str)
    requestFailed = Signal(str)
    finished = Signal()

    def __init__(self, message: str):
        super().__init__()
        self._message = message

    @Slot()
    def run(self) -> None:
        try:
            self.responseReady.emit(ask(self._message))
        except Exception as error:
            self.requestFailed.emit(str(error) or "The request could not be completed.")
        finally:
            self.finished.emit()


class ChatController(QObject):
    messageReceived = Signal(str)
    requestFailed = Signal(str)
    busyChanged = Signal(bool)

    def __init__(self):
        super().__init__()
        self._busy = False
        self._threads: set[QThread] = set()
        self._workers: dict[QThread, ChatWorker] = {}

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Slot(str)
    def send(self, message: str) -> None:
        message = message.strip()
        if not message or self._busy:
            return

        self._set_busy(True)
        thread = QThread(self)
        worker = ChatWorker(message)
        worker.moveToThread(thread)
        self._threads.add(thread)
        self._workers[thread] = worker

        thread.started.connect(worker.run)
        worker.responseReady.connect(self.messageReceived)
        worker.requestFailed.connect(self.requestFailed)
        worker.finished.connect(self._finish_request)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()

    @Slot()
    def _finish_request(self) -> None:
        self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        if self._busy == busy:
            return
        self._busy = busy
        self.busyChanged.emit(busy)

    def _cleanup_thread(self, thread: QThread) -> None:
        self._threads.discard(thread)
        self._workers.pop(thread, None)

    @Slot()
    def shutdown(self) -> None:
        for thread in self._threads:
            thread.quit()
        for thread in self._threads:
            thread.wait(1000)


QQuickStyle.setStyle("Basic")
app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()
controller = ChatController()
app.aboutToQuit.connect(controller.shutdown)
engine.rootContext().setContextProperty("chat", controller)

qml_file = Path(__file__).resolve().parent / "ui" / "Main.qml"
engine.load(qml_file.as_uri())

if not engine.rootObjects():
    sys.exit(-1)

sys.exit(app.exec())
