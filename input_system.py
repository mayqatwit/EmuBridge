
"""A small input layer that turns keyboard + joystick state into Actions.
 
The rest of the program never touches raw keys or joystick indices. Each frame:
 
    input.handle_event(event)   # for every pygame event (handles hot-plugging)
    input.update(dt)            # once per frame, after the event loop
    input.pressed(Action.UP)    # True on the frame an action fires
 
Directions auto-repeat while held, so holding the stick/D-pad scrolls the grid.
 
Controllers are matched by name to a *profile* (see JOY_PROFILES in config.py),
so an Xbox pad and a Switch pad can each use their own button numbers while
playing the same way: same physical position -> same Action.
"""
from __future__ import annotations
 
import enum
from typing import Dict, Iterable, List, Optional, Set, Tuple
 
import pygame
 
try:  # profiles live in config.py so everything is edited in one place
    from config import JOY_PROFILES as _CONFIG_PROFILES
except ImportError:  # pragma: no cover
    _CONFIG_PROFILES = []
 
 
class Action(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    CONFIRM = enum.auto()
    BACK = enum.auto()
    SORT = enum.auto()
    TAB_PREV = enum.auto()    # left bumper  (LB)
    TAB_NEXT = enum.auto()    # right bumper (RB)
    TRIGGER_L = enum.auto()   # left trigger  (LT) - registered, free to use
    TRIGGER_R = enum.auto()   # right trigger (RT) - registered, free to use
 
 
DIRECTIONS = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)
 
KEY_BINDINGS: Dict[Action, tuple] = {
    Action.UP: (pygame.K_UP, pygame.K_w),
    Action.DOWN: (pygame.K_DOWN, pygame.K_s),
    Action.LEFT: (pygame.K_LEFT, pygame.K_a),
    Action.RIGHT: (pygame.K_RIGHT, pygame.K_d),
    Action.CONFIRM: (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE),
    Action.BACK: (pygame.K_ESCAPE, pygame.K_BACKSPACE),
    Action.SORT: (pygame.K_TAB, pygame.K_q),
    Action.TAB_PREV: (pygame.K_PAGEUP, pygame.K_LEFTBRACKET),
    Action.TAB_NEXT: (pygame.K_PAGEDOWN, pygame.K_RIGHTBRACKET),
}
 
 
class JoyProfile:
    """Button/axis layout for one family of controllers."""
 
    def __init__(self, spec: dict) -> None:
        self.name: str = spec.get("name", "Controller")
        self.match: Tuple[str, ...] = tuple(m.lower() for m in spec.get("match", ()))
        # {Action: (button indices,)} - includes D-pad buttons if the pad has them
        self.buttons: Dict[Action, Tuple[int, ...]] = {
            Action[k.upper()]: tuple(v) if not isinstance(v, int) else (v,)
            for k, v in spec.get("buttons", {}).items()}
        # {Action: axis index} - triggers that are reported as analog axes
        self.axes: Dict[Action, int] = {
            Action[k.upper()]: v for k, v in spec.get("axes", {}).items()}
        self.exit_combo: Tuple[int, ...] = tuple(spec.get("exit_combo", ()))
 
    def matches(self, device_name: str) -> bool:
        n = device_name.lower()
        return any(m in n for m in self.match)
 
 
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
        profiles: Optional[List[dict]] = None,
    ) -> None:
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        self.deadzone = deadzone
        self.repeat_delay = repeat_delay
        self.repeat_interval = repeat_interval
 
        specs = profiles if profiles is not None else _CONFIG_PROFILES
        self.profiles: List[JoyProfile] = [JoyProfile(s) for s in specs]
        if not self.profiles:
            # Legacy fallback: one generic profile built from the old arguments.
            buttons = {"confirm": tuple(confirm_buttons),
                       "back": tuple(back_buttons),
                       "sort": tuple(sort_buttons)}
            for name, idx in (dpad_buttons or {}).items():
                buttons[name] = (idx,)
            self.profiles = [JoyProfile({"name": "Generic", "buttons": buttons})]
 
        self.joysticks: Dict[int, "pygame.joystick.JoystickType"] = {}
        self._joy_profile: Dict[int, JoyProfile] = {}
        self._held: Set[Action] = set()
        self._pressed: Set[Action] = set()
        self._repeat: Dict[Action, float] = {}
        self.last_source = "keyboard"
        self.last_raw_button: Optional[str] = None
 
        for index in range(pygame.joystick.get_count()):
            self._add_joystick(index)
 
    # ---- devices --------------------------------------------------------
    def profile_for(self, name: str) -> JoyProfile:
        """First profile whose 'match' words appear in the device name;
        otherwise the first profile in the list (the default)."""
        for p in self.profiles:
            if p.matches(name):
                return p
        return self.profiles[0]
 
    def _add_joystick(self, device_index: int) -> None:
        try:
            joy = pygame.joystick.Joystick(device_index)
            joy.init()
        except pygame.error:
            return
        iid = joy.get_instance_id()
        self.joysticks[iid] = joy
        self._joy_profile[iid] = self.profile_for(joy.get_name())
 
    def device_names(self) -> List[str]:
        return [f"{joy.get_name()} ({self._joy_profile[iid].name})"
                for iid, joy in self.joysticks.items()]
 
    def handle_event(self, event: pygame.event.Event) -> None:
        """Feed every pygame event here; handles controller plug/unplug."""
        if event.type == pygame.JOYDEVICEADDED:
            self._add_joystick(event.device_index)
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.joysticks.pop(event.instance_id, None)
            self._joy_profile.pop(event.instance_id, None)
        elif event.type == pygame.JOYBUTTONDOWN:
            self.last_raw_button = f"joy button {event.button}"
        elif event.type == pygame.JOYAXISMOTION and abs(event.value) > 0.9:
            # handy for finding trigger axis numbers: print input.last_raw_button
            self.last_raw_button = f"joy axis {event.axis} ({event.value:+.1f})"
 
    # ---- per-frame ------------------------------------------------------
    def _poll(self) -> Dict[Action, str]:
        """Return every action currently held, with the device holding it."""
        held: Dict[Action, str] = {}
 
        keys = pygame.key.get_pressed()
        for action, bound in KEY_BINDINGS.items():
            if any(keys[k] for k in bound):
                held[action] = "keyboard"
 
        for iid, joy in self.joysticks.items():
            src = joy.get_name()
            profile = self._joy_profile[iid]
            acts: Set[Action] = set()
 
            if joy.get_numhats() > 0:
                hx, hy = joy.get_hat(0)
                if hy > 0: acts.add(Action.UP)
                if hy < 0: acts.add(Action.DOWN)
                if hx < 0: acts.add(Action.LEFT)
                if hx > 0: acts.add(Action.RIGHT)
 
            n_axes = joy.get_numaxes()
            if n_axes >= 2:
                ax, ay = joy.get_axis(0), joy.get_axis(1)
                if ay < -self.deadzone: acts.add(Action.UP)
                if ay > self.deadzone: acts.add(Action.DOWN)
                if ax < -self.deadzone: acts.add(Action.LEFT)
                if ax > self.deadzone: acts.add(Action.RIGHT)
 
            n = joy.get_numbuttons()
            for action, indices in profile.buttons.items():
                if any(0 <= i < n and joy.get_button(i) for i in indices):
                    acts.add(action)
 
            # Analog triggers: rest at -1 (or 0), fully pressed at +1.
            for action, axis in profile.axes.items():
                if 0 <= axis < n_axes and joy.get_axis(axis) > self.deadzone:
                    acts.add(action)
 
            for action in acts:
                held.setdefault(action, src)
        return held
 
    def exit_combo_held(self) -> bool:
        """True while any controller holds its profile's 'close game' combo."""
        for iid, joy in self.joysticks.items():
            combo = self._joy_profile[iid].exit_combo
            n = joy.get_numbuttons()
            if combo and all(b < n and joy.get_button(b) for b in combo):
                return True
        return False
 
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
 
