"""Central settings: window, emulators, library, input tuning and colours."""
import sys

WINDOW_SIZE = (1280, 760)
FPS = 60
TITLE = "Emulator Bridge"

# ---- Emulators ------------------------------------------------------------
# "exe": path to the emulator program (edit for your machine).
# "args": command-line arguments; {game} is replaced with the game file path.
# "extensions": file types picked up when scanning "rom_dirs".
_WIN = sys.platform.startswith("win")
EMULATORS = {
    "pcsx2": {
        "name": "PCSX2", "console": "PlayStation 2", "color": (40, 70, 160),
        "exe": r"C:\Program Files\PCSX2\pcsx2-qt.exe" if _WIN else "pcsx2",
        "args": ["-batch", "-fullscreen", "--", "{game}"],
        "extensions": [".iso", ".chd", ".bin", ".cso", ".gz"],
        "rom_dirs": ["~/Documents/Emulators/ps2"],
    },
    "dolphin": {
        "name": "Dolphin", "console": "GameCube / Wii", "color": (110, 50, 150),
        "exe": r"C:\Program Files\Dolphin\Dolphin.exe" if _WIN else "dolphin-emu",
        "args": ["-b", "-e", "{game}"],
        "extensions": [".iso", ".gcm", ".gcz", ".rvz", ".wbfs", ".ciso", ".wad"],
        "rom_dirs": ["~/Documents/Emulators/gamecube", "~/Documents/Emulators/wii"],
    },
    "xemu": {
        "name": "xemu", "console": "Xbox", "color": (40, 130, 60),
        "exe": r"C:\Program Files\xemu\xemu.exe" if _WIN else "xemu",
        "args": ["-full-screen", "-dvd_path", "{game}"],
        "extensions": [".iso", ".xiso"],
        "rom_dirs": ["~/Documents/Emulators/xbox"],
    },
}

# Games added by hand (in addition to anything found in rom_dirs).
GAMES = [
    # {"title": "game name", "emulator": "pcsx2",
    #  "game_path": "/path/to/.iso"},
]

# Play history / last-played times are stored here.
LIBRARY_STATE_FILE = "./.emulator_bridge.json"

# ---- Library grid ---------------------------------------------------------
CARD_SIZE = (180, 240)   # width, height of each game tile
CARD_GAP = 22

# ---- Input --------------------------------------------------------------
AXIS_DEADZONE = 0.5
REPEAT_DELAY = 0.35
REPEAT_INTERVAL = 0.09

# Joystick button indices (Xbox-style layout under SDL: 0 = A, 1 = B, 3 = Y).
JOY_CONFIRM_BUTTONS = (0,)
JOY_BACK_BUTTONS = (1,)
JOY_SORT_BUTTONS = (3,)
JOY_DPAD_BUTTONS = {"up": 11, "down": 12, "left": 13, "right": 14}

# Hold these buttons together while a game is running to close the emulator
# and return to the library. Default: Back/Select + Start (Xbox layout under
# SDL2 = 4 + 6). Some older drivers report them as 6 + 7 - both are checked.
EXIT_COMBOS = [(10, 11)]
EXIT_HOLD_SECONDS = 1.0

# ---- Colours (RGB) ------------------------------------------------------
THEME = {
    "bg": (23, 26, 33),
    "panel": (32, 38, 50),
    "button": (42, 71, 94),
    "button_on": (102, 192, 244),
    "button_disabled": (30, 34, 48),
    "text": (235, 238, 245),
    "text_dim": (140, 150, 170),
    "text_on": (20, 20, 28),
    "focus": (102, 192, 244),
    "missing": (200, 90, 80),
    "overlay": (0, 0, 0, 170),
}