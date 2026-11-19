"""A grid of buttons with a single focused cell, driven by Actions or the mouse."""
from __future__ import annotations
 
import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence
 
import pygame
 
from input_system import Action, InputManager
 
 
# ---- drawing helpers ---------------------------------------------------------
_GRADIENTS: dict = {}
 
 
def vgradient(size, top, bottom, radius: int = 0) -> pygame.Surface:
    """Cached vertical gradient surface, optionally with rounded corners."""
    key = (tuple(size), tuple(top[:3]), tuple(bottom[:3]), radius)
    surf = _GRADIENTS.get(key)
    if surf is None:
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            k = y / max(1, h - 1)
            c = tuple(int(top[j] * (1 - k) + bottom[j] * k) for j in range(3))
            pygame.draw.line(surf, c, (0, y), (w - 1, y))
        if radius:
            mask = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
            surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        _GRADIENTS[key] = surf
    return surf
 
 
def draw_glow(surface: pygame.Surface, rect: pygame.Rect, color, radius: int,
              intensity: float = 1.0, spread: int = 10) -> None:
    """Soft coloured halo around a rounded rect."""
    glow = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
    for i in range(spread, 0, -1):
        alpha = int(70 * intensity * (1 - i / (spread + 1)) ** 2)
        if alpha <= 0:
            continue
        r = pygame.Rect(spread - i, spread - i, rect.w + i * 2, rect.h + i * 2)
        pygame.draw.rect(glow, (*color[:3], alpha), r, width=2, border_radius=radius + i)
    surface.blit(glow, (rect.x - spread, rect.y - spread))
 
 
def draw_shadow(surface: pygame.Surface, rect: pygame.Rect, radius: int,
                strength: int = 80) -> None:
    pad = 14
    sh = pygame.Surface((rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA)
    for k, grow in enumerate((6, 3, 0)):
        r = pygame.Rect(pad - grow, pad - grow + 6, rect.w + grow * 2, rect.h + grow * 2)
        pygame.draw.rect(sh, (0, 0, 0, strength // 2 + k * 10), r, border_radius=radius + grow)
    surface.blit(sh, (rect.x - pad, rect.y - pad))
 
 
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
        pulse = (math.sin(t * 5) + 1) / 2
        for i, (btn, r) in enumerate(zip(self.buttons, self.rects)):
            focused = i == self.index and btn.enabled
            if not btn.enabled:
                fill, fg = theme["button_disabled"], theme["text_dim"]
            elif btn.toggled:
                fill, fg = theme["button_on"], theme["text_on"]
            elif focused:
                fill, fg = theme["button_hover"], theme["text"]
            else:
                fill, fg = theme["button"], theme["text"]
            if focused:
                draw_glow(surface, r, theme["accent"], 14, 0.6 + 0.4 * pulse, 14)
            pygame.draw.rect(surface, fill, r, border_radius=14)
            pygame.draw.rect(surface, theme["focus"] if focused else theme["border"], r,
                             width=2 if focused else 1, border_radius=14)
            label = font.render(btn.label, True, fg)
            surface.blit(label, label.get_rect(center=r.center))
 
 
class LibraryGrid:
    """Scrolling grid of game cards (cover-style tiles), Steam library style."""
 
    PAD_TOP = 22
    RADIUS = 14
 
    def __init__(self, rect, card_size, gap: int = 20) -> None:
        self.rect = pygame.Rect(rect)
        self.cw, self.ch = card_size
        self.gap = gap
        self.cols = max(1, (self.rect.w + gap) // (self.cw + gap))
        self.games: list = []
        self.index = 0
        self.scroll = 0.0       # current pixel offset (animated)
        self.target = 0         # wanted pixel offset
        self._big_font = None   # lazily created, for the cover initial
 
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
                           self.rect.y + self.PAD_TOP + r * (self.ch + self.gap) - round(self.scroll),
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
 
    def _max_scroll(self) -> int:
        rows = math.ceil(len(self.games) / self.cols)
        return max(0, rows * (self.ch + self.gap) + 24 - self.rect.h)
 
    def handle_mouse(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.target = min(max(self.target - event.y * 60, 0), self._max_scroll())
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
        if self._big_font is None:
            self._big_font = pygame.font.Font(None, 130)
        prev_clip = surface.get_clip()
        surface.set_clip(self.rect)
        pulse = (math.sin(t * 5) + 1) / 2
        rad = self.RADIUS
        focused_card = None
 
        def draw_card(i: int, game, r: pygame.Rect, focused: bool) -> None:
            color = config.EMULATORS[game.emulator]["color"]
            draw_shadow(surface, r, rad, 120 if focused else 80)
            if focused:
                draw_glow(surface, r, theme["accent"], rad, 0.7 + 0.3 * pulse, 14)
            # gradient cover: console colour fading into near-black
            surface.blit(vgradient(r.size, color, theme["card_bottom"], rad), r.topleft)
            # big faint initial as stand-in cover art
            initial = self._big_font.render(game.title[:1].upper() or "?", True, (255, 255, 255))
            initial.set_alpha(34)
            surface.blit(initial, initial.get_rect(center=(r.centerx, r.y + int(r.h * 0.42))))
            # console badge (pill)
            badge = small.render(game.console, True, theme["text"])
            pill = badge.get_rect(topleft=(r.x + 12, r.y + 12)).inflate(16, 8)
            pill_bg = pygame.Surface(pill.size, pygame.SRCALPHA)
            pygame.draw.rect(pill_bg, (8, 5, 16, 170), pill_bg.get_rect(), border_radius=pill.h // 2)
            surface.blit(pill_bg, pill.topleft)
            surface.blit(badge, badge.get_rect(center=pill.center))
            # title
            lines = self._wrap(game.title, font, r.w - 24)
            y = r.bottom - 16 - len(lines) * font.get_linesize()
            for line in lines:
                surface.blit(font.render(line, True, theme["text"]), (r.x + 12, y))
                y += font.get_linesize()
            if not game.exists:
                m = small.render("File missing", True, theme["missing"])
                mp = m.get_rect(topleft=(r.x + 12, pill.bottom + 8)).inflate(14, 6)
                pygame.draw.rect(surface, (30, 8, 16), mp, border_radius=mp.h // 2)
                pygame.draw.rect(surface, theme["missing"], mp, width=1, border_radius=mp.h // 2)
                surface.blit(m, m.get_rect(center=mp.center))
            # outline
            if focused:
                pygame.draw.rect(surface, theme["focus"], r, width=3, border_radius=rad)
            else:
                pygame.draw.rect(surface, theme["border"], r, width=1, border_radius=rad)
 
        for i, game in enumerate(self.games):
            r = self._card_rect(i)
            if r.bottom < self.rect.top or r.top > self.rect.bottom:
                continue
            if i == self.index:
                focused_card = (i, game, r.inflate(14, 14))  # drawn last so it sits on top
                continue
            draw_card(i, game, r, False)
        if focused_card:
            draw_card(*focused_card, True)
 
        if not self.games:
            msg = font.render("No games for this console", True, theme["text_dim"])
            surface.blit(msg, msg.get_rect(center=self.rect.center))
 
        # slim scrollbar
        max_scroll = self._max_scroll()
        if max_scroll > 0:
            track = pygame.Rect(self.rect.right - 6, self.rect.y + 6, 4, self.rect.h - 12)
            pygame.draw.rect(surface, theme["panel"], track, border_radius=2)
            th_h = max(36, round(track.h * self.rect.h / (self.rect.h + max_scroll)))
            th_y = track.y + round((track.h - th_h) * min(1.0, self.scroll / max_scroll))
            pygame.draw.rect(surface, theme["accent"], (track.x, th_y, track.w, th_h), border_radius=2)
        surface.set_clip(prev_clip)
 