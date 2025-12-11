import pygame
from entity import Entity

class Player(Entity):
    def __init__(self, x, y, color=(0, 0, 255)):
        super().__init__(x, y, radius=20, color=color, speed=5)

    def update(self, keys):
        dx = dy = 0

        if keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_s]:
            dy = 1
        if keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_d]:
            dx = 1

        self.move(dx, dy)
