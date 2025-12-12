import pygame
import pickle
import os
import math
import random # Necessário para embaralhar oponentes
from datetime import datetime
import numpy as np

# Importa as classes do seu projeto
from quadra import Quadra
from redeneural import RedeNeural
from sidebar import Sidebar 
import config

# --- CONFIGURAÇÕES DE TREINO ROBUSTO ---
TIME_PER_MATCH = 10       # Tempo de cada partida (em segundos)
MATCHES_PER_AGENT = 3     # Quantos oponentes diferentes cada um enfrenta
POPULATION_SIZE = config.ROWS * config.COLUMNS * 2 

# Configurações Genéticas
MUTATION_RATE = 0.15      
MUTATION_SCALE = 0.25     
ELITISM_PERCENT = 0.1     

# --- CLASSE AUXILIAR PARA O TREINO ---
class Candidate:
    """
    Representa um 'atleta' no campeonato genético.
    Segura o cérebro e a pontuação acumulada de várias partidas.
    """
    def __init__(self, brain):
        self.brain = brain
        self.fitness = 0 # Fitness ACUMULADO das 3 partidas

def save_best_model(brain, prefix):
    if not os.path.exists("models"):
        os.makedirs("models")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"models/best_{prefix}_{timestamp}.pkl"
    with open(filename, 'wb') as f:
        pickle.dump(brain, f)
    print(f"✅ Modelo {prefix} salvo: {filename}")

def evolve_candidates(candidate_list, target_size):
    """
    Evolui uma lista de Candidatos.
    Retorna uma NOVA lista de Candidatos (fitness zerado) com cérebros evoluídos.
    """
    # 1. Ordena pelo fitness ACUMULADO
    candidate_list.sort(key=lambda x: x.fitness, reverse=True)
    
    new_candidates = []
    
    # 2. Elitismo
    num_elites = int(target_size * ELITISM_PERCENT)
    if num_elites < 1: num_elites = 1
    
    for i in range(num_elites):
        if i < len(candidate_list):
            # O elite passa com o mesmo cérebro, mas cria um novo Candidate (fit=0)
            new_candidates.append(Candidate(candidate_list[i].brain.copy()))
            
    # 3. Reprodução
    remaining = target_size - len(new_candidates)
    parent_pool = candidate_list[:int(len(candidate_list)/2)]
    if not parent_pool: parent_pool = candidate_list
    
    for _ in range(remaining):
        parent = np.random.choice(parent_pool)
        child_brain = parent.brain.copy()
        child_brain.mutate(mutation_rate=MUTATION_RATE, mutation_scale=MUTATION_SCALE)
        new_candidates.append(Candidate(child_brain))
        
    return new_candidates, candidate_list[0].fitness

def main():
    pygame.init()

    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    sidebar = Sidebar(screen, config.GAME_WIDTH, config.SIDEBAR_WIDTH, config.WINDOW_HEIGHT)
    pygame.display.set_caption(f"Neural HaxBall - Robust Training ({MATCHES_PER_AGENT} rounds)")

    clock = pygame.time.Clock()

    pop_size_side = int(POPULATION_SIZE / 2)
    
    # Inicializa Populações de Candidatos (Wrapper que segura o cérebro e o fitness global)
    pop_left = [Candidate(RedeNeural(input_size=9)) for _ in range(pop_size_side)]
    pop_right = [Candidate(RedeNeural(input_size=9)) for _ in range(pop_size_side)]
    
    generation = 1
    if len(sidebar.fitness_history) > 0:
        generation = len(sidebar.fitness_history) + 1
        print(f"Retomando da Geração {generation}...")
    
    running_program = True
    
    # --- LOOP DE GERAÇÕES ---
    while running_program:
        
        # Reinicia o fitness acumulado de todos para a nova geração
        for c in pop_left: c.fitness = 0
        for c in pop_right: c.fitness = 0
        
        print(f"--- Geração {generation} ---")
        
        # Para garantir pareamentos aleatórios, criamos índices
        indices_left = list(range(len(pop_left)))
        indices_right = list(range(len(pop_right)))

        # --- LOOP DE RODADAS (MATCHES) ---
        # Cada agente vai jogar 'MATCHES_PER_AGENT' vezes
        for match_round in range(1, MATCHES_PER_AGENT + 1):
            
            # Embaralha os oponentes da direita para criar confrontos novos
            random.shuffle(indices_right)
            
            # Prepara as Quadras
            quadras = []
            
            # Mapas para saber qual Agente na tela pertence a qual Candidato (para somar pontos dps)
            # Chave: Objeto Agent -> Valor: Objeto Candidate
            agent_to_candidate_map = {}
            
            # Variáveis visuais da rodada
            active_agents_left = []
            active_agents_right = []
            
            cell_width = config.GAME_WIDTH / config.COLUMNS
            cell_height = config.WINDOW_HEIGHT / config.ROWS

            # Distribuição nas Quadras
            # O Agente Esquerda[i] joga contra Direita[embaralhado[i]]
            for i in range(len(pop_left)):
                # Calcula posição da quadra (grid)
                row = i // config.COLUMNS
                col = i % config.COLUMNS
                
                cx = col * cell_width
                cy = row * cell_height
                
                q = Quadra(screen, (cx, cy), (cx + cell_width, cy + cell_height), ['agent', 'agent'])
                quadras.append(q)
                
                # Configura os Agentes
                cand_L = pop_left[indices_left[i]]
                cand_R = pop_right[indices_right[i]]
                
                for agent in q.players:
                    if agent.type == 'AGENT':
                        agent.fitness = 0 # Fitness DA PARTIDA (temporário)
                        
                        if agent.team == 0: # Esquerda
                            agent.brain = cand_L.brain
                            agent_to_candidate_map[agent] = cand_L
                            active_agents_left.append(agent)
                        else: # Direita
                            agent.brain = cand_R.brain
                            agent_to_candidate_map[agent] = cand_R
                            active_agents_right.append(agent)

            # --- LOOP DO JOGO (10 segundos) ---
            start_time = pygame.time.get_ticks()
            running_match = True
            
            print(f" > Rodada {match_round}/{MATCHES_PER_AGENT}...")

            while running_match:
                clock.tick(60) 

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running_program = False
                        running_match = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                        # Salva o melhor ATUAL da lista de candidatos
                        best_L = max(pop_left, key=lambda c: c.fitness)
                        save_best_model(best_L.brain, "LEFT_ROBUST")
                        running_program = False
                        running_match = False

                elapsed = (pygame.time.get_ticks() - start_time) / 1000
                if elapsed >= TIME_PER_MATCH:
                    running_match = False

                screen.fill((0, 0, 0))
                ended = True
                
                # Update Físico e Neural
                for q in quadras:
                    if q.status == 0: ended = False
                    q.update()
                    
                    # --- CÁLCULO DE FITNESS DA PARTIDA ---
                    for agent in q.players:
                        if agent.type != 'AGENT' or q.status != 0: continue
                        
                        # 1. Pressão / Ataque
                        is_attacking = False
                        if agent.team == 0 and (q.ball.x - q.begin[0] > q.largura/2): is_attacking = True
                        elif agent.team == 1 and (q.ball.x - q.begin[0] < q.largura/2): is_attacking = True
                        
                        if is_attacking: agent.fitness += 0.02
                        else: agent.fitness -= 0.01

                        # 2. Gol (Resetado pela quadra, mas capturado aqui)
                        if q.pontuou:
                            my_score = q.score[agent.team]
                            enemy_score = q.score[1 - agent.team]
                            agent.fitness += my_score * 30
                            agent.fitness -= enemy_score * 15
                            
                            # Hack para resetar flag apenas uma vez por frame
                            if q.players[-1] == agent: q.pontuou = False 

                        # 3. Penalidades
                        agent.fitness -= 0.001 # Tempo
                        if agent.walking == 0: agent.fitness -= 0.1 # Preguiça

                if ended: running_match = False

                # --- VISUALIZAÇÃO ---
                # Acha o melhor agente NA TELA (só para desenhar o quadrado)
                # Nota: Isso é visual, o fitness real está sendo somado depois
                if active_agents_left and active_agents_right:
                    best_vis_L = max(active_agents_left, key=lambda a: a.fitness)
                    best_vis_R = max(active_agents_right, key=lambda a: a.fitness)
                    
                    pygame.draw.rect(screen, config.LEFT_WIN_COLOR, [best_vis_L.begin[0], best_vis_L.begin[1], best_vis_L.end[0]-best_vis_L.begin[0], best_vis_L.end[1]-best_vis_L.begin[1]], 4)
                    pygame.draw.rect(screen, config.RIGHT_WIN_COLOR, [best_vis_R.begin[0], best_vis_R.begin[1], best_vis_R.end[0]-best_vis_R.begin[0], best_vis_R.end[1]-best_vis_R.begin[1]], 4)
                    
                    # Sidebar mostra "Round X" no tempo
                    # Para mostrar o fitness global, pegamos do candidato, não do agente
                    best_cand_global = max(pop_left + pop_right, key=lambda c: c.fitness)
                    
                    # Texto personalizado para mostrar o Round na sidebar
                    sidebar_time_text = f"Round {match_round}/{MATCHES_PER_AGENT} | {int(TIME_PER_MATCH - elapsed)}s"
                    
                    # Gambiarra visual: Criamos um "Fake Agent" só pra passar o fitness global acumulado pra sidebar
                    class FakeAgent:
                        def __init__(self, f): self.fitness = f
                        
                    sidebar.draw(generation, best_cand_global, TIME_PER_MATCH - elapsed)
                    # Sobrescreve o texto de tempo da sidebar (opcional, requer alteração na sidebar, 
                    # mas o padrão vai mostrar o tempo restante do round, o que já é bom)

                pygame.display.flip()
            
            if not running_program: break
            
            # --- FIM DA RODADA: CONSOLIDAÇÃO DE PONTOS ---
            # Soma o fitness da partida ao fitness TOTAL do Candidato
            for q in quadras:
                for agent in q.players:
                    if agent.type == 'AGENT':
                        # Pontos finais da partida (Vitória/Placar)
                        my_score = q.score[agent.team]
                        enemy_score = q.score[1 - agent.team]
                        agent.fitness += my_score * 100
                        agent.fitness -= enemy_score * 50
                        
                        # Recupera o Candidato dono desse agente e soma tudo
                        candidate = agent_to_candidate_map[agent]
                        candidate.fitness += agent.fitness

        if not running_program: break

        # --- FIM DA GERAÇÃO ---
        
        # Evolução baseada no Fitness ACUMULADO das 3 partidas
        pop_left, fit_L = evolve_candidates(pop_left, pop_size_side)
        pop_right, fit_R = evolve_candidates(pop_right, pop_size_side)
        
        best_global = max(fit_L, fit_R)
        print(f"Gen {generation} Finalizada | Best Score (Avg): {best_global/MATCHES_PER_AGENT:.2f}")
        
        # Salva histórico (usamos a média por partida para o gráfico não explodir em valores altos)
        sidebar.update_history(best_global / MATCHES_PER_AGENT)
        
        generation += 1

    pygame.quit()

if __name__ == "__main__":
    main()