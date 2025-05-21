# overlay.py
from __future__ import annotations
import asyncio
from typing import Callable, Mapping

from PyQt5 import QtWidgets, QtCore, QtGui
from qasync  import asyncSlot


# ──────────────────────────── Control (top-bar) ────────────────────────────
class ControlOverlay(QtWidgets.QWidget):
    """Start / Stop / Terminate bar – draggable, always on top."""
    def __init__(
        self,
        loop:        asyncio.AbstractEventLoop,
        on_start:    Callable[[], None | asyncio.Future],
        on_stop:     Callable[[], None | asyncio.Future],
        on_terminate:Callable[[], None | asyncio.Future],
        *,
        parent=None
    ):
        super().__init__(parent)
        self.loop = loop
        self.on_start     = on_start
        self.on_stop      = on_stop
        self.on_terminate = on_terminate

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 38)

        lay   = QtWidgets.QHBoxLayout(self); lay.setContentsMargins(5, 5, 5, 5)
        self.btn_start = QtWidgets.QPushButton("Start")
        self.btn_stop  = QtWidgets.QPushButton("Stop");  self.btn_stop.setEnabled(False)
        self.btn_term  = QtWidgets.QPushButton("Terminate")
        for b in (self.btn_start, self.btn_stop, self.btn_term): lay.addWidget(b)

        self.btn_start.clicked.connect(self._start)
        self.btn_stop .clicked.connect(self._stop )
        self.btn_term .clicked.connect(self._term )

    # drag support
    def mousePressEvent(self, ev): self._drag = ev.globalPos()
    def mouseMoveEvent (self, ev):
        delta = ev.globalPos() - self._drag
        self.move(self.x()+delta.x(), self.y()+delta.y())
        self._drag = ev.globalPos()

    # button wrappers
    @asyncSlot()
    async def _start(self):
        self.btn_start.setEnabled(False); self.btn_stop.setEnabled(True)
        if asyncio.iscoroutinefunction(self.on_start):
            await self.on_start()
        else:
            self.on_start()

    @asyncSlot()
    async def _stop(self):
        self.btn_start.setEnabled(True);  self.btn_stop.setEnabled(False)
        if asyncio.iscoroutinefunction(self.on_stop):
            await self.on_stop()
        else:
            self.on_stop()

    @asyncSlot()
    async def _term(self):
        if asyncio.iscoroutinefunction(self.on_terminate):
            await self.on_terminate()
        else:
            self.on_terminate()


# ───────────────────────────── Choice overlay ──────────────────────────────
class ChoiceOverlay(QtWidgets.QWidget):
    """
    Centre-screen, frameless, **transparent** widget that shows three choice
    buttons.  Returns the chosen index via the supplied future.
    """
    def __init__(self, future: asyncio.Future, choices: Mapping[int, str], *, parent=None):
        super().__init__(parent, QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.future = future

        # auto-size to content & centre
        btns = []
        vbox = QtWidgets.QVBoxLayout(self); vbox.setSpacing(10); vbox.setContentsMargins(20, 20, 20, 20)
        for idx, text in choices.items():
            b = QtWidgets.QPushButton(text)
            b.clicked.connect(lambda _, i=idx: self._choose(i))
            btns.append(b); vbox.addWidget(b)

        self.adjustSize()
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.left() + (screen.width()  - self.width() )//2,
            screen.top () + (screen.height() - self.height())//2,
        )

    def _choose(self, idx: int):
        if not self.future.done():
            self.future.set_result(idx)
        self.close()
