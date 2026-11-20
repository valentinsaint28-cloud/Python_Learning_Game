import pygame


def wrap_text(text, font, max_width):
    """Split text into lines that fit in max_width pixels."""
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            test = f"{line} {word}".strip()
            if font.size(test)[0] <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw_panel(surface, rect, bg=(20, 20, 35), border=(230, 230, 240), alpha=235):
    """Semi-transparent panel with a border."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill((*bg, alpha))
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, border, rect, 3, border_radius=6)
