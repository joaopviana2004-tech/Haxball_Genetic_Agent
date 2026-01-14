import pygame
import pickle
import os
import math
import random 
from datetime import datetime
import numpy as np

# Importa as classes do seu projeto
from quadra import Quadra
from redeneural import RedeNeural
from sidebar import Sidebar 
from bot import Bot # <--- Importante: Oponente padrão
import config

# --- CONFIGURAÇÕES ---
TIME_PER_MATCH = 10      
MATCHES_PER_AGENT = 3     # 3 Rodadas para provar que é bom contra o Bot
ELITISM_PERCENT = 0.1     

# Ajustamos a população para caber 1 Agente por quadra (o outro slot é do Bot)
POPULATION_SIZE = config.ROWS * config.COLUMNS 

# --- CONFIGURAÇÕES DE FASES ---
MUT_RATE_EXPLORE = 0.30  
MUT_SCALE_EXPLORE = 0.50 

MUT_RATE_2 = 0.15  
MUT_SCALE_2 = 0.25 

MUT_RATE_REFINE = 0.08   
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
    
    num_elites = int(target_size * ELITISM_PERCENT)
    if num_elites < 1: num_elites = 1
    
    for i in range(num_elites):
        if i < len(candidate_list):
            new_candidates.append(Candidate(candidate_list[i].brain.copy()))
            
    remaining = target_size - len(new_candidates)
    parent_pool = candidate_list[:int(len(candidate_list)/2)]
    if not parent_pool: parent_pool = candidate_list
    
    for _ in range(remaining):
        parent = np.random.choice(parent_pool)
        child_brain = parent.brain.copy()
        child_brain.mutate(mutation_rate=mutation_rate, mutation_scale=mutation_scale)
        new_candidates.append(Candidate(child_brain))
        
    return new_candidates, candidate_list[0].fitness

def get_phase_params(total_goals):
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
    pygame.display.set_caption(f"Neural HaxBall - Agent vs Bot (Robust)")

    clock = pygame.time.Clock()
    
    # --- CONTADORES DE FASE ---
    total_goals_agent = 0

    # Carrega ou inicia
    try:
        input_sz = config.INPUT_SIZE_LAYER
    except:
        input_sz = 11

    # População Única (Só os Agentes que aprendem)
    population = [Candidate(RedeNeural(input_size=input_sz)) for _ in range(POPULATION_SIZE)]
    
    generation = 1
    if len(sidebar.fitness_history) > 0:
        generation = len(sidebar.fitness_history) + 1
    
    running_program = True
    
    while running_program:
        # Zera fitness acumulado da geração
        for c in population: c.fitness = 0
        
        print(f"--- Geração {generation} (Vs Bot) ---")
        
        # Loop de Rounds (Robustez)
        for match_round in range(1, MATCHES_PER_AGENT + 1):
            quadras = []
            agent_to_candidate_map = {}
            active_agents = [] # Lista visual dos agentes na tela
            
            cell_width = config.GAME_WIDTH / config.COLUMNS
            cell_height = config.WINDOW_HEIGHT / config.ROWS

            # Distribui Agentes nas Quadras (1 por quadra)
            for i in range(len(population)):
                row = i // config.COLUMNS
                col = i % config.COLUMNS
                cx = col * cell_width
                cy = row * cell_height
                
                # CRIAÇÃO DA QUADRA: 'agent' (Esq) vs 'bot' (Dir)
                q = Quadra(screen, (cx, cy), (cx + cell_width, cy + cell_height), ['agent', 'bot'])
                quadras.append(q)
                
                candidate = population[i]
                
                for p in q.players:
                    if p.type == 'AGENT':
                        # Configura o Agente (Time 0 - Esquerda)
                        p.fitness = 0 
                        p.brain = candidate.brain
                        agent_to_candidate_map[p] = candidate
                        active_agents.append(p)
                    elif p.type == 'BOT':
                        # Bot já vem configurado pela classe Quadra/Bot
                        pass

            start_time = pygame.time.get_ticks()
            running_match = True
            
            while running_match:
                clock.tick(60) # Mantém 60 FPS fixo (Sem Turbo)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running_program = False
                        running_match = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                        best_cand = max(population, key=lambda c: c.fitness)
                        save_best_model(best_cand.brain, "AGENT_VS_BOT")
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
                        
                        # --- FITNESS (Mesma lógica robusta) ---
                        
                        # 1. Pressão / Ataque (Quer bola na direita > 0.5)
                        ball_relative_x = (q.ball.x - q.begin[0]) / q.largura
                        reward = 0
                        
                        # Como Agent é sempre Time 0 (Esquerda) neste modo:
                        if ball_relative_x > 0.5: 
                            reward = (0.02 + ((ball_relative_x - 0.5) * 0.1))/10
                        else: 
                            agent.fitness -= 0.01
                        
                        agent.fitness += reward

                        # 2. Gol e DETECÇÃO DE FASE
                        if q.pontuou:
                            # Se o Agente (Time 0) fez gol
                            if agent.team == 1: # Time que marcou é o do agente
                                total_goals_agent += 1
                                print(f"> GOL DO AGENTE! Total: {total_goals_agent}")
                                
                                my_score = q.score[agent.team]
                                agent.fitness += my_score * 50
                            
                            # Se tomou gol do Bot
                            else: 
                                enemy_score = q.score[1 - agent.team]
                                agent.fitness -= enemy_score * 20
                            
                            if q.players[-1] == agent: q.pontuou = False 

                        agent.fitness -= 0.001 
                        if agent.walking == 0: agent.fitness -= 0.1 

                if ended: running_match = False

                # Desenha UI
                if active_agents:
                    best_vis = max(active_agents, key=lambda a: a.fitness)
                    
                    # Highlight no melhor agente
                    pygame.draw.rect(screen, config.LEFT_WIN_COLOR, [best_vis.begin[0], best_vis.begin[1], best_vis.end[0]-best_vis.begin[0], best_vis.end[1]-best_vis.begin[1]], 4)
                    
                    # Sidebar
                    best_cand_global = max(population, key=lambda c: c.fitness)
                    
                    _, _, status = get_phase_params(total_goals_agent)
                    status_txt = f"Phase: {status} | Goals: {total_goals_agent}"

                    sidebar.draw(generation, match_round, MATCHES_PER_AGENT, best_cand_global, TIME_PER_MATCH - elapsed, status_txt)

                pygame.display.flip()
            
            if not running_program: break
            
            # Soma Fitness do Round ao Candidato
            for q in quadras:
                for agent in q.players:
                    if agent.type == 'AGENT':
                        my_score = q.score[agent.team]
                        enemy_score = q.score[1 - agent.team]
                        
                        # Recompensa final da partida
                        agent.fitness += my_score * 100
                        agent.fitness -= enemy_score * 50
                        
                        candidate = agent_to_candidate_map[agent]
                        candidate.fitness += agent.fitness

        if not running_program: break

        # --- AUTO SAVE ---
        if generation % 20 == 0:
            best_cand = max(population, key=lambda c: c.fitness)
            save_best_model(best_cand.brain, f"AUTO_VSBOT_GEN{generation}")
            
        # --- EVOLUÇÃO ---
        rate, scale, _ = get_phase_params(total_goals_agent)
        population, fit_best = evolve_candidates(population, POPULATION_SIZE, rate, scale)
        
        avg_fitness = fit_best / MATCHES_PER_AGENT
        print(f"Gen {generation} Finalizada | Best (Avg): {avg_fitness:.2f}")
        
        sidebar.update_history(avg_fitness)
        generation += 1
        total_goals_agent = 0 # Reseta contagem de gols da geração

    pygame.quit()

if __name__ == "__main__":
    main()