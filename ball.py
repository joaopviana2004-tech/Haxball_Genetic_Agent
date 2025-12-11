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
        
        # Bola escala com a menor dimensão da quadra
        size = min(largura, altura)
        radius = max(3, int(size * config.RADIUS_SCALE * 0.5))

        super().__init__(x_pos, y_pos, begin, end, screen, radius, config.BALL_COLOR, speed=0)

        self.players = players
        
        # Vetores de velocidade (Física real)
        self.vx = 0
        self.vy = 0
        
        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), int(self.radius * 2), int(self.radius * 2))

        # Lista de goals (será atribuída pela Quadra se existir)
        self.goals = []
        # Função callback a ser chamada quando um gol ocorrer: callback(goal)
        self.goal_callback = None

    def movimentacao(self):
        # 1. Aplica Velocidade
        self.x += self.vx
        self.y += self.vy

        # 2. Aplica Fricção gradual (Simula o peso/atrito da grama)
        # Reduz velocidade de forma mais suave e realista
        self.vx *= config.BALL_FRICTION
        self.vy *= config.BALL_FRICTION

        # Para completamente se a velocidade for muito baixa (evita deslizamento infinito)
        # Limiar ajustado para melhor responsividade
        if abs(self.vx) < 0.05: self.vx = 0
        if abs(self.vy) < 0.05: self.vy = 0

        # 3. Verifica Colisões
        self._check_border_collision()
        self._check_player_collision()

    def _check_border_collision(self):
        # Colisão com Teto/Chão (sempre)
        if self.y - self.radius < self.begin[1]:
            self.y = self.begin[1] + self.radius
            self.vy *= -0.8
        elif self.y + self.radius > self.end[1]:
            self.y = self.end[1] - self.radius
            self.vy *= -0.8

        # Colisão com Paredes Laterais
        # LEFT WALL: permitir passagem se for dentro de um goal
        if self.x - self.radius < self.begin[0]:
            left_goal = None
            for g in getattr(self, 'goals', []):
                if getattr(g, 'side', 'left') == 'left' and g.contains_ball(self):
                    left_goal = g
                    break

            if left_goal is not None:
                if callable(self.goal_callback):
                    self.goal_callback(left_goal)
            else:
                self.x = self.begin[0] + self.radius
                self.vx *= -0.8
        elif self.x + self.radius > self.end[0]:
            right_goal = None
            for g in getattr(self, 'goals', []):
                if getattr(g, 'side', 'right') == 'right' and g.contains_ball(self):
                    right_goal = g
                    break

            if right_goal is not None:
                if callable(self.goal_callback):
                    self.goal_callback(right_goal)
            else:
                self.x = self.end[0] - self.radius
                self.vx *= -0.8

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
                
                # 2. Correção de Posição (Empurrar a bola para fora do player)
                overlap = min_distance - distance
                self.x += math.cos(angle) * (overlap + 0.5)
                self.y += math.sin(angle) * (overlap + 0.5)
                
                # 3. Transferência de Energia Melhorada
                # Calcula velocidade do player para transferência realista
                player_speed = 0
                if hasattr(player, 'vx') and hasattr(player, 'vy'):
                    player_speed = math.hypot(player.vx, player.vy)
                
                # Força base + velocidade do player
                base_kick_power = 2.5
                player_contribution = player_speed * 0.4
                total_force = base_kick_power + player_contribution
                
                # Transfere velocidade na direção da colisão
                self.vx += math.cos(angle) * total_force
                self.vy += math.sin(angle) * total_force
                
                # 4. Limita velocidade máxima da bola
                current_speed = math.hypot(self.vx, self.vy)
                max_ball_speed = 15  # Limite máximo de velocidade
                if current_speed > max_ball_speed:
                    scale = max_ball_speed / current_speed
                    self.vx *= scale
                    self.vy *= scale

    def update(self):
        self.movimentacao()
        self.rect.center = (int(self.x), int(self.y))
        self.draw()