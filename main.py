"""Entry point: python main.py"""
from __future__ import annotations

from typing import List, Optional

import os

# Let the library hear the controller even while an emulator window has focus.
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame

import config
from input_system import InputManager
from scenes import LibraryScene, Scene


class App:
    def __init__(self) -> None:
        pygame.init()
        # self.screen = pygame.display.set_mode(config.WINDOW_SIZE)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.time = 0.0
        self.running = True
        self.input = InputManager(
            deadzone=config.AXIS_DEADZONE,
            repeat_delay=config.REPEAT_DELAY,
            repeat_interval=config.REPEAT_INTERVAL,
            confirm_buttons=config.JOY_CONFIRM_BUTTONS,
            back_buttons=config.JOY_BACK_BUTTONS,
            sort_buttons=config.JOY_SORT_BUTTONS,
            dpad_buttons=config.JOY_DPAD_BUTTONS,
        )
        self.fonts = {
            "title": pygame.font.Font(None, 54),
            "button": pygame.font.Font(None, 34),
            "body": pygame.font.Font(None, 30),
            "small": pygame.font.Font(None, 24),
            "card": pygame.font.Font(None, 26),
        }
        self.scenes: List[Scene] = []

    # ---- scene stack ------------------------------------------------------
    def push(self, scene: Scene) -> None:
        self.scenes.append(scene)

    def pop(self) -> None:
        if self.scenes:
            self.scenes.pop()
        if not self.scenes:
            self.running = False

    def quit(self) -> None:
        self.running = False

    # ---- main loop --------------------------------------------------------
    def run(self, max_frames: Optional[int] = None) -> None:
        self.push(LibraryScene(self))
        frames = 0
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self.time += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.input.handle_event(event)
                if self.scenes:
                    self.scenes[-1].handle_event(event)

            self.input.update(dt)
            if self.scenes:
                self.scenes[-1].update(dt)
            self.draw()

            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
        pygame.quit()

    def draw(self) -> None:
        # Draw from the topmost non-overlay scene upward.
        start = len(self.scenes) - 1
        while start > 0 and self.scenes[start].overlay:
            start -= 1
        for scene in self.scenes[max(start, 0):]:
            scene.draw(self.screen)
        pygame.display.flip()


if __name__ == "__main__":
    App().run()