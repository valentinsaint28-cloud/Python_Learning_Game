import pygame
from pathlib import Path



class Pypad:
    def __init__(self, screen):
        self.screen = screen
        self.visible = False
        self.code_str = ""
        self.bar = {"is_shown":False, "timer":0}

        assets = Path(__file__).resolve().parent / "assets"
        self.bg = pygame.image.load(str(assets / "pypad.png")).convert_alpha()

        self.panel = pygame.Rect(0, 0, 550, 400)
        self.panel.center = screen.get_rect().center

        self.close_button = pygame.Rect(0, 0, 60, 40)
        self.close_button.midbottom = (self.panel.x + 505, self.panel.y + 50)

        self.code_rect = pygame.Rect(0, 0, 200, 275)
        self.code_rect.midbottom = (self.panel.x + 134, self.panel.y + 357)

        font_path = Path(__file__).resolve().parent / "assets" / "PixelFont.ttf"
        font = pygame.font.Font(str(font_path), 24)
        font.set_bold(True)
        font_code = pygame.font.Font(str(font_path), 16)
        self.title = font.render("PyPad", True, (255, 255, 255))
        self.close_text = font.render("X", True, (255, 255, 255))
    #    self.test_code_test = font.render("Test Code", True, (255, 255, 255))
        self.code_font = font_code

        self.title_rect = self.title.get_rect(center=(self.panel.x + 85, self.panel.y + 25))

        self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150))



    def open(self):
        self.visible = True

    def close(self):
        self.visible = False

    def update_code_screen(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.code_str = self.code_str[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.code_str += "\n"
        elif event.unicode.isprintable():
            self.code_str += event.unicode
        

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button.collidepoint(event.pos):
                self.close()
        elif event.type == pygame.KEYDOWN:
            self.update_code_screen(event)

    def draw(self):
        if not self.visible:
            return

        #main asset
        self.screen.blit(self.overlay, (0, 0))
        self.screen.blit(self.bg, self.panel.topleft)

        #pypad component
        self.screen.blit(self.title, self.title_rect)

        self.screen.blit(self.close_text, self.close_text.get_rect(center=self.close_button.center))

        previous_clip = self.screen.get_clip()
        self.screen.set_clip(previous_clip.clip(self.code_rect))

        x = self.code_rect.left + 6
        y = self.code_rect.top + 6

        self.bar["timer"]+=1
        if self.bar["timer"] == 10:
            self.bar["timer"]=0
            self.bar["is_shown"] = not self.bar["is_shown"]
     

        for idx, line in enumerate(self.code_str.split("\n")):
            if idx == len(self.code_str.split("\n")) - 1 and self.bar["is_shown"]:
                line+='|'
            text = self.code_font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (x, y))
            y += self.code_font.get_linesize()
        
        


        self.screen.set_clip(previous_clip)


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

    