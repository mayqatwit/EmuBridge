"""A grid of buttons with a single focused cell, driven by Actions or the mouse."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

import pygame

from input_system import Action, InputManager


@dataclass
class GridButton:
    label: str
    on_press: Optional[Callable[["GridButton"], None]] = None
    toggled: bool = False
    enabled: bool = True


class ButtonGrid:
    def __init__(self, rect, cols: int, buttons: Sequence[GridButton],
                 gap: int = 16, wrap: bool = True, start_index: int = 0) -> None:
        if not buttons:
            raise ValueError("ButtonGrid needs at least one button")
        self.rect = pygame.Rect(rect)
        self.cols = max(1, cols)
        self.buttons: List[GridButton] = list(buttons)
        self.rows = math.ceil(len(self.buttons) / self.cols)
        self.gap = gap
        self.wrap = wrap
        self.index = start_index
        self.rects = self._layout()

    def _layout(self) -> List[pygame.Rect]:
        cw = (self.rect.w - self.gap * (self.cols - 1)) / self.cols
        ch = (self.rect.h - self.gap * (self.rows - 1)) / self.rows
        out = []
        for i in range(len(self.buttons)):
            r, c = divmod(i, self.cols)
            out.append(pygame.Rect(round(self.rect.x + c * (cw + self.gap)),
                                   round(self.rect.y + r * (ch + self.gap)),
                                   round(cw), round(ch)))
        return out

    @property
    def selected(self) -> GridButton:
        return self.buttons[self.index]

    def move(self, dcol: int, drow: int) -> bool:
        """Step focus, skipping empty or disabled cells. Returns True if it moved."""
        row, col = divmod(self.index, self.cols)
        for _ in range(max(self.rows, self.cols)):
            prev = (row, col)
            col += dcol
            row += drow
            if self.wrap:
                col %= self.cols
                row %= self.rows
            else:
                col = min(max(col, 0), self.cols - 1)
                row = min(max(row, 0), self.rows - 1)
                if (row, col) == prev:
                    return False
            i = row * self.cols + col
            if i < len(self.buttons) and self.buttons[i].enabled:
                if i == self.index:
                    return False
                self.index = i
                return True
        return False

    def activate(self) -> Optional[GridButton]:
        btn = self.selected
        if not btn.enabled:
            return None
        if btn.on_press:
            btn.on_press(btn)
        return btn

    def handle_input(self, inp: InputManager) -> Optional[GridButton]:
        if inp.pressed(Action.UP): self.move(0, -1)
        if inp.pressed(Action.DOWN): self.move(0, 1)
        if inp.pressed(Action.LEFT): self.move(-1, 0)
        if inp.pressed(Action.RIGHT): self.move(1, 0)
        if inp.pressed(Action.CONFIRM):
            return self.activate()
        return None

    def index_at(self, pos) -> Optional[int]:
        for i, r in enumerate(self.rects):
            if r.collidepoint(pos) and self.buttons[i].enabled:
                return i
        return None

    def handle_mouse(self, event: pygame.event.Event) -> Optional[GridButton]:
        if event.type == pygame.MOUSEMOTION:
            i = self.index_at(event.pos)
            if i is not None:
                self.index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            i = self.index_at(event.pos)
            if i is not None:
                self.index = i
                return self.activate()
        return None

    def draw(self, surface: pygame.Surface, font: pygame.font.Font,
             theme: dict, t: float) -> None:
        pulse = (math.sin(t * 6) + 1) / 2
        for i, (btn, r) in enumerate(zip(self.buttons, self.rects)):
            if not btn.enabled:
                fill, fg = theme["button_disabled"], theme["text_dim"]
            elif btn.toggled:
                fill, fg = theme["button_on"], theme["text_on"]
            else:
                fill, fg = theme["button"], theme["text"]
            pygame.draw.rect(surface, fill, r, border_radius=14)
            if i == self.index:
                grow = 3 + round(pulse * 3)
                pygame.draw.rect(surface, theme["focus"], r.inflate(grow * 2, grow * 2),
                                 width=3, border_radius=16 + grow)
            label = font.render(btn.label, True, fg)
            surface.blit(label, label.get_rect(center=r.center))


class LibraryGrid:
    """Scrolling grid of game cards (cover-style tiles), Steam library style."""

    def __init__(self, rect, card_size, gap: int = 20) -> None:
        self.rect = pygame.Rect(rect)
        self.cw, self.ch = card_size
        self.gap = gap
        self.cols = max(1, (self.rect.w + gap) // (self.cw + gap))
        self.games: list = []
        self.index = 0
        self.scroll = 0.0       # current pixel offset (animated)
        self.target = 0         # wanted pixel offset

    def set_games(self, games, keep=None) -> None:
        self.games = list(games)
        self.index = self.games.index(keep) if keep in self.games else 0
        self._follow()

    @property
    def selected(self):
        return self.games[self.index] if self.games else None

    def _card_rect(self, i: int) -> pygame.Rect:
        r, c = divmod(i, self.cols)
        x0 = self.rect.x + (self.rect.w - (self.cols * (self.cw + self.gap) - self.gap)) // 2
        return pygame.Rect(x0 + c * (self.cw + self.gap),
                           self.rect.y + 12 + r * (self.ch + self.gap) - round(self.scroll),
                           self.cw, self.ch)

    def _follow(self) -> None:
        row = self.index // self.cols
        top = row * (self.ch + self.gap)
        if top < self.target:
            self.target = top
        elif top + self.ch + 24 > self.target + self.rect.h:
            self.target = top + self.ch + 24 - self.rect.h

    def move(self, dcol: int, drow: int) -> None:
        if not self.games:
            return
        n = len(self.games)
        i = self.index + dcol + drow * self.cols
        if dcol and i // self.cols != self.index // self.cols and 0 <= i < n:
            pass  # allow wrapping across row ends for left/right
        self.index = min(max(i, 0), n - 1)
        self._follow()

    def handle_input(self, inp: InputManager):
        if inp.pressed(Action.UP): self.move(0, -1)
        if inp.pressed(Action.DOWN): self.move(0, 1)
        if inp.pressed(Action.LEFT): self.move(-1, 0)
        if inp.pressed(Action.RIGHT): self.move(1, 0)
        if inp.pressed(Action.CONFIRM):
            return self.selected
        return None

    def handle_mouse(self, event):
        if event.type == pygame.MOUSEWHEEL:
            rows = math.ceil(len(self.games) / self.cols)
            max_scroll = max(0, rows * (self.ch + self.gap) + 24 - self.rect.h)
            self.target = min(max(self.target - event.y * 60, 0), max_scroll)
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            if not self.rect.collidepoint(event.pos):
                return None
            for i in range(len(self.games)):
                if self._card_rect(i).collidepoint(event.pos):
                    self.index = i
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        return self.games[i]
        return None

    @staticmethod
    def _wrap(text: str, font, width: int):
        lines, cur = [], ""
        for word in text.split():
            test = f"{cur} {word}".strip()
            if font.size(test)[0] <= width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines[:4]

    def draw(self, surface, font, small, theme, t: float) -> None:
        import config  # local import keeps ui_grid free of app config at import time
        self.scroll += (self.target - self.scroll) * 0.25
        prev_clip = surface.get_clip()
        surface.set_clip(self.rect)
        pulse = (math.sin(t * 6) + 1) / 2
        for i, game in enumerate(self.games):
            r = self._card_rect(i)
            if r.bottom < self.rect.top or r.top > self.rect.bottom:
                continue
            focused = i == self.index
            if focused:
                r = r.inflate(10, 10)
            color = config.EMULATORS[game.emulator]["color"]
            # vertical gradient "cover"
            for y in range(r.h):
                k = y / r.h
                c = tuple(int(color[j] * (1 - k) + theme["bg"][j] * k * 0.6) for j in range(3))
                pygame.draw.line(surface, c, (r.x, r.y + y), (r.right - 1, r.y + y))
            # console badge
            badge = small.render(game.console, True, theme["text"])
            pygame.draw.rect(surface, (0, 0, 0), badge.get_rect(topleft=(r.x + 8, r.y + 8)).inflate(10, 6), border_radius=4)
            surface.blit(badge, (r.x + 8, r.y + 8))
            # title
            lines = self._wrap(game.title, font, r.w - 20)
            y = r.bottom - 14 - len(lines) * font.get_linesize()
            for line in lines:
                surface.blit(font.render(line, True, theme["text"]), (r.x + 10, y))
                y += font.get_linesize()
            if not game.exists:
                m = small.render("file missing", True, theme["missing"])
                surface.blit(m, (r.x + 10, r.y + 36))
            if focused:
                grow = 2 + round(pulse * 3)
                pygame.draw.rect(surface, theme["focus"], r.inflate(grow * 2, grow * 2),
                                 width=3, border_radius=8)
        if not self.games:
            msg = font.render("No games for this console", True, theme["text_dim"])
            surface.blit(msg, msg.get_rect(center=self.rect.center))
        surface.set_clip(prev_clip)