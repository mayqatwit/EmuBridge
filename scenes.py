"""Screens of the app. Each scene reads Actions and can push/pop other scenes."""
from __future__ import annotations

import pygame

import config
from input_system import Action
from ui_grid import ButtonGrid, GridButton


class Scene:
    overlay = False  # True: the scene below stays visible underneath

    def __init__(self, app) -> None:
        self.app = app

    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...


class GridScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        w, h = app.screen.get_size()
        buttons = [GridButton(label, on_press=self._toggle) for label in config.BUTTON_LABELS]
        self.grid = ButtonGrid(pygame.Rect(60, 110, w - 120, h - 230),
                               config.GRID_COLS, buttons, wrap=config.GRID_WRAP)
        self.message = "Move with D-pad / stick / arrows. Select with A / Enter."

    def _toggle(self, btn: GridButton) -> None:
        btn.toggled = not btn.toggled
        if btn.toggled:
            self.selected_game = config.GAMES[btn.label]
            self.message = f"Selected {self.selected_game['emulator']} with game {self.selected_game['game_path']}"
        self.message = f"{btn.label} turned {'ON' if btn.toggled else 'OFF'}"

    def handle_event(self, event) -> None:
        self.grid.handle_mouse(event)

    def update(self, dt: float) -> None:
        inp = self.app.input
        self.grid.handle_input(inp)
        if inp.pressed(Action.BACK):
            self.app.push(ConfirmQuitScene(self.app))
    
    def activate(self) -> Optional[GridButton]:
        btn = self.grid.selected
        print("1")
        if not btn.enabled:
            print("2")
            return None
        if btn.on_press:
            print("3")
            btn.on_press(btn)
        if self.selected_game:
            print("4")
            emulator_path = self.selected_game["emulator"]
            subprocess.Popen([emulator_path, self.selected_game["game_path"]])
            print(self.selected_game)
            self.selected_game = None
        return btn


    def draw(self, surface) -> None:
        th, f = config.THEME, self.app.fonts
        w, h = surface.get_size()
        surface.fill(th["bg"])
        surface.blit(f["title"].render(config.TITLE, True, th["text"]), (60, 40))
        selected = sum(b.toggled for b in self.grid.buttons)
        count = f["small"].render(f"{selected} selected", True, th["text_dim"])
        surface.blit(count, count.get_rect(topright=(w - 60, 52)))

        self.grid.draw(surface, f["button"], th, self.app.time)

        bar = pygame.Rect(0, h - 90, w, 90)
        pygame.draw.rect(surface, th["panel"], bar)
        surface.blit(f["body"].render(self.message, True, th["text"]), (60, h - 78))
        inp = self.app.input
        names = inp.device_names()
        devices = ", ".join(names) if names else "no controller connected (keyboard/mouse active)"
        info = f"Controllers: {devices}   |   last input: {inp.last_source}"
        if inp.last_raw_button:
            info += f" ({inp.last_raw_button})"
        surface.blit(f["small"].render(info, True, th["text_dim"]), (60, h - 46))
        hint = f["small"].render("B / Esc: quit", True, th["text_dim"])
        surface.blit(hint, hint.get_rect(topright=(w - 60, h - 46)))


class ConfirmQuitScene(Scene):
    overlay = True

    def __init__(self, app) -> None:
        super().__init__(app)
        w, h = app.screen.get_size()
        self.panel = pygame.Rect(0, 0, 440, 230)
        self.panel.center = (w // 2, h // 2)
        buttons = [GridButton("Yes", on_press=lambda b: app.quit()),
                   GridButton("No", on_press=lambda b: app.pop())]
        area = pygame.Rect(self.panel.x + 30, self.panel.y + 110, self.panel.w - 60, 80)
        self.grid = ButtonGrid(area, cols=2, buttons=buttons, start_index=1)

    def handle_event(self, event) -> None:
        self.grid.handle_mouse(event)

    def update(self, dt: float) -> None:
        if self.app.input.pressed(Action.BACK):
            self.app.pop()
            return
        self.grid.handle_input(self.app.input)

    def draw(self, surface) -> None:
        th, f = config.THEME, self.app.fonts
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill(th["overlay"])
        surface.blit(shade, (0, 0))
        pygame.draw.rect(surface, th["panel"], self.panel, border_radius=18)
        title = f["body"].render("Quit the application?", True, th["text"])
        surface.blit(title, title.get_rect(midtop=(self.panel.centerx, self.panel.y + 40)))
        self.grid.draw(surface, f["button"], th, self.app.time)
