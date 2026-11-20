import pygame
import pytmx
import pyscroll

from player import Player
from states.base import State
from states.dialogue import DialogueState
from ui import draw_panel


class ExploringState(State):
    """Walking around the village (what used to be in Game)."""

    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 24)

        # --- map ---
        tmx_data = pytmx.util_pygame.load_pygame(str(game.base_dir / "carte.tmx"))
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(
            map_data, game.screen.get_size()
        )
        map_layer.zoom = 1.5

        # --- player ---
        spawn = tmx_data.get_object_by_name("player")
        self.player = Player(spawn.x, spawn.y)

        # --- collisions + NPCs (read from the Tiled objects layer) ---
        self.walls = []
        self.npcs = []  # list of (interaction_rect, task_id)
        for obj in tmx_data.objects:
            if obj.type == "collision":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            elif obj.type == "npc":
                # In Tiled: object of type "npc" with a custom int property "task_id"
                task_id = obj.properties.get("task_id")
                rect = pygame.Rect(obj.x, obj.y, obj.width or 16, obj.height or 16)
                self.npcs.append((rect.inflate(32, 32), task_id))

        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=3)
        self.group.add(self.player)

        self.nearby_task = None  # task id of the NPC we could talk to

    # ---------- events ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self.nearby_task is not None:
                task = self.game.tasks[self.nearby_task]
                self.game.push_state(DialogueState(self.game, task))

    # ---------- update ----------
    def handle_input(self):
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_UP]:
            self.player.move_up()
            self.player.change_animation("up")
        elif pressed[pygame.K_DOWN]:
            self.player.move_down()
            self.player.change_animation("down")
        elif pressed[pygame.K_RIGHT]:
            self.player.move_right()
            self.player.change_animation("right")
        elif pressed[pygame.K_LEFT]:
            self.player.move_left()
            self.player.change_animation("left")

    def update(self, dt):
        self.player.save_location()
        self.handle_input()
        self.group.update()

        # wall collisions
        for sprite in self.group.sprites():
            if sprite.feet.collidelist(self.walls) > -1:
                sprite.move_back()

        # NPC proximity
        self.nearby_task = None
        for zone, task_id in self.npcs:
            if self.player.feet.colliderect(zone) and task_id in self.game.tasks:
                self.nearby_task = task_id
                break

        self.group.center(self.player.rect.center)

    # ---------- draw ----------
    def draw(self, screen):
        self.group.draw(screen)

        if self.nearby_task is not None:
            task = self.game.tasks[self.nearby_task]
            done = self.nearby_task in self.game.completed
            label = f"E - talk to {task['npc']}" + ("  (done)" if done else "")
            text = self.font.render(label, True, (255, 255, 255))
            rect = text.get_rect(midbottom=(screen.get_width() // 2, screen.get_height() - 20))
            draw_panel(screen, rect.inflate(24, 14))
            screen.blit(text, rect)
