import pygame
import config
import math # Necessário para colisão

from player import Player
from bot import Bot
from ball import Ball
from goal import Goal

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
        self.score = [0, 0]
        # Cria traves (goals)
        self.goals = [Goal(begin, end, 'left', screen), Goal(begin, end, 'right', screen)]
        # Atribui goals e callback na bola
        self.ball.goals = self.goals
        self.ball.goal_callback = self._on_goal
        
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
                    
                    # Dissipa velocidade ao colidir (reduz bounce)
                    if hasattr(p1, 'vx'):
                        p1.vx *= 0.7
                        p1.vy *= 0.7
                    if hasattr(p2, 'vx'):
                        p2.vx *= 0.7
                        p2.vy *= 0.7

    def draw(self):
        pygame.draw.rect(self.screen, self.color, [self.x_pos, self.y_pos, self.largura, self.altura])
        pygame.draw.line(self.screen, config.LINE_COLOR, (self.x_pos + self.largura/2, self.y_pos), (self.x_pos + self.largura/2, self.end[1]), self.grossura)
        pygame.draw.circle(self.screen, config.LINE_COLOR, ( int(self.x_pos + self.largura/2), int(self.y_pos + self.altura/2)), int(self.altura/10), self.grossura)

    def update(self):
        self.draw()
        
        # 1. Resolve colisões entre jogadores ANTES de desenhar
        self.check_entities_collision()
        
        # 2. Atualiza a bola (que resolve colisão Bola x Jogador internamente)
        self.ball.update()
        
        # 3. Atualiza jogadores
        for p in self.players:
            p.update()

    def _on_goal(self, goal):
        # Incrementa pontuação do time que marcou
        self.score[goal.score_for] += 1

        # Reseta bola no centro
        largura = self.end[0] - self.begin[0]
        altura = self.end[1] - self.begin[1]
        center_x = self.begin[0] + largura / 2
        center_y = self.begin[1] + altura / 2
        self.ball.set_position(center_x, center_y)
        self.ball.vx = 0
        self.ball.vy = 0

        # Reposiciona jogadores na linha central dos seus lados
        for p in self.players:
            # decide lado pelo x atual (se estiver mais à esquerda -> time 0)
            if p.x < center_x:
                start_x = self.begin[0] + p.radius * 4
            else:
                start_x = self.end[0] - p.radius * 4
            p.set_position(start_x, center_y)
            
            # Reseta velocidades dos jogadores
            if hasattr(p, 'vx'):
                p.vx = 0
            if hasattr(p, 'vy'):
                p.vy = 0

    def draw(self):
        # Desenha gramado e linhas base
        pygame.draw.rect(self.screen, self.color, [self.x_pos, self.y_pos, self.largura, self.altura])
        pygame.draw.line(self.screen, config.LINE_COLOR, (self.x_pos + self.largura/2, self.y_pos), (self.x_pos + self.largura/2, self.end[1]), self.grossura)
        pygame.draw.circle(self.screen, config.LINE_COLOR, ( self.x_pos + self.largura/2, self.y_pos + self.altura/2), (self.altura)/10, self.grossura)

        # Desenha traves
        for g in self.goals:
            g.draw()

        # Desenha placar com tamanho proporcional à altura da quadra
        font_size = max(12, int(self.altura * 0.3))
        font = pygame.font.SysFont(None, font_size)
        
        # Time 0 (esquerda)
        score_0 = font.render(str(self.score[0]), True, config.LINE_COLOR)
        self.screen.blit(score_0, (self.x_pos + self.largura/4 - score_0.get_width()/2, self.y_pos + self.altura/2 - score_0.get_height()/2))
        
        # Time 1 (direita)
        score_1 = font.render(str(self.score[1]), True, config.LINE_COLOR)
        self.screen.blit(score_1, (self.x_pos + 3*self.largura/4 - score_1.get_width()/2, self.y_pos + self.altura/2 - score_1.get_height()/2))