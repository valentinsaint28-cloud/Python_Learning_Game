import pygame

from states.base import State
from ui import draw_panel, wrap_text


class CodingState(State):
    """Full-screen coding view.

    Left: story / lesson / objective.  Right: the code editor area.
    The real editor (typing, cursor, run button, output panel) is still a
    TODO: replce with Theos Coding interface
    """

    def __init__(self, game, task):
        super().__init__(game)
        self.task = task
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
        self.code = task["starter_code"]  # TODO: replace by an editor object
        self.output = ""
        self.hints_shown = 0

    # ---------- called by the editor when the player presses Run ----------
    def on_success(self):
        self.game.completed.add(self.task["id"])
        self.game.pop_state()  # back to exploring

    def show_next_hint(self):
        self.hints_shown = min(self.hints_shown + 1, len(self.task["hints"]))

    # ---------- state interface ----------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.game.pop_state()
        elif event.key == pygame.K_F1:
            self.show_next_hint()
        elif event.key == pygame.K_F9:
            self.on_success()  # debug shortcut until the editor exists
        # TODO: forward typing events to the editor here

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((25, 25, 40))
        left = pygame.Rect(20, 20, 330, 560)
        right = pygame.Rect(370, 20, 410, 560)
        draw_panel(screen, left)
        draw_panel(screen, right)

        # --- left panel: info ---
        t = self.task
        y = left.y + 12
        screen.blit(self.title_font.render(t["name"], True, (255, 220, 120)), (left.x + 14, y))
        y += 40
        for label, key in (("Story", "story"), ("Lesson", "lesson"), ("Goal", "objective")):
            screen.blit(self.font.render(label, True, (120, 200, 255)), (left.x + 14, y))
            y += 24
            for line in wrap_text(t[key], self.font, left.width - 28):
                screen.blit(self.font.render(line, True, (230, 230, 230)), (left.x + 14, y))
                y += 22
            y += 10

        for i in range(self.hints_shown):
            line = f"Hint {i + 1}: {t['hints'][i]}"
            for part in wrap_text(line, self.font, left.width - 28):
                screen.blit(self.font.render(part, True, (255, 180, 100)), (left.x + 14, y))
                y += 22

        # --- right panel: editor placeholder ---
        mono = pygame.font.SysFont("consolas,couriernew,monospace", 18)
        y = right.y + 14
        for line in self.code.split("\n"):
            screen.blit(mono.render(line, True, (200, 255, 200)), (right.x + 14, y))
            y += 22

        footer = self.font.render("Esc: leave   F1: hint   F9: (debug) complete", True, (160, 160, 180))
        screen.blit(footer, (right.x + 14, right.bottom - 30))
