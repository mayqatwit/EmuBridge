
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
        "name": "PCSX2", "console": "PlayStation 2", "color": (104, 58, 214),
        "exe": r"C:\Program Files\PCSX2\pcsx2-qt.exe" if _WIN else "pcsx2",
        "args": ["-batch", "-fullscreen", "--", "{game}"],
        "extensions": [".iso", ".chd", ".bin", ".cso", ".gz"],
        "rom_dirs": ["~/Documents/Emulators/ps2"],
    },
    "dolphin": {
        "name": "Dolphin", "console": "GameCube / Wii", "color": (176, 66, 200),
        "exe": r"C:\Program Files\Dolphin\Dolphin.exe" if _WIN else "dolphin-emu",
        "args": ["-b", "-e", "{game}"],
        "extensions": [".iso", ".gcm", ".gcz", ".rvz", ".wbfs", ".ciso", ".wad"],
        "rom_dirs": ["~/Documents/Emulators/gamecube", "~/Documents/Emulators/wii"],
    },
    "xemu": {
        "name": "xemu", "console": "Xbox", "color": (66, 74, 196),
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
LIBRARY_STATE_FILE = ".emulator_bridge.json"
 
# ---- Library grid ---------------------------------------------------------
CARD_SIZE = (180, 240)   # width, height of each game tile
CARD_GAP = 22
 
# ---- Input --------------------------------------------------------------
AXIS_DEADZONE = 0.5
REPEAT_DELAY = 0.35
REPEAT_INTERVAL = 0.09
 
# Controller layouts. Each controller is matched by name ("match" words) to a
# profile, so the Xbox and Switch pads can use different button numbers but
# behave the same by physical position:
#   bottom face button = confirm, right = back, top = sort,
#   LB / RB = previous / next tab, Back+Start (Select/Minus+Plus) = close game.
# Unknown controllers fall back to the FIRST profile in the list.
#
# "buttons": Action name -> button index(es).  "axes": triggers that the driver
# reports as analog axes (pressed when the axis passes AXIS_DEADZONE).
# Trigger axis numbers vary by driver - run the app, squeeze a trigger and read
# input.last_raw_button ("joy axis N") to find yours.
JOY_PROFILES = [
    {
        "name": "Xbox",
        "match": ("xbox", "x-box", "xinput", "microsoft"),
        "buttons": {
            "confirm": (0,),        # A  (bottom)
            "back": (1,),           # B  (right)
            "sort": (4,),           # Y  (top)
            "tab_prev": (6,),       # LB
            "tab_next": (7,),       # RB
            "trigger_l": (8,),      # LT as a button (if your driver does that)
            "trigger_r": (9,),      # RT as a button
        },
        "axes": {"trigger_l": 4, "trigger_r": 5},   # LT / RT as analog axes
        "exit_combo": (10, 11),     # Back + Start
    },
    {
        "name": "Switch",
        "match": ("nintendo", "switch", "pro controller", "joy-con"),
        "buttons": {
            "confirm": (1,),        # B  (bottom on a Switch pad)
            "back": (0,),           # A  (right)
            "sort": (2,),           # X  (top)
            "tab_prev": (9,),       # L
            "tab_next": (10,),      # R
            "up": (11,), "down": (12,), "left": (13,), "right": (14,),
        },
        "axes": {"trigger_l": 4, "trigger_r": 5},   # ZL / ZR
        "exit_combo": (4, 6),       # Minus + Plus
    },
]
 
# Legacy single-layout settings - only used if JOY_PROFILES is empty.
JOY_CONFIRM_BUTTONS = (0,)
JOY_BACK_BUTTONS = (1,)
JOY_SORT_BUTTONS = (3,)
JOY_DPAD_BUTTONS = {"up": 11, "down": 12, "left": 13, "right": 14}
EXIT_COMBOS = [(10, 11)]
EXIT_HOLD_SECONDS = 1.0
 
# ---- Colours (RGB) ------------------------------------------------------
THEME = {
    "bg": (9, 7, 14),               # near-black with a violet cast
    "bg_top": (26, 15, 46),         # top of the background gradient
    "panel": (20, 16, 31),
    "border": (52, 40, 82),
    "button": (32, 25, 50),
    "button_hover": (50, 38, 80),
    "button_on": (139, 92, 246),
    "button_disabled": (15, 13, 22),
    "text": (240, 236, 250),
    "text_dim": (136, 126, 164),
    "text_on": (255, 255, 255),
    "accent": (139, 92, 246),       # violet
    "focus": (196, 170, 255),       # light lavender ring
    "card_bottom": (10, 7, 18),     # where card covers fade to
    "missing": (244, 112, 140),
    "overlay": (4, 2, 10, 200),
}
 
