import json
from pathlib import Path

import pygame

from states.exploring import ExploringState

BASE_DIR = Path(__file__).resolve().parent


class Game:
    """Owns the window, shared data and the stack of states."""

    def __init__(self):
        self.base_dir = BASE_DIR
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Python Learning Game")
        self.clock = pygame.time.Clock()
        self.running = True

        # Shared data (every state can read/write it)
        self.tasks = self.load_tasks()
        self.completed = set()  # ids of finished tasks

        # State stack: the last element is the active state
        self.states = []
        self.push_state(ExploringState(self))

    # ---------- data ----------
    def load_tasks(self):
        with open(self.base_dir / "tasks.json", encoding="utf-8") as f:
            data = json.load(f)
        return {task["id"]: task for task in data["tasks"]}

    # ---------- state management ----------
    @property
    def current_state(self):
        return self.states[-1] if self.states else None

    def push_state(self, state):
        """Put a state on top (the previous one is paused, not destroyed)."""
        if self.current_state:
            self.current_state.pause()
        self.states.append(state)
        state.enter()

    def pop_state(self):
        """Remove the top state and resume the one below."""
        if self.states:
            self.states.pop().exit()
        if self.current_state:
            self.current_state.resume()

    def change_state(self, state):
        """Replace the top state (e.g. Dialogue -> Coding)."""
        if self.states:
            self.states.pop().exit()
        self.states.append(state)
        state.enter()

    # ---------- main loop ----------
    def draw(self):
        # Draw from the lowest opaque state up, so transparent
        # states (dialogue box) appear on top of the frozen map.
        start = len(self.states) - 1
        while start > 0 and self.states[start].transparent:
            start -= 1
        for state in self.states[start:]:
            state.draw(self.screen)

    def run(self):
        while self.running and self.states:
            dt = self.clock.tick(60) / 1000  # seconds since last frame

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.current_state:
                    # current_state is re-read each event, because a
                    # state may have changed while handling the last one
                    self.current_state.handle_event(event)

            if self.current_state:
                self.current_state.update(dt)

            self.draw()
            pygame.display.flip()

        pygame.quit()
