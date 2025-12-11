import pygame
import config
import math # Necessário para colisão

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
        self.ball = Ball(begin, end, screen, self.players) # Passa lista vazia inicialmente
        
        # Cria os players
        for i in range(len(players)):
            if(players[i] == 'bot'):
                # Bot recebe target=self.ball
                individuo = Bot(begin, end, i % 2, screen, target=self.ball)
            elif(players[i] == 'player'):
                individuo = Player(begin, end, i % 2, screen) # Assumindo construtor padrão
            self.players.append(individuo)
            
        # Atualiza a referência de players na bola (agora que a lista está cheia)
        self.ball.players = self.players

    def check_entities_collision(self):
        """Verifica e resolve colisão entre players/bots (Círculo x Círculo)"""
        for i in range(len(self.players)):
            for j in range(i + 1, len(self.players)):
                p1 = self.players[i]
                p2 = self.players[j]

                dx = p1.x - p2.x
                dy = p1.y - p2.y
                dist = math.hypot(dx, dy)
                
                min_dist = p1.radius + p2.radius

                if dist < min_dist:
                    # Estão colidindo!
                    if dist == 0: dist = 0.1 # Evita erro math
                    
                    # Calcula o quanto precisam se afastar
                    overlap = min_dist - dist
                    
                    # Vetor normalizado da colisão
                    nx = dx / dist
                    ny = dy / dist
                    
                    # Empurra cada um metade do overlap para lados opostos
                    p1.x += nx * (overlap / 2)
                    p1.y += ny * (overlap / 2)
                    p2.x -= nx * (overlap / 2)
                    p2.y -= ny * (overlap / 2)

    def draw(self):
        pygame.draw.rect(self.screen, self.color, [self.x_pos, self.y_pos, self.largura, self.altura])
        pygame.draw.line(self.screen, config.LINE_COLOR, (self.x_pos + self.largura/2, self.y_pos), (self.x_pos + self.largura/2, self.end[1]), self.grossura)
        pygame.draw.circle(self.screen, config.LINE_COLOR, ( self.x_pos + self.largura/2, self.y_pos + self.altura/2), (self.altura)/10, self.grossura)

    def update(self):
        self.draw()
        
        # 1. Resolve colisões entre jogadores ANTES de desenhar
        self.check_entities_collision()
        
        # 2. Atualiza a bola (que resolve colisão Bola x Jogador internamente)
        self.ball.update()
        
        # 3. Atualiza jogadores
        for p in self.players:
            p.update()