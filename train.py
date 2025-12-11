import pygame
from quadra import Quadra
from player import Player
from bot import Bot
import config

pygame.init()
screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
pygame.display.set_caption("Haxball em Python")


quadras = [] 


cell_width = config.WINDOW_WIDTH / config.COLUMNS
cell_height = config.WINDOW_HEIGHT / config.ROWS


for y in range(config.ROWS): 
    for x in range(config.COLUMNS):
        coord_x_inicial = x * cell_width
        coord_x_final = (x + 1) * cell_width

        coord_y_inicial = y * cell_height
        coord_y_final = (y + 1) * cell_height
        
        begin = (coord_x_inicial,  coord_y_inicial)
        final = (coord_x_final,  coord_y_final)
        
        quadras.append(Quadra(screen, begin, final , []))

clock = pygame.time.Clock()
running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    screen.fill((0, 0, 0))
    [quadra.update() for quadra in quadras]
    pygame.display.flip()

pygame.quit()
