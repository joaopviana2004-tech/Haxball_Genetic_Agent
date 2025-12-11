# ========================
# CONFIGURAÇÕES DO JOGO
# ========================

import random


def Variate_grass_color():
    # Grande variação, afeta Vermelho e Azul
    variate_R_B = random.randint(-40, 40)
    # Pequena variação, afeta o Verde
    variate_G = random.randint(-15, 15)
    
    # 1. Escolhe um "temperamento" de cor principal para a quadra
    color_type = random.choice(['GREEN', 'YELLOW'])
    
    if color_type == 'GREEN':
        # Tons de grama viva: G alto, R e B baixos
        R_base = 80
        G_base = 180
        B_base = 80
        
    elif color_type == 'YELLOW':
        # Tons amarelados/secos: R e G altos, B baixo
        R_base = 220
        G_base = 180
        B_base = 80

    # Aplica a variação aleatória à cor base
    final_R = R_base + variate_R_B
    final_G = G_base + variate_G
    final_B = B_base + variate_R_B

    # Garante que os valores fiquem entre 0 e 255 (necessário para Pygame/RGB)
    final_R = max(0, min(255, final_R))
    final_G = max(0, min(255, final_G))
    final_B = max(0, min(255, final_B))
    
    return (final_R, final_G, final_B)

# JANELA
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 1000
FPS = 60

# Quantidade de Quadras
ROWS = 2
COLUMNS = 1

# QUADRA
GRASS_COLOR = (80, 180, 80)
LINE_COLOR = (255, 255, 255)

# ENTITY
RADIUS_SCALE = 0.1

# PLAYER
PLAYER_SPEED = 5
PLAYER_COLOR = (0, 0, 255)

# BOT
BOT_SPEED = 5
BOT_COLOR = (205, 76, 150)

# GERAL DAS ENTIDADES
DEFAULT_RADIUS = 20
DEFAULT_SPEED = 5

# BALL
BALL_COLOR = (255, 255, 255)
BALL_FRICTION = 0.98
BALL_VARIANCE = 0.2
LIMIT_DIRECTION = 2

