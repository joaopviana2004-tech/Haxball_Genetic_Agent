import pygame
from entity import Entity
import random
import math # Importante para manter a velocidade constante
import config

class Ball(Entity):
    def __init__(self, begin, end, screen, players):
        x_pos = begin[0] 
        y_pos = begin[1]
        
        largura = end[0] - begin[0] 
        altura = end[1] - begin[1]

        radius = largura/30
        speed = largura/30

        self.players = players

        super().__init__(x_pos + largura/2, y_pos + altura/2, begin, end, screen, radius, (255,255,255), speed)

        self.direction_x = random.choice([-1, 1]) 
        self.direction_y = random.choice([-0.8, 0.8]) # Evita começar 100% na diagonal perfeita

        # Criação inicial do rect
        self.rect = pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )
        
        # Garante que o vetor inicial seja unitário (tamanho 1)
        self._normalize_direction()

    def _normalize_direction(self):
        """Garante que a velocidade da bola seja sempre a mesma, apenas mudando a direção"""
        magnitude = math.sqrt(self.direction_x**2 + self.direction_y**2)
        if magnitude == 0:
            return
        self.direction_x /= magnitude
        self.direction_y /= magnitude

    def _check_border_collision(self):
        hit_wall = False

        # --- Colisão Vertical (Teto e Chão) ---
        if self.y - self.radius <= self.begin[1]: # Bateu no teto
            self.y = self.begin[1] + self.radius + 1 # CORREÇÃO POSICIONAL (Empurra para baixo)
            self.direction_y *= -1 
            self.direction_x += random.uniform(-config.BALL_VARIANCE, config.BALL_VARIANCE)
            hit_wall = True
            
        elif self.y + self.radius >= self.end[1]: # Bateu no chão
            self.y = self.end[1] - self.radius - 1 # CORREÇÃO POSICIONAL (Empurra para cima)
            self.direction_y *= -1 
            self.direction_x += random.uniform(-config.BALL_VARIANCE, config.BALL_VARIANCE)
            hit_wall = True

        # --- Colisão Horizontal (Paredes laterais - se existirem como barreira) ---
        if self.x - self.radius <= self.begin[0]:
            self.x = self.begin[0] + self.radius + 1 # CORREÇÃO POSICIONAL
            self.direction_x *= -1 
            self.direction_y += random.uniform(-config.BALL_VARIANCE, config.BALL_VARIANCE)
            hit_wall = True
            
        elif self.x + self.radius >= self.end[0]:
            self.x = self.end[0] - self.radius - 1 # CORREÇÃO POSICIONAL
            self.direction_x *= -1 
            self.direction_y += random.uniform(-config.BALL_VARIANCE, config.BALL_VARIANCE)
            hit_wall = True

        if hit_wall:
            self._normalize_direction()

    def _check_player_collision(self):
        for player in self.players:
            if self.rect.colliderect(player.rect):
                
                # Inverte a direção horizontal
                self.direction_x *= -1
                
                # CORREÇÃO POSICIONAL: Tira a bola de dentro do player
                if self.direction_x > 0: # Bola indo para direita
                    self.x = player.rect.right + self.radius + 1
                else: # Bola indo para esquerda
                    self.x = player.rect.left - self.radius - 1
                
                # Adiciona efeito baseado em onde bateu no player (opcional, usa a variancia)
                # Se bater nas pontas, angula mais.
                diff_y = self.y - player.rect.centery
                self.direction_y += diff_y * 0.005 # Fator de sensibilidade simples

                self._normalize_direction()
                return # Só colide com um player por vez

    def movimentacao(self):
        # 1. Atualiza Posição
        self.x += self.speed * self.direction_x
        self.y += self.speed * self.direction_y
        
        # 2. Verifica Colisões (e corrige posição se necessário)
        self._check_border_collision()
        self._check_player_collision()
        
        # 3. Garante que a bola não fique presa na vertical (loop infinito)
        # Se direction_x for muito pequeno (perto de 0), forçamos um mínimo
        if abs(self.direction_x) < 0.2: 
            self.direction_x = 0.2 if self.direction_x > 0 else -0.2
            self._normalize_direction()

    def update(self):
        self.movimentacao()
        # Atualiza o rect para o desenho e próxima verificação física
        self.rect.center = (int(self.x), int(self.y))
        self.draw()