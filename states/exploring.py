import pygame
import pytmx
import pyscroll

from player import Player
from states.base import State
from states.dialogue import DialogueState
from states.task_menu import TaskMenuState
from ui import draw_panel

# Every map of the game: file + camera zoom
MAPS = {
    "world": {"file": "carte.tmx", "zoom": 1.5},
    "house": {"file": "house.tmx", "zoom": 1.5},
}

# Doors: name of the trigger object in Tiled -> (destination map, spawn object in that map)
PORTALS = {
    "world": {"enter_house": ("house", "spawn")},
    "house": {"exit_house": ("world", "enter_house_exit")},
}


class ExploringState(State):
    """Walking around the village and the buildings."""

    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 24)
        self.tasks_hint = self.font.render("J - Tasks", True, (255, 255, 255))

        self.player = Player(0, 0)
        self.map_name = None
        self.group = None
        self.walls = []
        self.npcs = []      # (interaction_rect, task_id)
        self.portals = []   # (door_rect, destination_map, destination_spawn)
        self.nearby_task = None

        self.load_map("world", "player")

    # ---------- map loading (used at start AND for every door) ----------
    def load_map(self, name, spawn_name):
        info = MAPS[name]
        tmx_data = pytmx.util_pygame.load_pygame(str(self.game.base_dir / info["file"]))
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(
            map_data, self.game.screen.get_size()
        )
        map_layer.zoom = info["zoom"]

        # read the objects of THIS map
        self.walls, self.npcs, self.portals = [], [], []
        for obj in tmx_data.objects:
            rect = pygame.Rect(obj.x, obj.y, obj.width or 16, obj.height or 16)
            if obj.type == "collision":
                self.walls.append(rect)
            elif obj.type == "npc":
                task_id = obj.properties.get("task_id")
                self.npcs.append((rect.inflate(32, 32), task_id))
            elif obj.name in PORTALS[name]:
                dest_map, dest_spawn = PORTALS[name][obj.name]
                self.portals.append((rect, dest_map, dest_spawn))

        # new sprite group for the new map
        if self.group:
            self.group.remove(self.player)
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=3)
        self.group.add(self.player)

        # put the player on the spawn point of this map
        spawn = tmx_data.get_object_by_name(spawn_name)
        self.place_player(spawn.x, spawn.y)
        self.map_name = name
        self.nearby_task = None

    def place_player(self, x, y):
        """Put the player's FEET on the point (x, y)."""
        p = self.player
        p.position = [x - p.rect.width / 2, y - p.rect.height]
        p.old_position = p.position.copy()  # otherwise move_back() would send us to the old map
        p.update()                          # refresh rect and feet immediately

    # ---------- events ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e and self.nearby_task is not None:
                task = self.game.tasks[self.nearby_task]
                self.game.push_state(DialogueState(self.game, task))
            elif event.key == pygame.K_j:
                self.game.push_state(TaskMenuState(self.game))

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

        # doors: walking into a door rectangle loads the destination map
        for rect, dest_map, dest_spawn in self.portals:
            if self.player.feet.colliderect(rect):
                self.load_map(dest_map, dest_spawn)
                break

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

        # permanent hint in the top-right corner
        hint_rect = self.tasks_hint.get_rect(topright=(screen.get_width() - 20, 16))
        draw_panel(screen, hint_rect.inflate(24, 14))
        screen.blit(self.tasks_hint, hint_rect)

        if self.nearby_task is not None:
            task = self.game.tasks[self.nearby_task]
            done = self.nearby_task in self.game.completed
            label = f"E - talk to {task['npc']}" + ("  (done)" if done else "")
            text = self.font.render(label, True, (255, 255, 255))
            rect = text.get_rect(midbottom=(screen.get_width() // 2, screen.get_height() - 20))
            draw_panel(screen, rect.inflate(24, 14))
            screen.blit(text, rect)