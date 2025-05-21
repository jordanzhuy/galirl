"""
mouse_lock.py  ▸  Windows cursor-confinement manager  (STACK & auto-warp)

API (unchanged):
    confine_to_widget(widget)
    release()
    free()
    control()

New:  whenever a clip is applied,   SetCursorPos()  moves the pointer to
      the centre of the active rectangle.
"""

import ctypes
from ctypes import wintypes
from typing import List, Optional

# ─── Win32 bindings ───────────────────────────────────────────────────────────
user32 = ctypes.WinDLL("user32", use_last_error=True)

ClipCursor   = user32.ClipCursor
ClipCursor.argtypes = (ctypes.POINTER(wintypes.RECT),)
ClipCursor.restype  = wintypes.BOOL

SetCursorPos = user32.SetCursorPos
SetCursorPos.argtypes = (wintypes.INT, wintypes.INT)
SetCursorPos.restype  = wintypes.BOOL


# ─── internal state ──────────────────────────────────────────────────────────
_STACK: List[wintypes.RECT] = []    # FIFO STACK of active bounding boxes
_FREED: bool = False                # True if free() called and not yet control()


# ─── helpers ─────────────────────────────────────────────────────────────────
def _rect_from_qrect(qrect) -> wintypes.RECT:
    r = wintypes.RECT()
    r.left   = qrect.left()
    r.top    = qrect.top()
    r.right  = qrect.right() + 1     # RECT is right/bottom-exclusive
    r.bottom = qrect.bottom() + 1
    return r


def _apply(rect: Optional[wintypes.RECT]):
    """
    Apply clip (None → release).  If rect is not None also warp cursor to
    its centre for immediate usability.
    """
    ClipCursor(ctypes.byref(rect) if rect is not None else None)
    if rect is not None:
        cx = (rect.left + rect.right) // 2
        cy = (rect.top  + rect.bottom) // 2
        SetCursorPos(cx, cy)


# ─── public API ──────────────────────────────────────────────────────────────
def confine_to_widget(widget):
    """EnSTACK widget and, if it becomes head, apply confinement + warp."""
    global _FREED
    rect = _rect_from_qrect(widget.frameGeometry())
    _STACK.append(rect)
    if not _FREED and len(_STACK) >= 1:      # STACK was empty
        print("applying", rect.top)
        _apply(rect)


def release():
    """Pop one level and re-constrain (with warp) if STACK still non-empty."""
    global _FREED
    if not _STACK:
        return
    _STACK.pop()
    if _FREED:
        return
    _apply(_STACK[-1] if _STACK else None)


def free():
    """Temporarily lift confinement but keep STACK intact."""
    global _FREED
    if _FREED:
        return
    _FREED = True
    _apply(None)


def control():
    """Restore confinement to current STACK head (with warp)."""
    global _FREED
    if not _FREED:
        return
    _FREED = False
    _apply(_STACK[-1] if _STACK else None)