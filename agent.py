from entity import Entity
import config
import pygame
import math
import random
from redeneural import RedeNeural

class Agent(Entity):
    def __init__(self, ID, begin, end, team, screen, color=config.AGENT_COLOR, target=None, players=None):
        largura = end[0] - begin[0]
        altura = end[1] - begin[1]
        self.ID = ID
        self.players = players if players is not None else []
        self.type = "AGENT"
        self.walking = 0
        
        # Ajuste o input_size para 9 elementos conforme sua necessidade
        self.brain = RedeNeural(input_size=config.INPUT_SIZE_LAYER) 

        # Usa a menor dimensão para escalar variáveis de tamanho
        size = min(largura, altura)
        radius = max(4, int(size * config.RADIUS_SCALE))
        
        # Define posição inicial baseada no time
        x = (begin[0] + radius*4) if team == 0 else (end[0] - radius*4) 
        y = begin[1] + altura/2

        super().__init__(x, y, begin, end, screen, radius, color=color, speed=config.BOT_SPEED)
        
        self.target = target  # A bola
        self.team = team 
        
        # Define onde é o gol do INIMIGO (para onde devemos chutar)
        self.attack_goal_x = end[0] if team == 0 else begin[0]
        self.attack_goal_y = begin[1] + altura / 2  # Centro do gol (meio da altura)

        # --- FÍSICA DO BOT ---
        self.vx = 0
        self.vy = 0
        self.acceleration = 0.6
        self.friction = 0.85
        # --- NOVIDADE 1: Variável para saber se é o líder ---
        self.is_leader = False

        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), int(self.radius * 2), int(self.radius * 2))

    def update(self):
        self.walking = 0
        if self.target is None:
            return

        # 1. Constantes para Normalização
        width = self.end[0] - self.begin[0]
        height = self.end[1] - self.begin[1]
        MAX_DIST = math.hypot(width, height)  # Diagonal da quadra

        # 1. Constantes da Quadra
        width = self.end[0] - self.begin[0]
        height = self.end[1] - self.begin[1]
        MAX_DIST = math.hypot(width, height)

        
        my_x_norm = (self.x - self.begin[0]) / width
        my_y_norm = (self.y - self.begin[1]) / height

        

       # -----------------------------------------------------------
        # CÁLCULO DOS INPUTS (O resto continua igual)
        # -----------------------------------------------------------

        # A) BOLA
        dx_bola = self.target.x - self.x
        dy_bola = self.target.y - self.y

        ball_x = (self.target.x - self.begin[0]) / width  
        ball_y = (self.target.y - self.begin[1]) / height  

        dist_bola = math.hypot(dx_bola, dy_bola)
        ang_bola = math.atan2(dy_bola, dx_bola)
        dir_bola = math.atan2(self.target.vy, self.target.vx)

        # B) ADVERSÁRIO
        opponent = None
        for p in self.players:
            if p.ID != self.ID:
                opponent = p
                break
        
        if opponent:
            opponent_x = (opponent.x - self.begin[0]) / width  
            opponent_y = (opponent.y - self.begin[1]) / height  
            dx_adv = opponent.x - self.x
            dy_adv = opponent.y - self.y
            dist_adv = math.hypot(dx_adv, dy_adv)
            ang_adv = math.atan2(dy_adv, dx_adv)
            ovx = getattr(opponent, 'vx', 0)
            ovy = getattr(opponent, 'vy', 0)
            dir_adv = math.atan2(ovy, ovx)
        else:
            dist_adv = 0
            ang_adv = 0
            dir_adv = 0

        # C) GOL INIMIGO
        dx_gol = self.attack_goal_x - self.x
        dy_gol = self.attack_goal_y - self.y
        dist_gol = math.hypot(dx_gol, dy_gol)
        ang_gol = math.atan2(dy_gol, dx_gol)

        gol_x = (self.attack_goal_x - self.begin[0]) / width 
        gol_y = (self.attack_goal_y - self.begin[1]) / height 

        # D) SINAL DE DIREÇÃO
        direction_sign = 1 if self.team == 0 else -1

        # -----------------------------------------------------------
        # LISTA DE INPUTS ATUALIZADA (Total: 11 inputs)
        # -----------------------------------------------------------
        # inputs_atuais = [
        #     my_x_norm,         
        #     my_y_norm,          
        #     dist_bola / MAX_DIST,
        #     ang_bola / math.pi,
        #     dir_bola / math.pi,
        #     dist_adv / MAX_DIST,
        #     ang_adv / math.pi,
        #     dir_adv / math.pi,
        #     dist_gol / MAX_DIST,
        #     ang_gol / math.pi,
        #     direction_sign
        # ]

        inputs_atuais = [
            my_x_norm,         
            my_y_norm,
            ball_x,
            ball_y,
            opponent_x,   
            opponent_y,
            gol_x,   
            gol_y,
            direction_sign   
        ]
        
        # --- REDE NEURAL ---
        # Recebe a decisão da rede
        ax, ay = self.brain.feedForward(inputs_atuais)

        modulo_ax = ax if ax > 0 else -ax
        modulo_ay = ay if ay > 0 else -ay

        
        # Aplica aceleração
        self.vx += ax * self.acceleration
        self.vy += ay * self.acceleration
        
        # Aplica fricção
        self.vx *= self.friction
        self.vy *= self.friction
        
        # Limita velocidade máxima
        current_speed = math.hypot(self.vx, self.vy)
        if current_speed > self.speed:
            scale = self.speed / current_speed
            self.vx *= scale
            self.vy *= scale
        

        oldx = self.x
        oldy = self.y

        # Aplica movimento
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
        
        self.walking = (oldx - self.x if oldx>self.x else self.x - oldx ) +  (oldy - self.y if oldy>self.y else self.y - oldy )

        self.rect.center = (int(self.x), int(self.y))
        self.draw()

def draw(self):
        # Chama o desenho normal (círculo azul)
        super().draw()
        
        # Se for o líder, desenha um anel dourado e o fitness em cima
        if self.is_leader:
            # Anel Dourado
            pygame.draw.circle(self.screen, (255, 215, 0), (int(self.x), int(self.y)), self.radius + 4, 3)