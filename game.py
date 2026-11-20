import pygame
import pytmx
import pyscroll
from player import Player

class Game:
    
    def __init__(self):
        # window game
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("jeu de test")

        # charge the map
        tmx_data = pytmx.util_pygame.load_pygame('carte.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 1.5
        self.map = 'world'

        # add a player
        player_position = tmx_data.get_object_by_name("player")
        self.player = Player(player_position.x, player_position.y)

        # collisions list
        self.walls = []
        for i in tmx_data.objects:
            if i.type == "collision":
                self.walls.append(pygame.Rect(i.x, i.y, i.width, i.height))

        # draw the layers
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer = 5)
        self.group.add(self.player)

        #define the collision rect to enter the house
        enter_house = tmx_data.get_object_by_name("enter_house")
        self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)

    def handle_input(self):
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_UP]:
            self.player.move_up()
            self.player.change_animation('up')
        elif pressed[pygame.K_DOWN]:
            self.player.move_down()
            self.player.change_animation('down')
        elif pressed[pygame.K_RIGHT]:
            self.player.move_right()
            self.player.change_animation('right')
        elif pressed[pygame.K_LEFT]:
            self.player.move_left()
            self.player.change_animation('left')

    def switch_house(self):
        # charge the map
        tmx_data = pytmx.util_pygame.load_pygame('house.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 1.5

        # collisions list
        self.walls = []
        for i in tmx_data.objects:
            if i.type == "collision":
                self.walls.append(pygame.Rect(i.x, i.y, i.width, i.height))

        # draw the layers
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer = 5)
        self.group.add(self.player)

        #define the collision rect to exit the house
        enter_house = tmx_data.get_object_by_name("exit_house")
        self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)

        # spawn instanciation in front of the house-door
        spawn_housedoor_point = tmx_data.get_object_by_name("spawn")
        self.player.position[0] = spawn_housedoor_point.x
        self.player.position[1] = spawn_housedoor_point.y - 40

    def switch_world(self):
            # charge the map
            tmx_data = pytmx.util_pygame.load_pygame('carte.tmx')
            map_data = pyscroll.data.TiledMapData(tmx_data)
            map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
            map_layer.zoom = 1.5
    
            # collisions list
            self.walls = []
            for i in tmx_data.objects:
                if i.type == "collision":
                    self.walls.append(pygame.Rect(i.x, i.y, i.width, i.height))
    
            # draw the layers
            self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer = 5)
            self.group.add(self.player)
    
            #define the collision rect to exit the house
            enter_house = tmx_data.get_object_by_name("enter_house")
            self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)

            # spawn instanciation in front of the house
            spawn_house_point = tmx_data.get_object_by_name("enter_house_exit")
            self.player.position[0] = spawn_house_point.x
            self.player.position[1] = spawn_house_point.y + 20

    def update(self):
        self.group.update()

        # check the house entrance
        if self.map == 'world' and self.player.feet.colliderect(self.enter_house_rect):
            self.switch_house()
            self.map = 'house'

        elif self.map == 'house' and self.player.feet.colliderect(self.enter_house_rect):
            self.switch_world()
            self.map = 'world'

        # collisions verification
        for sprite in self.group.sprites():
            if sprite.feet.collidelist(self.walls) > -1 :
                sprite.move_back()

    def run(self):
        # FPS du jeu
        clock = pygame.time.Clock()

        # Boucle de jeu
        running = True
        while running:
            self.player.save_location()
            self.handle_input()
            self.update()
            self.group.center(self.player.rect.center)
            self.group.draw(self.screen)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            clock.tick(60)
        pygame.quit()