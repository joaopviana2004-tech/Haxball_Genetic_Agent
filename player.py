import pygame
import math
from entity import Entity
import config

class Player(Entity):
    def __init__(self, begin, end, team, screen, color=config.PLAYER_COLOR):
        largura = end[0] - begin[0]
        altura = end[1] - begin[1]

        # Usa a menor dimensão (largura/altura) para escalar variáveis de tamanho
        size = min(largura, altura)
        radius = max(4, int(size * config.RADIUS_SCALE))
        # Define posição inicial baseada no time
        x = (begin[0] + radius*4) if team == 0 else (end[0] - radius*4) 
        y = begin[1] + altura/2

        super().__init__(x, y, begin, end, screen, radius, color=color, speed=config.PLAYER_SPEED)

        # --- FÍSICA AVANÇADA ---
        self.vx = 0
        self.vy = 0
        self.acceleration = 0.8 # O quão rápido ele atinge a velocidade máxima
        self.friction = 0.85    # "Grip" no chão (quanto menor, mais sabão)
        
        # Atualiza o rect para colisões
        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), int(self.radius*2), int(self.radius*2))

    def get_input(self):
        keys = pygame.key.get_pressed()
        input_x = 0
        input_y = 0

        if keys[pygame.K_w]:
            input_y -= 1
        if keys[pygame.K_s]:
            input_y += 1
        if keys[pygame.K_a]:
            input_x -= 1
        if keys[pygame.K_d]:
            input_x += 1
            
        # --- NORMALIZAÇÃO DIAGONAL ---
        # Impede que andar na diagonal seja mais rápido que andar reto
        if input_x != 0 and input_y != 0:
            input_x *= 0.7071 # 1 / sqrt(2)
            input_y *= 0.7071
            
        return input_x, input_y
    
    def update(self):
        # 1. Captura Input
        dx, dy = self.get_input()

        # 2. Aplica Aceleração (Física Newtoniana)
        # Em vez de definir a velocidade direta, adicionamos ao vetor atual
        self.vx += dx * self.acceleration
        self.vy += dy * self.acceleration

        # 3. Aplica Fricção (Desaceleração natural)
        self.vx *= self.friction
        self.vy *= self.friction

        # 4. Limita a Velocidade Máxima
        # Se passar do limite configurado, cortamos o excesso
        current_speed = math.hypot(self.vx, self.vy)
        if current_speed > self.speed:
            scale = self.speed / current_speed
            self.vx *= scale
            self.vy *= scale

        # Evita movimento microscópico (jitter) quando quase parado
        if abs(self.vx) < 0.01: self.vx = 0
        if abs(self.vy) < 0.01: self.vy = 0

        # 5. Move e Checa Paredes
        # Usamos uma lógica manual aqui para não depender do 'move' da Entity 
        # que multiplica por self.speed novamente
        self.x += self.vx
        self.y += self.vy

        # Colisão com Paredes (Copia a lógica do Entity mas adaptada para velocidade)
        if self.x + self.radius > self.end[0]:
            self.x = self.end[0] - self.radius
            self.vx *= -0.5  # Rebote com amortecimento
        elif self.x - self.radius < self.begin[0]:
            self.x = self.begin[0] + self.radius
            self.vx *= -0.5  # Rebote com amortecimento

        if self.y + self.radius > self.end[1]:
            self.y = self.end[1] - self.radius
            self.vy *= -0.5  # Rebote com amortecimento
        elif self.y - self.radius < self.begin[1]:
            self.y = self.begin[1] + self.radius
            self.vy *= -0.5  # Rebote com amortecimento

        # 6. Atualiza Rect e Desenha
        self.rect.center = (int(self.x), int(self.y))
        
        # Dica visual: Se apertar ESPAÇO (Chute), desenha um contorno branco
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
             pygame.draw.circle(self.screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius + 3, 2)

        self.draw()
