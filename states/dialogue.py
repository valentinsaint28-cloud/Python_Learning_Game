import pygame

from states.base import State
from states.coding import CodingState
from ui import draw_panel, wrap_text


class DialogueState(State):
    """NPC speaks (typewriter effect), then the coding screen opens."""

    transparent = True  # the frozen map stays visible behind the box
    CHARS_PER_SECOND = 40

    def __init__(self, game, task):
        super().__init__(game)
        self.task = task
        self.font = pygame.font.Font(None, 26)
        self.name_font = pygame.font.Font(None, 32)
        self.text = task["story"]
        self.progress = 0.0

    @property
    def finished(self):
        return self.progress >= len(self.text)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if not self.finished:
                self.progress = len(self.text)  # skip the typewriter
            else:
                # replace dialogue by the coding screen
                self.game.change_state(CodingState(self.game, self.task))
        elif event.key == pygame.K_ESCAPE:
            self.game.pop_state()  # back to exploring

    def update(self, dt):
        if not self.finished:
            self.progress += self.CHARS_PER_SECOND * dt

    def draw(self, screen):
        box = pygame.Rect(40, 410, 720, 160)
        draw_panel(screen, box)

        name = self.name_font.render(self.task["npc"], True, (255, 220, 120))
        screen.blit(name, (box.x + 16, box.y + 10))

        # wrap the FULL text first so words don't jump while typing
        remaining = int(self.progress)
        y = box.y + 48
        for line in wrap_text(self.text, self.font, box.width - 32):
            if remaining <= 0:
                break
            surf = self.font.render(line[:remaining], True, (240, 240, 240))
            screen.blit(surf, (box.x + 16, y))
            remaining -= len(line) + 1
            y += 26

        if self.finished:
            hint = self.font.render("Enter - continue", True, (160, 160, 180))
            screen.blit(hint, hint.get_rect(bottomright=(box.right - 16, box.bottom - 10)))
