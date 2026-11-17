"""Central settings: window, grid, input tuning and colours."""

WINDOW_SIZE = (960, 640)
FPS = 60
TITLE = "Grid Selector"

# ---- Grid ---------------------------------------------------------------
GRID_COLS = 4
BUTTON_LABELS = [f"Game {i}" for i in range(1, 13)]  # 12 buttons -> 3 rows x 4 cols
GRID_WRAP = True  # moving past an edge wraps to the other side

# ---- Input --------------------------------------------------------------
AXIS_DEADZONE = 0.5      # how far the analog stick must be pushed to count
REPEAT_DELAY = 0.35      # seconds a direction is held before it auto-repeats
REPEAT_INTERVAL = 0.09   # seconds between repeats while held

# Joystick button indices (Xbox-style layout under SDL: 0 = A, 1 = B).
# Run the app and press buttons; the status bar shows the raw index pressed.
JOY_CONFIRM_BUTTONS = (0,)
JOY_BACK_BUTTONS = (1,)
# Some controllers (e.g. PlayStation pads on some systems) report the D-pad
# as buttons instead of a hat. Map them here; unknown indices are ignored.
JOY_DPAD_BUTTONS = {"up": 11, "down": 12, "left": 13, "right": 14}

# ---- Colours (RGB) ------------------------------------------------------
THEME = {
    "bg": (16, 20, 34),
    "panel": (26, 32, 52),
    "button": (38, 46, 74),
    "button_on": (232, 160, 48),
    "button_disabled": (30, 34, 48),
    "text": (230, 234, 245),
    "text_dim": (130, 140, 170),
    "text_on": (20, 20, 28),
    "focus": (90, 210, 255),
    "overlay": (0, 0, 0, 170),
}

GAMES = {
    "Game 1": {"emulator": "pcsx2", "game_path": "~/Documents/Emulators/ps2/Burnout3.iso"}
}

