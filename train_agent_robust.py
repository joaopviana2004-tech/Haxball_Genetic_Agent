import pygame
import pickle
import os
import math
import random 
from datetime import datetime
import numpy as np

from quadra import Quadra
from redeneural import RedeNeural
from sidebar import Sidebar 
import config

# --- CONFIGURAÇÕES DE TREINO ROBUSTO ---
TIME_PER_MATCH = 10      
MATCHES_PER_AGENT = 3     
POPULATION_SIZE = config.ROWS * config.COLUMNS * 2 
ELITISM_PERCENT = 0.1     

# --- CONFIGURAÇÕES DE FASES (Exploração vs Refinamento) ---
# Fase 1: CAOS (Exploração) - Ninguém fez gol ainda
MUT_RATE_EXPLORE = 0.30  
MUT_SCALE_EXPLORE = 0.50 

# Fase 2: INTERMEDIÁRIO - Começou a marcar, mas não é consistente (< 5 gols)
MUT_RATE_2 = 0.15  
MUT_SCALE_2 = 0.25 

# Fase 3: REFINAMENTO (Exploitation) - Consistente (>= 5 gols)
MUT_RATE_REFINE = 0.08   # Corrigido de 0.8 para 0.08 para condizer com "Ajuste fino"
MUT_SCALE_REFINE = 0.10  

class Candidate:
    def __init__(self, brain):
        self.brain = brain
        self.fitness = 0 

def save_best_model(brain, prefix):
    if not os.path.exists("models"): os.makedirs("models")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"models/best_{prefix}_{timestamp}.pkl"
    with open(filename, 'wb') as f: pickle.dump(brain, f)
    print(f"✅ Modelo {prefix} salvo: {filename}")

def evolve_candidates(candidate_list, target_size, mutation_rate, mutation_scale):
    candidate_list.sort(key=lambda x: x.fitness, reverse=True)
    new_candidates = []
    
    # Elitismo
    num_elites = int(target_size * ELITISM_PERCENT)
    if num_elites < 1: num_elites = 1
    
    for i in range(num_elites):
        if i < len(candidate_list):
            new_candidates.append(Candidate(candidate_list[i].brain.copy()))
            
    # Reprodução
    remaining = target_size - len(new_candidates)
    parent_pool = candidate_list[:int(len(candidate_list)/2)]
    if not parent_pool: parent_pool = candidate_list
    
    for _ in range(remaining):
        parent = np.random.choice(parent_pool)
        child_brain = parent.brain.copy()
        # Usa os parâmetros dinâmicos passados
        child_brain.mutate(mutation_rate=mutation_rate, mutation_scale=mutation_scale)
        new_candidates.append(Candidate(child_brain))
        
    return new_candidates, candidate_list[0].fitness

def get_phase_params(total_goals):
    """Retorna (Rate, Scale, NomeDaFase) baseado no histórico de gols"""
    if total_goals == 0:
        return MUT_RATE_EXPLORE, MUT_SCALE_EXPLORE, "EXPLORE"
    elif total_goals < 6:
        return MUT_RATE_2, MUT_SCALE_2, "INTERMED"
    else:
        return MUT_RATE_REFINE, MUT_SCALE_REFINE, "REFINE"

def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    sidebar = Sidebar(screen, config.GAME_WIDTH, config.SIDEBAR_WIDTH, config.WINDOW_HEIGHT)
    pygame.display.set_caption(f"Neural HaxBall - Robust Training")

    clock = pygame.time.Clock()
    pop_size_side = int(POPULATION_SIZE / 2)
    
    # --- CONTADORES DE GOLS PARA CONTROLE DE FASE ---
    # Substituem os flags booleanos antigos
    total_goals_left = 0
    total_goals_right = 0

    # Carrega ou inicia
    # Ajustado para INPUT_SIZE 11 conforme conversas anteriores sobre normalização
    try:
        input_sz = config.INPUT_SIZE_LAYER
    except:
        input_sz = 11 # Fallback caso não esteja no config

    pop_left = [Candidate(RedeNeural(input_size=input_sz)) for _ in range(pop_size_side)]
    pop_right = [Candidate(RedeNeural(input_size=input_sz)) for _ in range(pop_size_side)]
    
    generation = 1
    if len(sidebar.fitness_history) > 0:
        generation = len(sidebar.fitness_history) + 1
    
    running_program = True
    
    while running_program:
        # Zera fitness acumulado
        for c in pop_left: c.fitness = 0
        for c in pop_right: c.fitness = 0
        
        print(f"--- Geração {generation} ---")
        indices_left = list(range(len(pop_left)))
        indices_right = list(range(len(pop_right)))

        # Loop de Rounds
        for match_round in range(1, MATCHES_PER_AGENT + 1):
            random.shuffle(indices_right)
            quadras = []
            agent_to_candidate_map = {}
            active_agents_left = []
            active_agents_right = []
            
            cell_width = config.GAME_WIDTH / config.COLUMNS
            cell_height = config.WINDOW_HEIGHT / config.ROWS

            for i in range(len(pop_left)):
                row = i // config.COLUMNS
                col = i % config.COLUMNS
                cx = col * cell_width
                cy = row * cell_height
                q = Quadra(screen, (cx, cy), (cx + cell_width, cy + cell_height), ['agent', 'agent'])
                quadras.append(q)
                
                cand_L = pop_left[indices_left[i]]
                cand_R = pop_right[indices_right[i]]
                
                for agent in q.players:
                    if agent.type == 'AGENT':
                        agent.fitness = 0 
                        if agent.team == 0:
                            agent.brain = cand_L.brain
                            agent_to_candidate_map[agent] = cand_L
                            active_agents_left.append(agent)
                        else:
                            agent.brain = cand_R.brain
                            agent_to_candidate_map[agent] = cand_R
                            active_agents_right.append(agent)

            start_time = pygame.time.get_ticks()
            running_match = True
            
            while running_match:
                clock.tick(60) 

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running_program = False
                        running_match = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                        best_L = max(pop_left, key=lambda c: c.fitness)
                        save_best_model(best_L.brain, "LEFT_MANUAL")
                        best_R = max(pop_right, key=lambda c: c.fitness)
                        save_best_model(best_R.brain, "RIGHT_MANUAL")
                        running_program = False
                        running_match = False

                elapsed = (pygame.time.get_ticks() - start_time) / 1000
                if elapsed >= TIME_PER_MATCH:
                    running_match = False

                screen.fill((0, 0, 0))
                ended = True
                
                for q in quadras:
                    if q.status == 0: ended = False
                    q.update()
                    
                    for agent in q.players:
                        if agent.type != 'AGENT' or q.status != 0: continue
                        
                        # 1. Pressão / Ataque
                        ball_relative_x = (q.ball.x - q.begin[0]) / q.largura
                        reward = 0
                        if agent.team == 0:
                            if ball_relative_x > 0.5: reward = (0.02 + ((ball_relative_x - 0.5) * 0.1))/10
                            else: agent.fitness -= 0.01
                        elif agent.team == 1:
                            if ball_relative_x < 0.5: reward = (0.02 + ((0.5 - ball_relative_x) * 0.1))/10
                            else: agent.fitness -= 0.01
                        agent.fitness += reward

                        # 2. Gol e DETECÇÃO DE FASE
                        if q.pontuou:
                            # Contagem de Gols para evolução de fase
                            if agent.team == 0:
                                total_goals_left += 1
                                print(f"> GOL ESQUERDA! Total: {total_goals_left}")
                            elif agent.team == 1:
                                total_goals_right += 1
                                print(f"> GOL DIREITA! Total: {total_goals_right}")

                            my_score = q.score[agent.team]
                            enemy_score = q.score[1 - agent.team]
                            agent.fitness += my_score * 50
                            agent.fitness -= enemy_score * 20
                            
                            if q.players[-1] == agent: q.pontuou = False 

                        agent.fitness -= 0.001 
                        if agent.walking == 0: agent.fitness -= 0.1 

                if ended: running_match = False

                if active_agents_left and active_agents_right:
                    best_vis_L = max(active_agents_left, key=lambda a: a.fitness)
                    best_vis_R = max(active_agents_right, key=lambda a: a.fitness)
                    
                    pygame.draw.rect(screen, config.LEFT_WIN_COLOR, [best_vis_L.begin[0], best_vis_L.begin[1], best_vis_L.end[0]-best_vis_L.begin[0], best_vis_L.end[1]-best_vis_L.begin[1]], 4)
                    pygame.draw.rect(screen, config.RIGHT_WIN_COLOR, [best_vis_R.begin[0], best_vis_R.begin[1], best_vis_R.end[0]-best_vis_R.begin[0], best_vis_R.end[1]-best_vis_R.begin[1]], 4)
                    
                    # Sidebar
                    best_cand_global = max(pop_left + pop_right, key=lambda c: c.fitness)
                    
                    # Pega status baseado nos gols
                    _, _, status_L = get_phase_params(total_goals_left)
                    _, _, status_R = get_phase_params(total_goals_right)
                    status_txt = f"L: {status_L}({total_goals_left}) | R: {status_R}({total_goals_right})"

                    sidebar.draw(generation, match_round, MATCHES_PER_AGENT, best_cand_global, TIME_PER_MATCH - elapsed, status_txt)

                pygame.display.flip()
            
            if not running_program: break
            
            # Soma Fitness do Round
            for q in quadras:
                for agent in q.players:
                    if agent.type == 'AGENT':
                        my_score = q.score[agent.team]
                        enemy_score = q.score[1 - agent.team]
                        agent.fitness += my_score * 100
                        agent.fitness -= enemy_score * 50
                        candidate = agent_to_candidate_map[agent]
                        candidate.fitness += agent.fitness

        if not running_program: break

        # --- AUTO SAVE ---
        if generation % 20 == 0:
            best_L = max(pop_left, key=lambda c: c.fitness)
            save_best_model(best_L.brain, f"AUTO_L_GEN{generation}")
            best_R = max(pop_right, key=lambda c: c.fitness)
            save_best_model(best_R.brain, f"AUTO_R_GEN{generation}")
            
        # --- EVOLUÇÃO COM PARÂMETROS ADAPTATIVOS (3 FASES) ---
        
        # Define parametros para Esquerda
        rate_L, scale_L, _ = get_phase_params(total_goals_left)
        pop_left, fit_L = evolve_candidates(pop_left, pop_size_side, rate_L, scale_L)
        
        # Define parametros para Direita
        rate_R, scale_R, _ = get_phase_params(total_goals_right)
        pop_right, fit_R = evolve_candidates(pop_right, pop_size_side, rate_R, scale_R)
        
        best_global = max(fit_L, fit_R)
        print(f"Gen {generation} Finalizada | Best (Avg): {best_global/MATCHES_PER_AGENT:.2f}")
        
        sidebar.update_history(best_global / MATCHES_PER_AGENT)
        generation += 1
        total_goals_left = 0
        total_goals_right = 0

    pygame.quit()

if __name__ == "__main__":
    main()