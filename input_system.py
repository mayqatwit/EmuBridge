"""A small input layer that turns keyboard + joystick state into Actions.

The rest of the program never touches raw keys or joystick indices. Each frame:

    input.handle_event(event)   # for every pygame event (handles hot-plugging)
    input.update(dt)            # once per frame, after the event loop
    input.pressed(Action.UP)    # True on the frame an action fires

Directions auto-repeat while held, so holding the stick/D-pad scrolls the grid.
"""
from __future__ import annotations

import enum
from typing import Dict, Iterable, List, Optional, Set

import pygame


class Action(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    CONFIRM = enum.auto()
    BACK = enum.auto()
    SORT = enum.auto()


DIRECTIONS = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)

KEY_BINDINGS: Dict[Action, tuple] = {
    Action.UP: (pygame.K_UP, pygame.K_w),
    Action.DOWN: (pygame.K_DOWN, pygame.K_s),
    Action.LEFT: (pygame.K_LEFT, pygame.K_a),
    Action.RIGHT: (pygame.K_RIGHT, pygame.K_d),
    Action.CONFIRM: (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE),
    Action.BACK: (pygame.K_ESCAPE, pygame.K_BACKSPACE),
    Action.SORT: (pygame.K_TAB, pygame.K_q),
}


class InputManager:
    def __init__(
        self,
        deadzone: float = 0.5,
        repeat_delay: float = 0.35,
        repeat_interval: float = 0.09,
        confirm_buttons: Iterable[int] = (0,),
        back_buttons: Iterable[int] = (1,),
        sort_buttons: Iterable[int] = (3,),
        dpad_buttons: Optional[Dict[str, int]] = None,
    ) -> None:
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        self.deadzone = deadzone
        self.repeat_delay = repeat_delay
        self.repeat_interval = repeat_interval
        self.confirm_buttons = tuple(confirm_buttons)
        self.back_buttons = tuple(back_buttons)
        self.sort_buttons = tuple(sort_buttons)
        dpad = dpad_buttons or {}
        self.dpad_buttons = {
            Action.UP: dpad.get("up"),
            Action.DOWN: dpad.get("down"),
            Action.LEFT: dpad.get("left"),
            Action.RIGHT: dpad.get("right"),
        }

        self.joysticks: Dict[int, "pygame.joystick.JoystickType"] = {}
        self._held: Set[Action] = set()
        self._pressed: Set[Action] = set()
        self._repeat: Dict[Action, float] = {}
        self.last_source = "keyboard"
        self.last_raw_button: Optional[str] = None

        for index in range(pygame.joystick.get_count()):
            self._add_joystick(index)

    # ---- devices --------------------------------------------------------
    def _add_joystick(self, device_index: int) -> None:
        try:
            joy = pygame.joystick.Joystick(device_index)
            joy.init()
        except pygame.error:
            return
        self.joysticks[joy.get_instance_id()] = joy

    def device_names(self) -> List[str]:
        return [joy.get_name() for joy in self.joysticks.values()]

    def handle_event(self, event: pygame.event.Event) -> None:
        """Feed every pygame event here; handles controller plug/unplug."""
        if event.type == pygame.JOYDEVICEADDED:
            self._add_joystick(event.device_index)
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.joysticks.pop(event.instance_id, None)
        elif event.type == pygame.JOYBUTTONDOWN:
            self.last_raw_button = f"joy button {event.button}"

    # ---- per-frame ------------------------------------------------------
    def _poll(self) -> Dict[Action, str]:
        """Return every action currently held, with the device holding it."""
        held: Dict[Action, str] = {}

        keys = pygame.key.get_pressed()
        for action, bound in KEY_BINDINGS.items():
            if any(keys[k] for k in bound):
                held[action] = "keyboard"

        for joy in self.joysticks.values():
            src = joy.get_name()
            dirs: Set[Action] = set()

            if joy.get_numhats() > 0:
                hx, hy = joy.get_hat(0)
                if hy > 0: dirs.add(Action.UP)
                if hy < 0: dirs.add(Action.DOWN)
                if hx < 0: dirs.add(Action.LEFT)
                if hx > 0: dirs.add(Action.RIGHT)

            if joy.get_numaxes() >= 2:
                ax, ay = joy.get_axis(0), joy.get_axis(1)
                if ay < -self.deadzone: dirs.add(Action.UP)
                if ay > self.deadzone: dirs.add(Action.DOWN)
                if ax < -self.deadzone: dirs.add(Action.LEFT)
                if ax > self.deadzone: dirs.add(Action.RIGHT)

            n = joy.get_numbuttons()
            def down(i: Optional[int]) -> bool:
                return i is not None and 0 <= i < n and joy.get_button(i)

            for action, idx in self.dpad_buttons.items():
                if down(idx):
                    dirs.add(action)
            if any(down(i) for i in self.confirm_buttons):
                dirs.add(Action.CONFIRM)
            if any(down(i) for i in self.back_buttons):
                dirs.add(Action.BACK)
            if any(down(i) for i in self.sort_buttons):
                dirs.add(Action.SORT)

            for action in dirs:
                held.setdefault(action, src)
        return held

    def update(self, dt: float, held: Optional[Dict[Action, str]] = None) -> None:
        """Call once per frame after the event loop. `held` is for testing."""
        held = self._poll() if held is None else held
        now = set(held)
        pressed = now - self._held

        for action in DIRECTIONS:
            if action in pressed:
                self._repeat[action] = self.repeat_delay
            elif action in now:
                self._repeat[action] -= dt
                if self._repeat[action] <= 0:
                    pressed.add(action)
                    self._repeat[action] += self.repeat_interval

        if pressed:
            self.last_source = held[next(iter(pressed))]
        self._pressed = pressed
        self._held = now

    # ---- queries --------------------------------------------------------
    def pressed(self, action: Action) -> bool:
        """True on the frame the action fires (including auto-repeats)."""
        return action in self._pressed

    def held(self, action: Action) -> bool:
        return action in self._held

    def actions(self) -> List[Action]:
        return [a for a in Action if a in self._pressed]