"""Game library: collects games from every emulator, sorts them, launches them."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import config


@dataclass
class Game:
    title: str
    emulator: str          # key into config.EMULATORS
    path: str
    last_played: float = 0.0
    play_count: int = 0

    @property
    def console(self) -> str:
        return config.EMULATORS[self.emulator]["console"]

    @property
    def exists(self) -> bool:
        return os.path.exists(self.path)


def _title_from_file(path: str) -> str:
    name = os.path.splitext(os.path.basename(path))[0]
    name = re.sub(r"[\(\[].*?[\)\]]", "", name)  # drop "(USA)", "[SLUS-123]" etc.
    return re.sub(r"[_.]+", " ", name).strip() or os.path.basename(path)


def scan(emulators: Dict[str, dict] = None, manual: List[dict] = None) -> List[Game]:
    emulators = config.EMULATORS if emulators is None else emulators
    manual = config.GAMES if manual is None else manual
    games: Dict[str, Game] = {}
    for g in manual:
        if g["emulator"] not in emulators:
            continue
        path = os.path.expanduser(g["game_path"])
        games[path] = Game(g.get("title") or _title_from_file(path), g["emulator"], path)
    for key, emu in emulators.items():
        exts = tuple(e.lower() for e in emu.get("extensions", []))
        for d in emu.get("rom_dirs", []):
            d = os.path.expanduser(d)
            if not os.path.isdir(d):
                continue
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(exts):
                        p = os.path.join(root, f)
                        games.setdefault(p, Game(_title_from_file(p), key, p))
    return list(games.values())


# ---- sorting ----------------------------------------------------------------
SortKey = Callable[[Game], tuple]
SORT_MODES: List[Tuple[str, SortKey, bool]] = [
    ("A-Z", lambda g: (g.title.lower(),), False),
    ("Z-A", lambda g: (g.title.lower(),), True),
    ("Console", lambda g: (g.console.lower(), g.title.lower()), False),
    ("Recently played", lambda g: (g.last_played, g.title.lower()), True),
    ("Most played", lambda g: (g.play_count, g.title.lower()), True),
]


def sort_games(games: List[Game], mode: int) -> List[Game]:
    _, key, reverse = SORT_MODES[mode % len(SORT_MODES)]
    return sorted(games, key=key, reverse=reverse)


# ---- play history -------------------------------------------------------------
def _state_path() -> str:
    return os.path.expanduser(config.LIBRARY_STATE_FILE)


def load_history(games: List[Game]) -> None:
    try:
        with open(_state_path()) as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return
    for g in games:
        h = data.get(g.path)
        if h:
            g.last_played = h.get("last_played", 0.0)
            g.play_count = h.get("play_count", 0)


def save_history(games: List[Game]) -> None:
    data = {g.path: {"last_played": g.last_played, "play_count": g.play_count}
            for g in games if g.play_count}
    try:
        with open(_state_path(), "w") as fh:
            json.dump(data, fh, indent=2)
    except OSError:
        pass


# ---- launching ----------------------------------------------------------------
def build_command(game: Game) -> List[str]:
    emu = config.EMULATORS[game.emulator]
    exe = os.path.expanduser(emu["exe"])
    return [exe] + [a.replace("{game}", game.path) for a in emu["args"]]


def launch(game: Game) -> Tuple[Optional[subprocess.Popen], str]:
    """Start the game's emulator. Returns (process or None, status message)."""
    emu = config.EMULATORS[game.emulator]
    cmd = build_command(game)
    if not (os.path.exists(cmd[0]) or shutil.which(cmd[0])):
        return None, f"{emu['name']} not found at {cmd[0]} - set its path in config.py"
    if not game.exists:
        return None, f"Game file missing: {game.path}"
    try:
        proc = subprocess.Popen(cmd)
    except OSError as exc:
        return None, f"Could not start {emu['name']}: {exc}"
    game.last_played = time.time()
    game.play_count += 1
    return proc, f"Playing {game.title} on {emu['name']}"


def stop(proc: subprocess.Popen, timeout: float = 3.0) -> None:
    """Close an emulator: ask politely first, force it if it won't go."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout)
    except subprocess.TimeoutExpired:
        proc.kill()