import io
import contextlib

import pygame

from code_editor import CodeEditor
from states.base import State
from ui import wrap_text


class PypadState(State):
    """The PyPad coding window, opened over the frozen map."""

    transparent = True  # the map stays visible behind the overlay

    def __init__(self, game, task):
        super().__init__(game)
        self.task = task
        screen = game.screen
        assets = game.base_dir / "assets"   # not Path(__file__): this file is in states/

        load = lambda name: pygame.image.load(str(assets / name)).convert_alpha()
        self.bg = load("bg.webp")
        self.code_bg = load("code_screen.webp")
        self.output_bg = load("output_screen.webp")
        self.close_bg = load("close_btn.webp")
        self.run_bg = load("run_btn.webp")

        self.panel = pygame.Rect(0, 0, 550, 400)
        self.panel.center = screen.get_rect().center

        self.close_button = self.close_bg.get_bounding_rect(min_alpha=128).move(self.panel.topleft)
        self.run_button = self.run_bg.get_bounding_rect(min_alpha=128).move(self.panel.topleft)

        self.code_rect = pygame.Rect(0, 0, 200, 275)
        self.code_rect.midbottom = (self.panel.x + 134, self.panel.y + 357)

        # Output area: adjust these numbers to match output_screen.webp
        self.output_rect = pygame.Rect(0, 0, 200, 275)
        self.output_rect.midbottom = (self.panel.x + 416, self.panel.y + 357)

        font_path = str(assets / "PixelFont.ttf")
        font = pygame.font.Font(font_path, 24)
        font.set_bold(True)
        self.code_font = pygame.font.Font(font_path, 16)
        self.title = font.render("PyPad", True, (255, 255, 255))
        self.close_text = font.render("X", True, (255, 255, 255))
        self.run_text = font.render("Run Code", True, (255, 255, 255))
        self.title_rect = self.title.get_rect(center=(self.panel.x + 85, self.panel.y + 25))

        self.editor = CodeEditor(self.code_rect, self.code_font)
        self.editor.text = task["starter_code"]
        self.editor.cursor = len(self.editor.text)

        self.output = ""
        self.hints_shown = 0

        self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150))

    # ---------- running the player's code ----------
    def run_code(self):
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                exec(self.editor.text, {})
        except Exception as e:
            self.output = buffer.getvalue() + f"{type(e).__name__}: {e}"
            return

        result = buffer.getvalue()
        if result.strip() == self.task["expected_output"].strip():
            self.game.completed.add(self.task["id"])
            self.output = result + "\nCorrect! Close PyPad to continue."
        else:
            self.output = result + "\nNot quite, try again!"

    def show_next_hint(self):
        hints = self.task["hints"]
        if self.hints_shown < len(hints):
            self.output = f"Hint {self.hints_shown + 1}: {hints[self.hints_shown]}"
            self.hints_shown += 1

    # ---------- state interface ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.pop_state()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.show_next_hint()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button.collidepoint(event.pos):
                self.game.pop_state()
            elif self.run_button.collidepoint(event.pos):
                self.run_code()
        else:
            self.editor.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))
        for img in (self.bg, self.code_bg, self.output_bg, self.close_bg, self.run_bg):
            screen.blit(img, self.panel.topleft)

        screen.blit(self.title, self.title_rect)
        screen.blit(self.close_text, self.close_text.get_rect(center=self.close_button.center))
        screen.blit(self.run_text, self.run_text.get_rect(center=self.run_button.center))
        self.editor.draw(screen)

        # output text
        y = self.output_rect.top + 6
        for line in wrap_text(self.output, self.code_font, self.output_rect.width - 14):
            if y > self.output_rect.bottom - 16:
                break
            screen.blit(self.code_font.render(line, True, (255, 255, 255)),
                        (self.output_rect.left + 6, y))
            y += self.code_font.get_linesize()