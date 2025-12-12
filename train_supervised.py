import pygame
import pickle
import os
import math
from datetime import datetime
import numpy as np

from quadra import Quadra
from redeneural import RedeNeural
from bot import Bot
import config

# --- CONFIGURAÇÕES DE TREINAMENTO SUPERVISIONADO ---
SUPERVISED_MATCHES = 20  # 20 partidas contra bot fixo
MATCH_DURATION = 30      # Segundos por partida (aumentado de 15)
POPULATION_SIZE = config.ROWS * config.COLUMNS * 2

# --- CONFIGURAÇÕES DE TREINAMENTO GENÉTICO (Stage 2) ---
TIME_PER_GENERATION = 30  # Aumentado de 20
MUTATION_RATE = 0.15
MUTATION_SCALE = 0.25
ELITISM_PERCENT = 0.1

def save_best_model(brain, stage=""):
    """Salva o melhor modelo em um arquivo .pkl com data/hora"""
    if not os.path.exists("models"):
        os.makedirs("models")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"models/best_model_{stage}_{timestamp}.pkl"
    
    with open(filename, 'wb') as f:
        pickle.dump(brain, f)
    
    print(f"✅ Modelo salvo com sucesso: {filename}")
    return filename

def load_best_model(filepath):
    """Carrega um modelo salvo"""
    if not os.path.exists(filepath):
        print(f"❌ Arquivo não encontrado: {filepath}")
        return None
    
    with open(filepath, 'rb') as f:
        brain = pickle.load(f)
    
    print(f"✅ Modelo carregado: {filepath}")
    return brain

def stage1_supervised_training(initial_brain=None):
    """
    Stage 1: Treino Supervisionado contra Bot Fixo
    - 20 partidas contra um bot fixo
    - O agente aprende a jogar melhor
    """
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    pygame.display.set_caption("Stage 1: Treinamento Supervisionado contra Bot")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    # Cria ou carrega o cérebro do agente
    if initial_brain is None:
        agent_brain = RedeNeural(input_size=9)
    else:
        agent_brain = initial_brain.copy()
    
    agent_fitnesses = []
    
    print("\n" + "="*60)
    print("STAGE 1: TREINAMENTO SUPERVISIONADO (Agent vs Fixed Bot)")
    print("="*60)
    
    for match_num in range(1, SUPERVISED_MATCHES + 1):
        print(f"\n--- Partida {match_num}/{SUPERVISED_MATCHES} ---")
        
        # Cria ambiente (apenas 1 quadra com 1 agent + 1 bot fixo)
        q = Quadra(screen, (0, 0), (config.WINDOW_WIDTH, config.WINDOW_HEIGHT), ['agent', 'player'])
        
        # Injeta o cérebro no agente
        agent = q.players[0]
        agent.brain = agent_brain.copy()
        agent.fitness = 0
        
        # Bot fixo (sem evolução)
        bot = q.players[1]
        
        # Simula a partida
        start_time = pygame.time.get_ticks()
        running_match = True
        
        while running_match:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return agent_brain
            
            elapsed = (pygame.time.get_ticks() - start_time) / 1000
            if elapsed >= MATCH_DURATION:
                running_match = False
            
            screen.fill((0, 0, 0))
            q.update()
            
            # Cálculo de Fitness
            dist_max = math.hypot(q.largura, q.altura)
            dist_ball = math.hypot(agent.x - q.ball.x, agent.y - q.ball.y)
            
            if dist_ball < (agent.radius + q.ball.radius + 2):
                agent.fitness += 2.0
            
            if dist_ball < dist_max:
                agent.fitness += (1 - (dist_ball / dist_max)) * 0.05
            
            agent.fitness += agent.team == 0 and q.score[0] or q.score[1] * 50
            agent.fitness -= agent.team == 0 and q.score[1] or q.score[0] * 20
            
            # Draw
            info = font.render(f"Partida {match_num}/{SUPERVISED_MATCHES} | Tempo: {int(MATCH_DURATION - elapsed)}s | Score: {q.score[0]} - {q.score[1]}", True, (255, 255, 255))
            screen.blit(info, (10, 10))
            fit = font.render(f"Fitness: {agent.fitness:.2f}", True, (0, 255, 0))
            screen.blit(fit, (10, 35))
            
            pygame.display.flip()
        
        agent_fitnesses.append(agent.fitness)
        print(f"Fitness final: {agent.fitness:.2f}")
        print(f"Score: {q.score[0]} - {q.score[1]}")
    
    pygame.quit()
    
    print("\n" + "="*60)
    print(f"STAGE 1 COMPLETO!")
    print(f"Média de Fitness: {np.mean(agent_fitnesses):.2f}")
    print(f"Melhor Fitness: {np.max(agent_fitnesses):.2f}")
    print("="*60)
    
    return agent_brain

def stage2_genetic_training(population_seed_brain=None):
    """
    Stage 2: Treinamento Genético Agent vs Agent
    - Usa o agente treinado em Stage 1 como seed
    - Evolui contra outros agentes
    """
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    pygame.display.set_caption("Stage 2: Treinamento Genético Agent vs Agent")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)
    
    print("\n" + "="*60)
    print("STAGE 2: TREINAMENTO GENÉTICO (Agent vs Agent)")
    print("="*60)
    
    # Inicializa população com o modelo treinado como base
    if population_seed_brain is not None:
        # Cria população baseada no melhor modelo de Stage 1
        population_brains = [population_seed_brain.copy() for _ in range(POPULATION_SIZE)]
        # Aplica pequenas mutações à população inicial
        for brain in population_brains:
            brain.mutate(mutation_rate=0.05, mutation_scale=0.1)
    else:
        population_brains = [RedeNeural(input_size=9) for _ in range(POPULATION_SIZE)]
    
    generation = 1
    running_program = True
    
    while running_program:
        quadras = []
        all_agents = []
        
        cell_width = config.WINDOW_WIDTH / config.COLUMNS
        cell_height = config.WINDOW_HEIGHT / config.ROWS
        
        agent_index = 0
        
        for y in range(config.ROWS):
            for x in range(config.COLUMNS):
                cx = x * cell_width
                cy = y * cell_height
                q = Quadra(screen, (cx, cy), (cx + cell_width, cy + cell_height), ['agent', 'agent'])
                quadras.append(q)
                
                for agent in q.players:
                    agent.brain = population_brains[agent_index]
                    agent.fitness = 0
                    all_agents.append(agent)
                    agent_index += 1
        
        start_time = pygame.time.get_ticks()
        running_generation = True
        
        print(f"\n--- Geração {generation} Iniciada ---")
        
        while running_generation:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_program = False
                    running_generation = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        best_agent = max(all_agents, key=lambda a: a.fitness)
                        save_best_model(best_agent.brain, "stage2")
                        running_program = False
                        running_generation = False
            
            elapsed_seconds = (pygame.time.get_ticks() - start_time) / 1000
            if elapsed_seconds >= TIME_PER_GENERATION:
                running_generation = False
            
            screen.fill((0, 0, 0))
            
            for q in quadras:
                q.update()
                
                dist_max = math.hypot(q.largura, q.altura)
                
                for agent in q.players:
                    dist_ball = math.hypot(agent.x - q.ball.x, agent.y - q.ball.y)
                    
                    if dist_ball < (agent.radius + q.ball.radius + 2):
                        agent.fitness += 2.0
                    
                    if dist_ball < dist_max:
                        agent.fitness += (1 - (dist_ball / dist_max)) * 0.05
                    
                    my_score = q.score[agent.team]
                    enemy_score = q.score[1 - agent.team]
                    
                    agent.fitness += my_score * 50
                    agent.fitness -= enemy_score * 20
            
            info_text = font.render(f"Geração: {generation} | Tempo: {int(TIME_PER_GENERATION - elapsed_seconds)}s | [Q] Salvar e Sair", True, (255, 255, 255))
            screen.blit(info_text, (10, 10))
            
            best_now = max(all_agents, key=lambda a: a.fitness)
            fit_text = font.render(f"Melhor Fitness: {best_now.fitness:.2f}", True, (0, 255, 0))
            screen.blit(fit_text, (10, 35))
            
            pygame.display.flip()
        
        if not running_program:
            break
        
        # EVOLUÇÃO
        all_agents.sort(key=lambda x: x.fitness, reverse=True)
        
        print(f"Melhor Fitness Geração {generation}: {all_agents[0].fitness:.2f}")
        
        num_elites = int(POPULATION_SIZE * ELITISM_PERCENT)
        new_population = []
        
        for i in range(num_elites):
            new_population.append(all_agents[i].brain.copy())
        
        remaining_slots = POPULATION_SIZE - num_elites
        
        for _ in range(remaining_slots):
            parent_pool = all_agents[:int(POPULATION_SIZE/2)]
            parent = parent_pool[np.random.randint(0, len(parent_pool))]
            
            child_brain = parent.brain.copy()
            child_brain.mutate(mutation_rate=MUTATION_RATE, mutation_scale=MUTATION_SCALE)
            
            new_population.append(child_brain)
        
        population_brains = new_population
        generation += 1
    
    pygame.quit()

def main():
    print("\n" + "="*60)
    print("HAXBALL AI TRAINING PIPELINE")
    print("="*60)
    
    # Opção 1: Carregar modelo salvo previamente
    print("\n[1] Carregar modelo existente")
    print("[2] Treinar novo modelo do zero")
    choice = input("Escolha (1 ou 2): ").strip()
    
    if choice == "1":
        print("\nArquivos de modelo disponíveis:")
        if os.path.exists("models"):
            models = [f for f in os.listdir("models") if f.endswith(".pkl")]
            for i, model in enumerate(models):
                print(f"  [{i}] {model}")
            
            model_idx = int(input("Escolha o índice do modelo: "))
            model_path = os.path.join("models", models[model_idx])
            initial_brain = load_best_model(model_path)
        else:
            print("Nenhum modelo encontrado. Iniciando do zero.")
            initial_brain = None
    else:
        initial_brain = None
    
    # Stage 1: Treinamento Supervisionado
    print("\n✓ Iniciando STAGE 1: Treinamento Supervisionado...")
    trained_brain = stage1_supervised_training(initial_brain)
    
    # Salva o modelo treinado em Stage 1
    stage1_model_path = save_best_model(trained_brain, "stage1")
    
    # Stage 2: Treinamento Genético
    print("\n✓ Iniciando STAGE 2: Treinamento Genético...")
    stage2_genetic_training(trained_brain)
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETO!")
    print("="*60)

if __name__ == "__main__":
    main()
