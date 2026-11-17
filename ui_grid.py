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
