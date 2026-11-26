import pygame

from states.base import State
from ui import draw_panel, wrap_text

GREEN = (110, 220, 130)
YELLOW = (255, 220, 120)
GREY = (120, 120, 140)
WHITE = (240, 240, 240)
BLUE = (120, 200, 255)


class TaskMenuState(State):
    """Task list: shows which tasks are done, available or locked."""

    transparent = True  # the frozen map stays visible (dimmed) behind the menu
    VISIBLE_ROWS = 8
    ROW_HEIGHT = 46

    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 36)

        self.tasks = sorted(game.tasks.values(), key=lambda t: t["id"])
        self.selected = 0
        self.scroll = 0  # index of the first visible row

        # start on the first task that is available, if there is one
        for i, task in enumerate(self.tasks):
            if self.status(task) == "available":
                self.selected = i
                break
        self.keep_selection_visible()

    # ---------- task status ----------
    def is_unlocked(self, task):
        """Default rule: a task is unlocked when every task with a lower id is done.
        Replace the body with your own level rule if it is different."""
        return all(
            t["id"] in self.game.completed
            for t in self.tasks
            if t["id"] < task["id"]
        )

    def status(self, task):
        if task["id"] in self.game.completed:
            return "done"
        if self.is_unlocked(task):
            return "available"
        return "locked"

    def blocking_task(self, task):
        """First unfinished task before this one (what the player must do first)."""
        for t in self.tasks:
            if t["id"] < task["id"] and t["id"] not in self.game.completed:
                return t
        return None

    # ---------- events ----------
    def keep_selection_visible(self):
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + self.VISIBLE_ROWS:
            self.scroll = self.selected - self.VISIBLE_ROWS + 1

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_j, pygame.K_TAB):
            self.game.pop_state()
        elif event.key == pygame.K_UP:
            self.selected = max(0, self.selected - 1)
            self.keep_selection_visible()
        elif event.key == pygame.K_DOWN:
            self.selected = min(len(self.tasks) - 1, self.selected + 1)
            self.keep_selection_visible()

    # ---------- drawing ----------
    def draw_icon(self, screen, status, center):
        """Small icon drawn with shapes (the default font has no check/lock glyphs)."""
        x, y = center
        if status == "done":
            pygame.draw.circle(screen, GREEN, center, 11)
            pygame.draw.lines(screen, (20, 40, 25), False,
                              [(x - 5, y), (x - 1, y + 5), (x + 6, y - 5)], 3)
        elif status == "available":
            pygame.draw.circle(screen, YELLOW, center, 11)
            pygame.draw.circle(screen, (20, 20, 35), center, 4)
        else:
            pygame.draw.circle(screen, GREY, center, 11, 3)
            pygame.draw.line(screen, GREY, (x - 6, y), (x + 6, y), 3)

    def draw(self, screen):
        # dim the map
        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        screen.blit(dim, (0, 0))

        panel = pygame.Rect(50, 40, 700, 520)
        draw_panel(screen, panel)

        done_count = sum(1 for t in self.tasks if t["id"] in self.game.completed)
        title = self.title_font.render(f"Tasks  {done_count}/{len(self.tasks)}", True, YELLOW)
        screen.blit(title, (panel.x + 20, panel.y + 16))

        # ----- left: list -----
        list_x = panel.x + 20
        list_y = panel.y + 70
        list_w = 290
        rows = self.tasks[self.scroll:self.scroll + self.VISIBLE_ROWS]
        for i, task in enumerate(rows):
            index = self.scroll + i
            status = self.status(task)
            row = pygame.Rect(list_x, list_y + i * self.ROW_HEIGHT, list_w, self.ROW_HEIGHT - 6)

            if index == self.selected:
                pygame.draw.rect(screen, (60, 60, 95), row, border_radius=6)
                pygame.draw.rect(screen, WHITE, row, 2, border_radius=6)

            self.draw_icon(screen, status, (row.x + 20, row.centery))

            color = {"done": GREEN, "available": WHITE, "locked": GREY}[status]
            name = task["name"] if status != "locked" else "???"
            screen.blit(self.font.render(name, True, color), (row.x + 42, row.y + 5))
            sub = self.small_font.render(f"with {task['npc']}", True, GREY)
            screen.blit(sub, (row.x + 42, row.y + 24))

        # scroll arrows
        if self.scroll > 0:
            pygame.draw.polygon(screen, WHITE, [(list_x + list_w // 2, list_y - 14),
                                                (list_x + list_w // 2 - 7, list_y - 4),
                                                (list_x + list_w // 2 + 7, list_y - 4)])
        if self.scroll + self.VISIBLE_ROWS < len(self.tasks):
            by = list_y + self.VISIBLE_ROWS * self.ROW_HEIGHT
            pygame.draw.polygon(screen, WHITE, [(list_x + list_w // 2, by + 4),
                                                (list_x + list_w // 2 - 7, by - 6),
                                                (list_x + list_w // 2 + 7, by - 6)])

        # ----- right: details of the selected task -----
        detail = pygame.Rect(panel.x + 330, panel.y + 70, panel.width - 350, panel.height - 130)
        pygame.draw.rect(screen, (30, 30, 50), detail, border_radius=6)
        pygame.draw.rect(screen, GREY, detail, 2, border_radius=6)
        self.draw_details(screen, detail, self.tasks[self.selected])

        footer = self.small_font.render("Up/Down: select      Esc / J: close", True, GREY)
        screen.blit(footer, (panel.x + 20, panel.bottom - 34))

    def draw_details(self, screen, rect, task):
        status = self.status(task)
        x, y = rect.x + 16, rect.y + 14
        max_w = rect.width - 32

        if status == "locked":
            screen.blit(self.title_font.render("???", True, GREY), (x, y))
            y += 46
            blocker = self.blocking_task(task)
            msg = "Locked."
            if blocker:
                msg = f"Locked. Finish \"{blocker['name']}\" first."
            for line in wrap_text(msg, self.font, max_w):
                screen.blit(self.font.render(line, True, GREY), (x, y))
                y += 26
            return

        screen.blit(self.title_font.render(task["name"], True, YELLOW), (x, y))
        y += 40
        label, color = ("Completed", GREEN) if status == "done" else ("Available", YELLOW)
        screen.blit(self.font.render(label, True, color), (x, y))
        y += 28
        screen.blit(self.font.render(f"Helper: {task['npc']}", True, BLUE), (x, y))
        y += 38

        screen.blit(self.font.render("Goal", True, BLUE), (x, y))
        y += 26
        for line in wrap_text(task["objective"], self.font, max_w):
            screen.blit(self.font.render(line, True, WHITE), (x, y))
            y += 24
