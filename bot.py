from entity import Entity
import config
import pygame
import math

class Bot(Entity):
    def __init__(self, begin, end, team, screen, color=config.BOT_COLOR, target=None):
        largura = end[0] - begin[0]
        altura = end[1] - begin[1]

        radius = config.RADIUS_SCALE * altura 
        # Define posição inicial baseada no time
        x = (begin[0] + radius*4) if team == 0 else (end[0] - radius*4) 
        y = begin[1] + altura/2

        super().__init__(x, y, begin, end, screen, radius, color=color, speed=config.BOT_SPEED)
        
        self.target = target 
        self.team = team # 0 = Esquerda (Ataca Direita), 1 = Direita (Ataca Esquerda)
        
        # Define onde é o gol do INIMIGO (para onde devemos chutar)
        # Se sou time 0 (esquerda), chuto para o final da tela (direita)
        self.attack_goal_x = end[0] if team == 0 else begin[0]

        self.rect = pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

    def update(self):
        if self.target is None:
            return

        # Posição da bola
        bx, by = self.target.x, self.target.y
        
        # Distância que o bot deve manter atrás da bola para preparar o chute
        offset_dist = self.radius * 2.5 

        # Lógica de Direção do Chute
        # Se sou time 0, quero chutar para direita (+1 no x), senão para esquerda (-1 no x)
        direction_sign = 1 if self.team == 0 else -1

        # --- ESTRATÉGIA ---
        
        # 1. Calcular o "Ponto Ideal" (Sweet Spot)
        # O ponto ideal é ligeiramente atrás da bola, alinhado com o gol inimigo.
        # Isso garante que quando o bot avançar, ele empurre a bola pro gol.
        ideal_x = bx - (offset_dist * direction_sign)
        ideal_y = by

        # Verifica se a bola está "atrás" do bot (perigo de gol contra)
        # Se sou time 0 e a bola está à minha esquerda (menor que meu x), estou na frente dela.
        is_ball_behind = (self.team == 0 and bx < self.x) or (self.team == 1 and bx > self.x)

        dx, dy = 0, 0
        
        # Distancia entre bot e o ponto ideal
        dist_to_ideal = math.hypot(self.x - ideal_x, self.y - ideal_y)
        dist_to_ball = math.hypot(self.x - bx, self.y - by)

        # SELEÇÃO DE ALVO:
        # Se eu já estou bem posicionado (perto do ponto ideal) OU a bola está na minha frente:
        # VOU DIRETO NA BOLA (Modo Ataque)
        if dist_to_ideal < self.radius or (not is_ball_behind and abs(self.y - by) < self.radius):
            target_x, target_y = bx, by
        else:
            # Caso contrário, vou para o PONTO IDEAL primeiro (Modo Posicionamento)
            target_x, target_y = ideal_x, ideal_y
            
            # Pequeno ajuste: Se a bola está muito perto da parede superior ou inferior,
            # evitamos ficar presos na parede tentando dar a volta.
            if by < self.begin[1] + self.radius * 3: # Bola muito no topo
                target_y = by + self.radius * 2
            elif by > self.end[1] - self.radius * 3: # Bola muito no chão
                target_y = by - self.radius * 2

        # --- MOVIMENTAÇÃO ---
        
        # Define dx (Movimento horizontal)
        # Usamos uma zona morta (tolerance) de 2 pixels para evitar tremedeira
        if self.x < target_x - 2:
            dx = 1
        elif self.x > target_x + 2:
            dx = -1
            
        # Define dy (Movimento vertical)
        if self.y < target_y - 2:
            dy = 1
        elif self.y > target_y + 2:
            dy = -1

        self.move(dx, dy)
        self.rect.center = (int(self.x), int(self.y))
        self.draw()