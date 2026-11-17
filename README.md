# Grid Selector (pygame + joystick)

A window with a grid of buttons you can move around and select with a game
controller, keyboard or mouse.

## Run
    pip install -r requirements.txt
    python main.py

Tests: `python -m unittest discover tests`

## Controls
| Action  | Controller            | Keyboard            |
|---------|-----------------------|---------------------|
| Move    | D-pad / left stick    | Arrows / WASD       |
| Select  | A (button 0)          | Enter / Space       |
| Back    | B (button 1)          | Esc / Backspace     |

Holding a direction auto-repeats. Controllers can be plugged in or out while
running. The status bar shows the raw index of any controller button you press,
so you can remap buttons in `config.py`.

## How it fits together
- `input_system.py` - `InputManager` turns keys, hats, sticks and buttons into
  `Action`s. Scenes only ask `input.pressed(Action.CONFIRM)` etc.
- `ui_grid.py` - `ButtonGrid` keeps the focused cell, moves it, and calls each
  `GridButton.on_press`.
- `scenes.py` - screens on a stack: `GridScene` (main grid) and
  `ConfirmQuitScene` (Yes/No overlay). Use `app.push(...)` / `app.pop()`.
- `main.py` - window, loop: events -> `input.update()` -> top scene update -> draw.

To add a new action: add it to `Action`, bind keys in `KEY_BINDINGS`, and map
joystick input in `InputManager._poll`.
