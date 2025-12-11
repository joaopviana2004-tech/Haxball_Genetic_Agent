import pygame
import config

from player import Player
from bot import Bot
from ball import Ball

class Quadra:
    def __init__(self, screen, begin, end, players):
        self.screen = screen
        self.begin = begin
        self.end = end
        self.color = config.Variate_grass_color()

        self.x_pos = self.begin[0] 
        self.y_pos = self.begin[1]
        
        self.largura = self.end[0] - self.begin[0] 
        self.altura = self.end[1] - self.begin[1]

        self.grossura_proporcional = int(self.altura / 100) 
        self.grossura = max(2, min(self.grossura_proporcional, 6))
        
        self.players = []
        for i in  range(len(players)):
            if(players[i] == 'bot'):
                individuo = Bot()
            elif(players[i] == 'player'):
                individuo = Player()
            # elif(players[i] == 'agent'):
            self.players.append(individuo)
        
        self.ball = Ball(begin, end, screen, players)

    def draw(self):
        pygame.draw.rect(self.screen, self.color, [self.x_pos, self.y_pos, self.largura, self.altura])
        pygame.draw.line(self.screen, config.LINE_COLOR, (self.x_pos + self.largura/2, self.y_pos), (self.x_pos + self.largura/2, self.end[1]), self.grossura)
        pygame.draw.circle(self.screen, config.LINE_COLOR, ( self.x_pos + self.largura/2, self.y_pos + self.altura/2), (self.altura)/10, self.grossura)

    def update(self):
        self.draw()
        self.ball.update()