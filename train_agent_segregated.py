import pygame
import pickle
import os
import math
from datetime import datetime
import numpy as np

# Importa as classes do seu projeto
from quadra import Quadra
from redeneural import RedeNeural
from sidebar import Sidebar 
import config

# --- CONFIGURAÇÕES DE TREINO ---
TIME_PER_GENERATION = 10 # Tempo da geração
POPULATION_SIZE = config.ROWS * config.COLUMNS * 2 
MUTATION_RATE = 0.15      
MUTATION_SCALE = 0.25     
ELITISM_PERCENT = 0.1     

def save_best_model(brain, prefix):
    """Salva o modelo com prefixo (LEFT ou RIGHT)"""
    if not os.path.exists("models"):
        os.makedirs("models")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"models/best_{prefix}_{timestamp}.pkl"
    
    with open(filename, 'wb') as f:
        pickle.dump(brain, f)
    
    print(f"✅ Modelo {prefix} salvo: {filename}")

def evolve_list(agent_list, target_size):
    """
    Recebe uma lista de AGENTES (ex: só os da esquerda),
    retorna uma lista de CÉREBROS (RedeNeural) para a próxima geração.
    """
    # 1. Ordena pelo fitness (do maior para o menor)
    agent_list.sort(key=lambda x: x.fitness, reverse=True)
    
    new_brains = []
    
    # 2. Elitismo (Mantém os Reis)
    num_elites = int(target_size * ELITISM_PERCENT)
    if num_elites < 1: num_elites = 1 # Garante pelo menos 1
    
    for i in range(num_elites):
        if i < len(agent_list):
            new_brains.append(agent_list[i].brain.copy())
            
    # 3. Reprodução (Preenche o resto)
    remaining = target_size - len(new_brains)
    
    # Define os pais (Top 50%)
    parent_pool = agent_list[:int(len(agent_list)/2)]
    if not parent_pool: parent_pool = agent_list # Fallback
    
    for _ in range(remaining):
        parent = np.random.choice(parent_pool)
        child_brain = parent.brain.copy()
        child_brain.mutate(mutation_rate=MUTATION_RATE, mutation_scale=MUTATION_SCALE)
        new_brains.append(child_brain)
        
    return new_brains, agent_list[0].fitness

def main():
    pygame.init()

    # Configura Tela e Sidebar (FORA DO LOOP)
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    sidebar = Sidebar(screen, config.GAME_WIDTH, config.SIDEBAR_WIDTH, config.WINDOW_HEIGHT)
    pygame.display.set_caption("Neural HaxBall - Evolution (Left vs Right) - "+str(config.HIDDEN_SIZE_LAYER))

    clock = pygame.time.Clock()

    # --- INICIALIZAÇÃO SEGREGADA ---
    # Divide a população total por 2
    pop_size_side = int(POPULATION_SIZE / 2)
    
    # Cria populações virgens iniciais
    pop_left = [RedeNeural(input_size=9) for _ in range(pop_size_side)]
    pop_right = [RedeNeural(input_size=9) for _ in range(pop_size_side)]
    
    generation = 1
    
    # Carrega histórico visual se existir
    if len(sidebar.fitness_history) > 0:
        generation = len(sidebar.fitness_history) + 1
        print(f"Retomando histórico da Geração {generation}...")
    
    running_program = True
    while running_program:
        
        # --- PREPARAÇÃO DA GERAÇÃO ---
        quadras = []
        
        # Listas para separar os agentes desta rodada
        agents_left_active = []
        agents_right_active = []

        cell_width = config.GAME_WIDTH / config.COLUMNS
        cell_height = config.WINDOW_HEIGHT / config.ROWS

        # Indices para distribuir os cérebros
        idx_L = 0
        idx_R = 0
        
        for y in range(config.ROWS): 
            for x in range(config.COLUMNS):
                cx = x * cell_width
                cy = y * cell_height
                
                # Cria quadra Agent vs Agent
                q = Quadra(screen, (cx, cy), (cx + cell_width, cy + cell_height), ['agent', 'agent'])
                quadras.append(q)
                
                # Injeta cérebros
                for agent in q.players:
                    if agent.type == 'AGENT':
                        agent.fitness = 0 # Reinicia fitness
                        
                        if agent.team == 0: # Time Esquerda
                            if idx_L < len(pop_left):
                                agent.brain = pop_left[idx_L]
                                agents_left_active.append(agent)
                                idx_L += 1
                        else: # Time Direita
                            if idx_R < len(pop_right):
                                agent.brain = pop_right[idx_R]
                                agents_right_active.append(agent)
                                idx_R += 1

        # --- LOOP DA PARTIDA ---
        start_time = pygame.time.get_ticks()
        running_generation = True
        
        print(f"--- Geração {generation} (Segregada) ---")

        while running_generation:
            clock.tick(60) 

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_program = False
                    running_generation = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        # Salva o melhor de cada lado ao sair
                        if agents_left_active:
                            best_L = max(agents_left_active, key=lambda a: a.fitness)
                            save_best_model(best_L.brain, "LEFT")
                        if agents_right_active:
                            best_R = max(agents_right_active, key=lambda a: a.fitness)
                            save_best_model(best_R.brain, "RIGHT")
                            
                        running_program = False
                        running_generation = False

            elapsed_seconds = (pygame.time.get_ticks() - start_time) / 1000
            if elapsed_seconds >= TIME_PER_GENERATION:
                running_generation = False

            screen.fill((0, 0, 0))
            ended = True
            
            # --- UPDATE E LÓGICA DO JOGO ---
            for q in quadras:
                if q.status == 0:
                    ended = False
                q.update()
                
                # --- SUAS MÉTRICAS ORIGINAIS DE FITNESS ---
                for agent in q.players:
                    if agent.type != 'AGENT' or q.status != 0:
                        continue
                    
                    # 1. Territorial (Se a bola está no campo de ataque)
                    # Time 0 ataca para a direita (> largura/2)
                    # Time 1 ataca para a esquerda (< largura/2)
                    
                    # Lógica original adaptada para identificar ataque independente do lado
                    is_attacking = False
                    if agent.team == 0 and (q.ball.x - q.begin[0] > q.largura/2):
                        is_attacking = True
                    elif agent.team == 1 and (q.ball.x - q.begin[0] < q.largura/2):
                        is_attacking = True
                        
                    if is_attacking:
                        agent.fitness += 0.01
                    else:
                        agent.fitness -= 0.01

                    # 2. Gol Marcado / Sofrido (Durante a partida)
                    if q.pontuou:
                        # A logica do seu codigo original usava 'my_score' e 'enemy_score' aqui
                        my_score = q.score[agent.team]
                        enemy_score = q.score[1 - agent.team]
                        
                        agent.fitness += my_score * 30
                        agent.fitness -= enemy_score * 15
                        # Nota: q.pontuou precisa ser resetado na classe Quadra ou aqui com cuidado
                        # No seu código original ele resetava a flag 'q.ponutou = False' dentro do loop de agents
                        # Vou assumir que o primeiro agente reseta
                        if(q.players[-1] == agent):
                            q.pontuou = False 

                    # 3. Penalidade Temporal
                    agent.fitness -= 0.001

                    # 4. Penalidade por ficar parado (Walking)
                    if agent.walking == 0:
                        agent.fitness -= 0.1

            if ended:
                running_generation = False

            # --- DESTAQUES VISUAIS (HIGHLIGHTS) ---
            best_left_now = None
            best_right_now = None

            # Encontra o melhor da Esquerda
            if agents_left_active:
                best_left_now = max(agents_left_active, key=lambda a: a.fitness)
                # Retângulo Verde (LEFT_WIN_COLOR)
                pygame.draw.rect(screen, config.LEFT_WIN_COLOR, 
                                 [best_left_now.begin[0], best_left_now.begin[1], 
                                  best_left_now.end[0] - best_left_now.begin[0], 
                                  best_left_now.end[1] - best_left_now.begin[1]], 4)

            # Encontra o melhor da Direita
            if agents_right_active:
                best_right_now = max(agents_right_active, key=lambda a: a.fitness)
                # Retângulo Vermelho (RIGHT_WIN_COLOR)
                pygame.draw.rect(screen, config.RIGHT_WIN_COLOR, 
                                 [best_right_now.begin[0], best_right_now.begin[1], 
                                  best_right_now.end[0] - best_right_now.begin[0], 
                                  best_right_now.end[1] - best_right_now.begin[1]], 4)

            # --- ATUALIZA SIDEBAR ---
            # Escolhe o melhor GLOBAL para exibir na sidebar (o "Craque da Partida")
            best_global = None
            if best_left_now and best_right_now:
                best_global = best_left_now if best_left_now.fitness > best_right_now.fitness else best_right_now
            elif best_left_now: best_global = best_left_now
            elif best_right_now: best_global = best_right_now

            sidebar.draw(generation, best_global, TIME_PER_GENERATION - elapsed_seconds)
            
            pygame.display.flip()

        if not running_program:
            break

        # --- FIM DA GERAÇÃO: SCORE FINAL ---
        
        # Aplica a pontuação final (Vitória/Derrota) como no seu código original
        # Isso precisa ser feito para todos os agentes antes de ordenar
        all_active = agents_left_active + agents_right_active
        
        # Para facilitar, percorremos as quadras novamente
        for q in quadras:
            for agent in q.players:
                if agent.type == 'AGENT':
                    my_score = q.score[agent.team]
                    enemy_score = q.score[1 - agent.team]
                    
                    # Seus valores originais de recompensa final
                    agent.fitness += my_score * 100
                    agent.fitness -= enemy_score * 50

        # --- EVOLUÇÃO SEGREGADA ---
        
        # 1. Evolui time da Esquerda
        pop_left, fit_L = evolve_list(agents_left_active, pop_size_side)
        
        # 2. Evolui time da Direita
        pop_right, fit_R = evolve_list(agents_right_active, pop_size_side)
        
        # Logging e Gráfico
        best_of_gen = max(fit_L, fit_R)
        print(f"Gen {generation} | Top Left: {fit_L:.2f} | Top Right: {fit_R:.2f}")
        
        sidebar.update_history(best_of_gen)
        
        generation += 1

    pygame.quit()

if __name__ == "__main__":
    main()