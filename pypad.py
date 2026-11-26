import pygame
from pathlib import Path
from code_editor import CodeEditor


class Pypad:
    def __init__(self, screen):
        self.screen = screen
        self.visible = False

        assets = Path(__file__).resolve().parent / "assets"
        self.bg = pygame.image.load(str(assets / "bg.webp")).convert_alpha()
        self.code_bg = pygame.image.load(str(assets / "code_screen.webp")).convert_alpha()
        self.output_bg = pygame.image.load(str(assets / "output_screen.webp")).convert_alpha()
        self.close_bg = pygame.image.load(str(assets / "close_btn.webp")).convert_alpha()
        self.run_bg = pygame.image.load(str(assets / "run_btn.webp")).convert_alpha()

        self.panel = pygame.Rect(0, 0, 550, 400)
        self.panel.center = screen.get_rect().center

        self.close_button = self.close_bg.get_bounding_rect(min_alpha=128).move(
            self.panel.topleft
        )
        self.run_button = self.run_bg.get_bounding_rect(min_alpha=128).move(
            self.panel.topleft
        )

        self.code_rect = pygame.Rect(0, 0, 200, 275)
        self.code_rect.midbottom = (self.panel.x + 134, self.panel.y + 357)

        font_path = Path(__file__).resolve().parent / "assets" / "PixelFont.ttf"
        font = pygame.font.Font(str(font_path), 24)
        font.set_bold(True)
        font_code = pygame.font.Font(str(font_path), 16)
        self.title = font.render("PyPad", True, (255, 255, 255))
        self.close_text = font.render("X", True, (255, 255, 255))
        self.run_text = font.render("Run Code", True, (255, 255, 255))
        self.editor = CodeEditor(self.code_rect, font_code)

        self.title_rect = self.title.get_rect(center=(self.panel.x + 85, self.panel.y + 25))

        self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150))



    def open(self):
        self.visible = True

    def close(self):
        self.visible = False

    def run_code(self):
        print(self.editor.text)
        

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button.collidepoint(event.pos):
                self.close()
            if self.run_button.collidepoint(event.pos):
                self.run_code()
        else:
            self.editor.handle_event(event)

    def draw(self):
        if not self.visible:
            return

        #main asset
        self.screen.blit(self.overlay, (0, 0))

        self.screen.blit(self.bg, self.panel.topleft)
        self.screen.blit(self.code_bg, self.panel.topleft)
        self.screen.blit(self.output_bg, self.panel.topleft)
        self.screen.blit(self.close_bg, self.panel.topleft)
        self.screen.blit(self.run_bg, self.panel.topleft)

        #pypad component
        self.screen.blit(self.title, self.title_rect)

        self.screen.blit(self.close_text, self.close_text.get_rect(center=self.close_button.center))
        self.screen.blit(self.run_text, self.run_text.get_rect(center=self.run_button.center))

        self.editor.draw(self.screen)

if __name__=='__main__':
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("PyPad test")
    clock = pygame.time.Clock()

    pypad = Pypad(screen)
    pypad.open()

    while pypad.visible:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pypad.close()
            else:
                pypad.handle_event(event)

        screen.fill((35, 50, 65))
        pypad.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

    