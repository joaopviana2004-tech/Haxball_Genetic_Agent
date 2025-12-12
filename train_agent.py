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
TIME_PER_GENERATION = 10 # Segundos por geração (aumente se eles ficarem espertos)
POPULATION_SIZE = config.ROWS * config.COLUMNS * 2 # 2 Agentes por quadra
MUTATION_RATE = 0.15      # Chance de mutação
MUTATION_SCALE = 0.25     # Intensidade da mutação
ELITISM_PERCENT = 0.1     # Top 10% passa sem mutação (os reis da geração)

def save_best_model(brain):
    """Salva o melhor modelo em um arquivo .pkl com data/hora"""
    if not os.path.exists("models"):
        os.makedirs("models")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"models/best_model_{timestamp}.pkl"
    
    with open(filename, 'wb') as f:
        pickle.dump(brain, f)
    
    print(f"✅ Modelo salvo com sucesso: {filename}")

def main():
    pygame.init()

    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    sidebar = Sidebar(screen, config.GAME_WIDTH, config.SIDEBAR_WIDTH, config.WINDOW_HEIGHT)
    pygame.display.set_caption("Neural HaxBall - Training Lab")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)


    # 1. Inicializa a primeira população de cérebros (Redes Neurais)
    population_brains = [RedeNeural(input_size=9) for _ in range(POPULATION_SIZE)]
    
    generation = 1
    
    # Loop principal de gerações
    running_program = True
    while running_program:
        
        # --- PREPARAÇÃO DA GERAÇÃO ---
        quadras = []
        all_agents = []

        # Recria o ambiente (Quadras)
        cell_width = config.GAME_WIDTH / config.COLUMNS
        cell_height = config.WINDOW_HEIGHT / config.ROWS

        agent_index = 0
        
        for y in range(config.ROWS): 
            for x in range(config.COLUMNS):
                cx = x * cell_width
                cy = y * cell_height
                # Cria quadra com 2 agentes (1v1)
                # 'agent' vs 'agent' para treinarem entre si
                q = Quadra(screen, (cx, cy), (cx + cell_width, cy + cell_height), ['agent', 'bot'])
                # q = Quadra(screen, (cx, cy), (cx + cell_width, cy + cell_height), ['agent', 'agent'])
                quadras.append(q)
                
                # Injeta os cérebros da população nos agentes criados
                for agent in q.players:
                    if agent.type == 'AGENT':
                        agent.brain = population_brains[agent_index]
                        agent.fitness = 0 # Reinicia pontuação
                        all_agents.append(agent)
                        agent_index += 1

        # --- LOOP DA PARTIDA (SIMULAÇÃO) ---
        start_time = pygame.time.get_ticks()
        running_generation = True
        
        print(f"--- Geração {generation} Iniciada ---")

        while running_generation:
            # Controle de FPS
            clock.tick(60) # Pode aumentar para acelerar o treino (ex: 999) se o PC aguentar

            # Eventos (Fechar ou Salvar)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_program = False
                    running_generation = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        # Salva o melhor da geração atual antes de sair
                        best_agent = max(all_agents, key=lambda a: a.fitness)
                        save_best_model(best_agent.brain)
                        running_program = False
                        running_generation = False

            # Lógica de Tempo da Geração
            elapsed_seconds = (pygame.time.get_ticks() - start_time) / 1000
            if elapsed_seconds >= TIME_PER_GENERATION:
                running_generation = False

            # Renderização e Updates
            screen.fill((0, 0, 0))
            ended = True
            
            # Atualiza todas as quadras
            for q in quadras:
                if(q.status == 0):
                    ended = False
                q.update()
                
                # --- CÁLCULO DE FITNESS (A MÁGICA ACONTECE AQUI) ---
                # Precisamos premiar bons comportamentos
                # dist_max = math.hypot(q.largura, q.altura)


                for agent in q.players:
                    if(agent.type != 'AGENT' or q.status != 0):
                        continue
                    # 1. Recompensa por tocar na bola
                    # dist_ball = math.hypot(agent.x - q.ball.x, agent.y - q.ball.y)
                    # # Se tocar na bola (distância < soma dos raios)
                    # if dist_ball < (agent.radius + q.ball.radius + 2):
                    #     agent.fitness += 10.0 # Ganha pontos por tocar na bola
                    
                    # 2. Recompensa por estar PERTO da bola (shaping reward)
                    # Ajuda no início quando eles são burros
                    # if dist_ball < dist_max:
                    #     agent.fitness += (1 - (dist_ball / dist_max)) * 0.05

                    # 3. Penalidade por GOL SOFRIDO / Recompensa por GOL FEITO
                    # A classe Quadra já atualiza o score. Vamos checar o placar.
                    # agent.team 0 (esquerda) vs agent.team 1 (direita)
                    
                    # Pontos do Time do Agente
                    my_score = q.score[agent.team]
                    # Pontos do Inimigo
                    enemy_score = q.score[1 - agent.team]

                    if(q.ball.x - q.begin[0] > q.largura/2):
                        agent.fitness += 0.01
                        # pygame.draw.rect(screen, config.RIGHT_WIN_COLOR, [agent.begin[0], agent.begin[1], agent.end[0] - agent.begin[0], agent.end[1] - agent.begin[1]], 5)
                    else:
                        agent.fitness -= 0.01
                        # pygame.draw.rect(screen, config.LEFT_WIN_COLOR, [agent.begin[0], agent.begin[1], agent.end[0] - agent.begin[0], agent.end[1] - agent.begin[1]], 5)

                    if(q.pontuou):
                        agent.fitness += my_score * 30
                        agent.fitness -= enemy_score * 15
                        q.ponutou = False


                    # Nota: Isso é acumulativo, então precisamos cuidar para não somar 
                    # o mesmo gol todo frame. Mas como o score reseta na quadra só no fim...
                    # Simplificação: Usamos o delta de gols no final ou um valor alto aqui.
                    # Vamos adicionar valor base fixo por gol marcado:
                    agent.fitness -= 0.001

                    if(agent.walking == 0):
                        agent.fitness -= 0.1

            if(ended):
                    running_generation = False

            if len(all_agents) > 0:
                # Encontra o agente com maior fitness na lista inteira
                best_agent_now = max(all_agents, key=lambda a: a.fitness)
                
                # Atualiza o status de todos
                for agent in all_agents:
                    if agent == best_agent_now:
                        pygame.draw.rect(screen, config.BEST_COLOR, [agent.begin[0], agent.begin[1], agent.end[0] - agent.begin[0], agent.end[1] - agent.begin[1]], 5)

            # --- ATUALIZA SIDEBAR ---
            best_agent_now = None
            if len(all_agents) > 0:
                best_agent_now = max(all_agents, key=lambda a: a.fitness)
                
                # Highlight no campo (Quadrado Verde)
                pygame.draw.rect(screen, (0, 255, 0), 
                                 [best_agent_now.begin[0], best_agent_now.begin[1], 
                                  best_agent_now.end[0] - best_agent_now.begin[0], 
                                  best_agent_now.end[1] - best_agent_now.begin[1]], 2)

            best_now = max(all_agents, key=lambda a: a.fitness) if all_agents else None
            sidebar.draw(generation, best_now, TIME_PER_GENERATION - elapsed_seconds)
            
            pygame.display.flip()
        if not running_program:
            break

        # --- EVOLUÇÃO (ALGORITMO GENÉTICO) ---
        
        # 1. Ordena agentes pelo fitness (do maior para o menor)
        for q in quadras:
            my_score = q.score[agent.team]
            enemy_score = q.score[1 - agent.team]

            agent.fitness += my_score * 100
            agent.fitness -= enemy_score * 50

        all_agents.sort(key=lambda x: x.fitness, reverse=True)
        
        print(f"Melhor Fitness Geração {generation}: {all_agents[0].fitness:.2f}")
        sidebar.update_history(all_agents[0].fitness)

        # 2. Elitismo: Mantém os melhores inalterados
        num_elites = int(POPULATION_SIZE * ELITISM_PERCENT)
        new_population = []
        
        # Salva os 'Elites' (Copia exata)
        for i in range(num_elites):
            new_population.append(all_agents[i].brain.copy())
            
        # 3. Cruzamento e Mutação para preencher o resto
        # Vamos encher o resto da população usando mutações dos melhores
        remaining_slots = POPULATION_SIZE - num_elites
        
        for _ in range(remaining_slots):
            # Escolhe um pai aleatório entre os TOP 50% (para garantir qualidade)
            parent_pool = all_agents[:int(POPULATION_SIZE/2)]
            parent = random_choice = np.random.choice(parent_pool)
            
            # Clona o cérebro
            child_brain = parent.brain.copy()
            
            # Aplica Mutação
            child_brain.mutate(mutation_rate=MUTATION_RATE, mutation_scale=MUTATION_SCALE)
            
            new_population.append(child_brain)

        # Atualiza a população global para a próxima geração
        population_brains = new_population
        generation += 1

    pygame.quit()

if __name__ == "__main__":
    main()