"""Screens of the app. Each scene reads Actions and can push/pop other scenes."""
from __future__ import annotations
 
import pygame
 
import config
import library
from input_system import Action
from ui_grid import ButtonGrid, GridButton, LibraryGrid, draw_glow, vgradient
 
 
class Scene:
    overlay = False  # True: the scene below stays visible underneath
 
    def __init__(self, app) -> None:
        self.app = app
 
    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
 
 
class LibraryScene(Scene):
    """Steam-style grid of every game across all emulators."""
 
    HEADER = 110
    FOOTER = 90
 
    def __init__(self, app) -> None:
        super().__init__(app)
        self.games = library.scan()
        library.load_history(self.games)
        self.sort_mode = 0
        self.filters = [None] + list(config.EMULATORS)  # None = all consoles
        self.filter_index = 0
        self.process = None
        self.running_game = None
        self.bg = None
        w, h = app.screen.get_size()
        self.grid = LibraryGrid(pygame.Rect(40, self.HEADER, w - 80, h - self.HEADER - self.FOOTER),
                                config.CARD_SIZE, config.CARD_GAP)
        self.message = (f"{len(self.games)} games found. A/Enter: play   Y/Tab: sort"
                        if self.games else "No games found - add rom_dirs or GAMES in config.py")
        self._refresh()
 
    # ---- library state -------------------------------------------------------
    def _refresh(self, keep: library.Game = None) -> None:
        f = self.filters[self.filter_index]
        visible = [g for g in self.games if f is None or g.emulator == f]
        self.grid.set_games(library.sort_games(visible, self.sort_mode), keep)
 
    def cycle_sort(self) -> None:
        self.sort_mode = (self.sort_mode + 1) % len(library.SORT_MODES)
        self._refresh(self.grid.selected)
        self.message = f"Sorted by {library.SORT_MODES[self.sort_mode][0]}"
 
    def cycle_filter(self, step: int = 1) -> None:
        self.filter_index = (self.filter_index + step) % len(self.filters)
        self._refresh()
 
    def play(self, game: library.Game) -> None:
        if self.process and self.process.poll() is None:
            self.message = f"{self.running_game.title} is still running"
            return
        self.process, self.message = library.launch(game)
        if self.process:
            self.running_game = game
            library.save_history(self.games)
 
    # ---- scene hooks -----------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._tab_rects()):
                if r.collidepoint(event.pos):
                    self.filter_index = i
                    self._refresh()
                    return
            if self._sort_rect().collidepoint(event.pos):
                self.cycle_sort()
                return
        picked = self.grid.handle_mouse(event)
        if picked:
            self.play(picked)
 
    def _exit_combo_held(self) -> bool:
        return self.app.input.exit_combo_held()
 
    def update(self, dt: float) -> None:
        if self.process and self.process.poll() is None:
            # Game running: only watch for the "close game" button combo.
            if self._exit_combo_held():
                self.exit_hold = getattr(self, "exit_hold", 0.0) + dt
                if self.exit_hold >= config.EXIT_HOLD_SECONDS:
                    library.stop(self.process)
                    self.exit_hold = 0.0
            else:
                self.exit_hold = 0.0
            return
        if self.process and self.process.poll() is not None:
            self.message = f"Finished {self.running_game.title}"
            self.process = self.running_game = None
        inp = self.app.input
        picked = self.grid.handle_input(inp)
        if picked:
            self.play(picked)
        if inp.pressed(Action.SORT):
            self.cycle_sort()
        if inp.pressed(Action.TAB_PREV):
            self.cycle_filter(-1)
        if inp.pressed(Action.TAB_NEXT):
            self.cycle_filter(1)
        if inp.pressed(Action.BACK):
            self.app.push(ConfirmQuitScene(self.app))
 
    # ---- drawing ---------------------------------------------------------------
    def _tab_labels(self):
        return ["All"] + [config.EMULATORS[k]["console"] for k in self.filters[1:]]
 
    def _tab_rects(self):
        f, x, out = self.app.fonts["small"], 40, []
        for label in self._tab_labels():
            w = f.size(label)[0] + 28
            out.append(pygame.Rect(x, 66, w, 30))
            x += w + 8
        return out
 
    def _sort_rect(self):
        w = self.app.screen.get_width()
        return pygame.Rect(w - 280, 66, 260, 30)
 
    def draw(self, surface) -> None:
        th, f = config.THEME, self.app.fonts
        w, h = surface.get_size()
        if self.bg is None or self.bg.get_size() != (w, h):
            self.bg = vgradient((w, h), th["bg_top"], th["bg"])
        surface.blit(self.bg, (0, 0))
 
        # header
        surface.blit(f["title"].render("Library", True, th["text"]), (40, 18))
        brand = f["small"].render(config.TITLE, True, th["accent"])
        surface.blit(brand, brand.get_rect(topright=(w - 40, 30)))
 
        for i, (label, r) in enumerate(zip(self._tab_labels(), self._tab_rects())):
            on = i == self.filter_index
            if on:
                draw_glow(surface, r, th["accent"], 15, 0.8, 8)
                pygame.draw.rect(surface, th["accent"], r, border_radius=15)
            else:
                pygame.draw.rect(surface, th["panel"], r, border_radius=15)
                pygame.draw.rect(surface, th["border"], r, width=1, border_radius=15)
            t = f["small"].render(label, True, th["text_on"] if on else th["text_dim"])
            surface.blit(t, t.get_rect(center=r.center))
 
        sr = self._sort_rect()
        pygame.draw.rect(surface, th["panel"], sr, border_radius=15)
        pygame.draw.rect(surface, th["border"], sr, width=1, border_radius=15)
        t = f["small"].render(f"Sort: {library.SORT_MODES[self.sort_mode][0]}  (Y/Tab)", True, th["text"])
        surface.blit(t, t.get_rect(center=sr.center))
 
        pygame.draw.line(surface, th["border"], (40, self.HEADER - 4), (w - 40, self.HEADER - 4))
 
        self.grid.draw(surface, f["card"], f["small"], th, self.app.time)
 
        # footer
        bar = pygame.Rect(0, h - self.FOOTER, w, self.FOOTER)
        pygame.draw.rect(surface, th["panel"], bar)
        pygame.draw.line(surface, th["border"], bar.topleft, bar.topright)
        pygame.draw.line(surface, th["accent"], (40, bar.y), (120, bar.y), 2)
        surface.blit(f["body"].render(self.message, True, th["text"]), (40, h - 78))
        g = self.grid.selected
        if g:
            emu = config.EMULATORS[g.emulator]["name"]
            info = f"{g.title}  -  {g.console} via {emu}  -  played {g.play_count}x"
            surface.blit(f["small"].render(info, True, th["text_dim"]), (40, h - 46))
        hint = f["small"].render("LB / RB: switch tabs  |  B / Esc: quit", True, th["text_dim"])
        surface.blit(hint, hint.get_rect(topright=(w - 40, h - 46)))
        held = [b for joy in self.app.input.joysticks.values()
                for b in range(joy.get_numbuttons()) if joy.get_button(b)]
        dbg = f["small"].render(f"held buttons: {held}", True, th["text_dim"])
        surface.blit(dbg, (40, h - 22))
 
 
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
        draw_glow(surface, self.panel, th["accent"], 18, 0.5, 18)
        pygame.draw.rect(surface, th["panel"], self.panel, border_radius=18)
        pygame.draw.rect(surface, th["border"], self.panel, width=2, border_radius=18)
        title = f["body"].render("Quit the application?", True, th["text"])
        surface.blit(title, title.get_rect(midtop=(self.panel.centerx, self.panel.y + 40)))
        self.grid.draw(surface, f["button"], th, self.app.time)