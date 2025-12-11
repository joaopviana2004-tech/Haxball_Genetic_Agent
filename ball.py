import pygame
from entity import Entity
import math
import config

class Ball(Entity):
    def __init__(self, begin, end, screen, players):
        largura = end[0] - begin[0] 
        altura = end[1] - begin[1]
        
        # Posição inicial no centro
        x_pos = begin[0] + largura/2
        y_pos = begin[1] + altura/2
        
        radius = (altura * config.RADIUS_SCALE) / 2
        
        super().__init__(x_pos, y_pos, begin, end, screen, radius, config.BALL_COLOR, speed=0)

        self.players = players
        
        # Vetores de velocidade (Física real)
        self.vx = 0
        self.vy = 0
        
        self.rect = pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

    def movimentacao(self):
        # 1. Aplica Velocidade
        self.x += self.vx
        self.y += self.vy

        # 2. Aplica Fricção (Simula o peso/atrito da grama)
        self.vx *= config.BALL_FRICTION
        self.vy *= config.BALL_FRICTION

        # Para completamente se a velocidade for muito baixa (evita deslizamento infinito)
        if abs(self.vx) < 0.1: self.vx = 0
        if abs(self.vy) < 0.1: self.vy = 0

        # 3. Verifica Colisões
        self._check_border_collision()
        self._check_player_collision()

    def _check_border_collision(self):
        # Colisão com Paredes Laterais
        if self.x - self.radius < self.begin[0]:
            self.x = self.begin[0] + self.radius
            self.vx *= -1 # Inverte velocidade (quique)
        elif self.x + self.radius > self.end[0]:
            self.x = self.end[0] - self.radius
            self.vx *= -1

        # Colisão com Teto/Chão
        if self.y - self.radius < self.begin[1]:
            self.y = self.begin[1] + self.radius
            self.vy *= -1
        elif self.y + self.radius > self.end[1]:
            self.y = self.end[1] - self.radius
            self.vy *= -1

    def _check_player_collision(self):
        for player in self.players:
            # Distância entre os centros
            dx = self.x - player.x
            dy = self.y - player.y
            distance = math.hypot(dx, dy)
            
            min_distance = self.radius + player.radius

            if distance < min_distance:
                # COLISÃO DETECTADA
                
                # 1. Calcular ângulo da colisão
                if distance == 0: distance = 0.1 # Evitar divisão por zero
                angle = math.atan2(dy, dx)
                
                # 2. Correção de Posição (Empurrar a bola para fora do player imediatamente)
                # Isso impede que eles fiquem grudados ("entrem um no outro")
                overlap = min_distance - distance
                self.x += math.cos(angle) * overlap
                self.y += math.sin(angle) * overlap
                
                # 3. Transferência de Energia (Chute)
                # Adiciona força na direção que o player está empurrando a bola
                # Quanto mais rápido o bot/player, maior o 'kick_power'
                kick_power = 0.5 # Força base do empurrão
                
                # Se o player estiver se movendo, adiciona velocidade extra
                # (Assumimos velocidade base do player config.PLAYER_SPEED ou BOT_SPEED como referência)
                self.vx += math.cos(angle) * (player.speed * kick_power + 2) 
                self.vy += math.sin(angle) * (player.speed * kick_power + 2)

    def update(self):
        self.movimentacao()
        self.rect.center = (int(self.x), int(self.y))
        self.draw()