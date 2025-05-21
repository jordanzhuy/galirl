from pynput import mouse

def on_click(x, y, button, pressed):
    if pressed:
        print(f"Clicked at: ({x}, {y})")

# Start the listener and keep it alive until manually interrupted
print("Click anywhere on the screen. Press Ctrl+C to stop.")
with mouse.Listener(on_click=on_click) as listener:
    listener.join()

# new message detect portion
# Clicked at: (382, 67)
# Clicked at: (437, 821)

# copy paste position
# Clicked at: (448, 796)