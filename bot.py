from entity import Entity
import config
import pygame
import math
import random # Importante para dar uma variada se travar muito

class Bot(Entity):
    def __init__(self, ID, begin, end, team, screen, color=config.BOT_COLOR, target=None):
        largura = end[0] - begin[0]
        altura = end[1] - begin[1]
        self.ID = ID
        self.type = "BOT"

        # Usa a menor dimensão (largura/altura) para escalar variáveis de tamanho
        size = min(largura, altura)
        radius = max(4, int(size * config.RADIUS_SCALE))
        # Define posição inicial baseada no time
        x = (begin[0] + radius*4) if team == 0 else (end[0] - radius*4) 
        y = begin[1] + altura/2

        super().__init__(x, y, begin, end, screen, radius, color=color, speed=config.BOT_SPEED)
        
        self.target = target 
        self.team = team 
        
        self.attack_goal_x = end[0] if team == 0 else begin[0]

        # --- FÍSICA DO BOT ---
        self.vx = 0
        self.vy = 0
        self.acceleration = 0.6
        self.friction = 0.85

        # --- NOVIDADE: Timer para detectar se travou ---
        self.stuck_timer = 0 

        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), int(self.radius * 2), int(self.radius * 2))

    def update(self):
        if self.target is None:
            return

        # Posição da bola
        bx, by = self.target.x, self.target.y
        
        # Distância que o bot deve manter atrás da bola para preparar o chute
        offset_dist = self.radius * 2.5 

        # Lógica de Direção do Chute
        direction_sign = 1 if self.team == 0 else -1

        # --- ESTRATÉGIA ---
        
        ideal_x = bx - (offset_dist * direction_sign)
        ideal_y = by

        is_ball_behind = (self.team == 0 and bx < self.x) or (self.team == 1 and bx > self.x)

        dist_to_ideal = math.hypot(self.x - ideal_x, self.y - ideal_y)
        
        # Lógica Padrão (que você já gosta)
        if dist_to_ideal < self.radius or (not is_ball_behind and abs(self.y - by) < self.radius):
            target_x, target_y = bx, by
        else:
            target_x, target_y = ideal_x, ideal_y
            
            # Evita ficar preso nas paredes de cima/baixo
            if by < self.begin[1] + self.radius * 3: 
                target_y = by + self.radius * 2
            elif by > self.end[1] - self.radius * 3: 
                target_y = by - self.radius * 2

        # --- CORREÇÃO DE "BOT PARADÃO" ---
        
        # Verifica velocidade atual
        current_speed = math.hypot(self.vx, self.vy)
        
        # Se estiver muito lento (quase parado) E longe da bola
        dist_to_ball = math.hypot(self.x - bx, self.y - by)
        
        if current_speed < 0.5 and dist_to_ball > self.radius + 5:
            self.stuck_timer += 1
        else:
            self.stuck_timer = 0
            
        # Se ficou parado por mais de 60 frames (1 segundo aprox)
        if self.stuck_timer > 60:
            # FORÇA BRUTA: Ignora estratégia e vai na bola para destravar o jogo
            target_x, target_y = bx, by
            
            # Adiciona um pequeno "jitter" aleatório para sair de alinhamentos perfeitos na parede
            target_x += random.randint(-10, 10)
            target_y += random.randint(-10, 10)

        # --- MOVIMENTAÇÃO COM FÍSICA ---
        
        ax, ay = 0, 0
        
        # Tolerância reduzida de 2 para 1 para ele tentar ser mais preciso antes de parar
        if self.x < target_x - 1:
            ax = 1
        elif self.x > target_x + 1:
            ax = -1
            
        if self.y < target_y - 1:
            ay = 1
        elif self.y > target_y + 1:
            ay = -1
        
        self.vx += ax * self.acceleration
        self.vy += ay * self.acceleration
        
        self.vx *= self.friction
        self.vy *= self.friction
        
        current_speed = math.hypot(self.vx, self.vy)
        if current_speed > self.speed:
            scale = self.speed / current_speed
            self.vx *= scale
            self.vy *= scale
        
        self.x += self.vx
        self.y += self.vy
        
        # Colisão com Paredes
        if self.x + self.radius > self.end[0]:
            self.x = self.end[0] - self.radius
            self.vx *= -0.5
        elif self.x - self.radius < self.begin[0]:
            self.x = self.begin[0] + self.radius
            self.vx *= -0.5

        if self.y + self.radius > self.end[1]:
            self.y = self.end[1] - self.radius
            self.vy *= -0.5
        elif self.y - self.radius < self.begin[1]:
            self.y = self.begin[1] + self.radius
            self.vy *= -0.5
        
        self.rect.center = (int(self.x), int(self.y))
        self.draw()