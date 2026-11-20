import pygame
from pathlib import Path



class Pypad:
    def __init__(self, screen):
        image_path = Path(__file__).resolve().parent / "assets" / "pypad.png"
        image = pygame.image.load(str(image_path)).convert_alpha()


        self.bg = image
        self.visible = False
        self.screen=screen

        self.panel = pygame.Rect(0, 0, 550, 400)
        self.panel.center = screen.get_rect().center

        self.close_button = pygame.Rect(0, 0, 60, 40)
        self.close_button.midbottom = (self.panel.x + 505, self.panel.y + 50)


        font_path = Path(__file__).resolve().parent / "assets" / "PixelFont.ttf"
        font = pygame.font.Font(str(font_path), 24)
        font.set_bold(True)
        self.title = font.render("PyPad", True, (255, 255, 255))
        self.close_text = font.render("X", True, (255, 255, 255))

        self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150))

    def open(self):
        self.visible = True

    def close(self):
        self.visible = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button.collidepoint(event.pos):
                self.close()

    def draw(self):
        if not self.visible:
            return

        self.screen.blit(self.overlay, (0, 0))
        self.screen.blit(self.bg, self.panel.topleft)
        title_rect = self.title.get_rect(center=(self.panel.x + 85, self.panel.y + 25))
        self.screen.blit(self.title, title_rect)

        self.screen.blit(self.close_text, self.close_text.get_rect(center=self.close_button.center))


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

    