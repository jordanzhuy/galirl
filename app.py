__version__ = "0.0.1"

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import sys, asyncio, signal, time, hashlib
from typing import Optional

import pyautogui, pyperclip, mss
import numpy as np
from PyQt5 import QtWidgets
from qasync import QEventLoop

from overlay import ControlOverlay, ChoiceOverlay
from mock_selection import MockSession
from selection_generation import DialogueSession
import mouse_lock

# ---------------------------------------------------------------------------
# low‑level helpers
# ---------------------------------------------------------------------------

def hash_region(img: np.ndarray) -> str:
    return hashlib.md5(img.tobytes()).hexdigest()


def capture_region(monitor) -> np.ndarray:
    with mss.mss() as sct:
        shot = np.array(sct.grab(monitor))
        return shot[:, :, :3]


def click_and_copy(x: int, y: int) -> str:
    mouse_lock.free()
    # triple‑click, Ctrl+C, return clipboard content
    for _ in range(3):
        pyautogui.click(x, y)
    pyautogui.hotkey("ctrl", "c")
    mouse_lock.control()
    return pyperclip.paste().strip()


def send_message(text: str):
    mouse_lock.free()
    pyautogui.click(399, 869)
    time.sleep(0.10)
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.05) 
    pyautogui.press("enter")
    mouse_lock.control()
    

# ---------------------------------------------------------------------------
# Conversation manager (stateful)
# ---------------------------------------------------------------------------

class ConversationManager:
    def __init__(self, region, bubble_click_pos, debug=False):
        self.region = region
        self.bubble_pos = bubble_click_pos
        self.session = MockSession() if debug else DialogueSession()
        self.session.init_session()
        self.user_selection: Optional[str] = None
        self.prev_hash: Optional[str] = None
        self.just_sent, self.skip_frames = False, 0
        self._task: Optional[asyncio.Task] = None
        print("Using " + ("DSAPI" if debug else "mock API"))
    # ----- callbacks for ControlOverlay -----
    def start(self):
        if not self._task:
            self._task = asyncio.create_task(self._watch_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def terminate(self, loop):
        await self.stop(); loop.stop()

    # ----- core loop -----
    async def _watch_loop(self, poll: float = 0.5):
        """Watch region for new bubbles, show choices, send reply."""
        print("[Watcher] started")
        self.prev_hash = hash_region(capture_region(self.region))
        loop = asyncio.get_running_loop()

        while True:
            await asyncio.sleep(poll)
            curr_hash = hash_region(capture_region(self.region))

            # ── 1.  Ignore identical frames ──────────────────────────────
            if curr_hash == self.prev_hash:
                continue

            # ── 2.  If we just sent a message, swallow *this* change only ─
            if self.just_sent:
                self.just_sent = False
                self.prev_hash = curr_hash
                continue

            # ── 3.  New incoming bubble detected ─────────────────────────
            incoming = click_and_copy(*self.bubble_pos)
            print("<", incoming)

            choices = await self.session.generate_choice(incoming, self.user_selection)
            if not choices:
                self.prev_hash = curr_hash
                continue

            # 3-A · show choice overlay
            fut = loop.create_future()
            chooser = ChoiceOverlay(fut, choices)
            chooser.show()
            mouse_lock.confine_to_widget(chooser)

            choice_idx = await fut
            chooser.hide()

            # 3-B · send selected reply
            self.user_selection = choices[choice_idx]
            send_message(self.user_selection)
            mouse_lock.release()         # back to control bar

            # 3-C · set flag so next *one* diff is ignored
            self.just_sent = True
            self.prev_hash = curr_hash
                

# ---------------------------------------------------------------------------
# bootstrap
# ---------------------------------------------------------------------------


async def main(DEBUG=0):
    region     = {"top": 67, "left": 382, "width": 55, "height": 754}
    bubble_pos = (448, 796)
    loop = asyncio.get_running_loop()

    mgr    = ConversationManager(region, bubble_pos, debug=(DEBUG))

    async def start_cb():
        ctrl.raise_(); mgr.start(); mouse_lock.confine_to_widget(ctrl)

    async def stop_cb():
        await mgr.stop(); mouse_lock.release()

    async def term_cb():
        await mgr.terminate(loop)

    ctrl = ControlOverlay(loop, on_start=start_cb, on_stop=stop_cb, on_terminate=term_cb)
    ctrl.move(100, 15); ctrl.show()

    global _WINDOW_KEEP
    _WINDOW_KEEP = [ctrl]
    
# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app  = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app); asyncio.set_event_loop(loop)
    signal.signal(signal.SIGINT, lambda *_: loop.stop())
    if (len(sys.argv) == 2 and sys.argv[1] == '--debug'):
        DEBUG = True
    else:
        DEBUG = False
    loop.create_task(main(DEBUG))
    loop.run_forever()
    
