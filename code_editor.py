import pygame


class CodeEditor:
    def __init__(self, rect, font):
        self.rect = rect
        self.font = font
        self.text = ""
        self.cursor = 0
        self.preferred_column = None
        self.first_row = 0
        self.follow_cursor = True
        self.last_key_time = pygame.time.get_ticks()

    def _display_rows(self):
        rows = []
        offset = 0
        max_width = self.rect.width - 14

        for line in self.text.split("\n"):
            start = offset
            part = ""

            for char in line:
                if part and self.font.size(part + char)[0] > max_width:
                    rows.append((start, part))
                    start += len(part)
                    part = ""
                part += char

            rows.append((start, part))
            offset += len(line) + 1

        return rows

    def _cursor_row(self, rows):
        return max(i for i, (start, _) in enumerate(rows) if start <= self.cursor)

    def _move_vertically(self, direction):
        rows = self._display_rows()
        row = self._cursor_row(rows)

        if self.preferred_column is None:
            self.preferred_column = self.cursor - rows[row][0]

        target = row + direction
        if 0 <= target < len(rows):
            start, line = rows[target]
            end = start + len(line)

            # Au bord d'un retour automatique, le curseur appartient à la ligne suivante.
            if target + 1 < len(rows):
                end = min(end, rows[target + 1][0] - 1)

            self.cursor = min(start + self.preferred_column, end)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.first_row -= event.y * 3
            self.follow_cursor = False
            return

        if event.type != pygame.KEYDOWN:
            return

        key = event.key
        pos = self.cursor

        if key == pygame.K_UP:
            self._move_vertically(-1)
        elif key == pygame.K_DOWN:
            self._move_vertically(1)
        elif key == pygame.K_LEFT:
            self.cursor = max(0, pos - 1)
        elif key == pygame.K_RIGHT:
            self.cursor = min(len(self.text), pos + 1)
        elif key == pygame.K_BACKSPACE:
            if pos > 0:
                self.text = self.text[:pos - 1] + self.text[pos:]
                self.cursor -= 1
        elif key == pygame.K_DELETE:
            self.text = self.text[:pos] + self.text[pos + 1:]
        else:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                inserted = "\n"
            elif event.unicode.isprintable():
                inserted = event.unicode
            else:
                return

            self.text = self.text[:pos] + inserted + self.text[pos:]
            self.cursor += len(inserted)

        if key not in (pygame.K_UP, pygame.K_DOWN):
            self.preferred_column = None

        self.follow_cursor = True
        self.last_key_time = pygame.time.get_ticks()

    def draw(self, screen):
        rows = self._display_rows()
        cursor_row = self._cursor_row(rows)
        line_height = self.font.get_linesize()
        visible_count = max(1, (self.rect.height - 12) // line_height)

        if self.follow_cursor:
            if cursor_row < self.first_row:
                self.first_row = cursor_row
            elif cursor_row >= self.first_row + visible_count:
                self.first_row = cursor_row - visible_count + 1
            self.follow_cursor = False

        max_scroll = max(0, len(rows) - visible_count)
        self.first_row = max(0, min(self.first_row, max_scroll))

        previous_clip = screen.get_clip()
        screen.set_clip(previous_clip.clip(self.rect))

        x = self.rect.left + 6
        y = self.rect.top + 6
        end = min(len(rows), self.first_row + visible_count)
        show_cursor = (pygame.time.get_ticks() - self.last_key_time) % 1000 < 500
        color = (255, 255, 255)

        for index in range(self.first_row, end):
            start, line = rows[index]
            screen.blit(self.font.render(line, True, color), (x, y))

            if index == cursor_row and show_cursor:
                prefix = line[:self.cursor - start]
                cursor_x = x + self.font.size(prefix)[0]
                pygame.draw.line(
                    screen, color,
                    (cursor_x, y), (cursor_x, y + self.font.get_height() - 1),
                )

            y += line_height

        screen.set_clip(previous_clip)