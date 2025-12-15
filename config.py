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
GAME_WIDTH = 1000   # Antigo WINDOW_WIDTH
GAME_HEIGHT = 1000  # Antigo WINDOW_HEIGHT
SIDEBAR_WIDTH = 600 # Largura da barra lateral
WINDOW_WIDTH = GAME_WIDTH + SIDEBAR_WIDTH # Largura Total
WINDOW_HEIGHT = GAME_HEIGHT

# Cores da UI
BG_COLOR = (30, 30, 30)       # Fundo da sidebar
GRAPH_LINE_COLOR = (0, 255, 255) # Ciano
TEXT_COLOR = (220, 220, 220)
NODE_OFF_COLOR = (50, 50, 50)
NODE_ON_COLOR = (0, 255, 0)
WEIGHT_POS_COLOR = (0, 200, 0) # Peso positivo (verde)
WEIGHT_NEG_COLOR = (200, 0, 0) # Peso negativo (vermelho)

# Quantidade de Quadras
limiar = 5
ROWS = 2*limiar
COLUMNS = limiar

# QUADRA
GRASS_COLOR = (80, 180, 80)
LINE_COLOR = (220, 220, 220)
LEFT_WIN_COLOR = (0,255,0)
RIGHT_WIN_COLOR = (255,0,0)
BEST_COLOR = (255, 215, 0)
WIN_SCORE = 10

# ENTITY
RADIUS_SCALE = 0.05

# PLAYER
PLAYER_SPEED = 2.5
PLAYER_COLOR = (0, 0, 255)

# BOT
BOT_SPEED = 2.5
BOT_COLOR = (205, 76, 150)

# AGENT
AGENT_COLOR = (76, 150, 205)
DUAL_AGENT_COLOR = (50, 120, 176)
HIDDEN_SIZE_LAYER = [ 128,16]
INPUT_SIZE_LAYER = 7
# HIDDEN_SIZE_LAYER = [24,8]
# HIDDEN_SIZE_LAYER = [24]s

# GERAL DAS ENTIDADES
DEFAULT_RADIUS = 20
DEFAULT_SPEED = 5

# BALL
BALL_COLOR = (255, 255, 255)
BALL_FRICTION = 0.9
BALL_VARIANCE = 0.2
LIMIT_DIRECTION = 2

