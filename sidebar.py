import pygame
import json
import os
import matplotlib
import matplotlib.pyplot as plt
import io
import numpy as np

# Configura backend não-interativo
matplotlib.use("Agg")

class Sidebar:
    def __init__(self, screen, x_start, width, height):
        self.screen = screen
        self.x_start = x_start
        self.width = width
        self.height = height
        
        self.font_title = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_text = pygame.font.SysFont("Consolas", 14)
        self.font_tiny = pygame.font.SysFont("Arial", 11)
        
        self.margin_x = 20
        self.net_y_start = 420 

        self.history_file = "training_history.json"
        self.fitness_history = self.load_history()
        self.cached_graph_surface = None
        self.update_graph_surface()

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    return [float(x) for x in data]
            except:
                return []
        return []

    def update_history(self, best_fitness):
        self.fitness_history.append(float(best_fitness))
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.fitness_history, f)
        except Exception as e:
            print(f"Erro ao salvar: {e}")
        self.update_graph_surface()

    def update_graph_surface(self):
        dpi = 100
        w_inch = (self.width - 40) / dpi
        h_inch = 2.4 
        
        fig, ax = plt.subplots(figsize=(w_inch, h_inch), dpi=dpi)
        fig.patch.set_facecolor('#2D2D2D')
        ax.set_facecolor('#1E1E1E')
        
        data = self.fitness_history
        if not data: data = [0]
        iterations = range(1, len(data) + 1)
        
        ax.plot(iterations, data, color='#00FFFF', linewidth=2, marker='o', markersize=3)
        ax.fill_between(iterations, data, color='#00FFFF', alpha=0.15)
        ax.grid(True, color='#444444', linestyle='--', linewidth=0.5, alpha=0.7)
        ax.tick_params(axis='both', colors='#BBBBBB', labelsize=8)
        
        for spine in ax.spines.values():
            spine.set_edgecolor('#555555')
            
        ax.set_title("Evolução do Fitness (Média)", color='white', fontsize=9, pad=5)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        self.cached_graph_surface = pygame.image.load(buf)
        plt.close(fig)
        buf.close()

    # --- ATUALIZADO: Aceita Round Info ---
    def draw(self, generation, current_round, total_rounds, best_agent, elapsed_time, phase_status):
        # Fundo
        pygame.draw.rect(self.screen, (30, 30, 30), (self.x_start, 0, self.width, self.height))
        pygame.draw.line(self.screen, (80, 80, 80), (self.x_start, 0), (self.x_start, self.height), 2)

        # Cabeçalho
        y_cursor = 20
        self._draw_centered_text(f"GEN: {generation}", y_cursor, size=24, color=(255, 215, 0))
        
        y_cursor += 30
        self._draw_centered_text(f"Round: {current_round}/{total_rounds}", y_cursor, size=18, color=(200, 200, 255))
        
        y_cursor += 25
        self._draw_centered_text(f"Tempo: {int(elapsed_time)}s", y_cursor)

        y_cursor += 25
        # Mostra o status da fase (Exploração ou Refinamento)
        self._draw_centered_text(phase_status, y_cursor, size=12, color=(150, 255, 150))

        y_cursor += 25
        if best_agent:
            fit = best_agent.fitness
            c = (0, 255, 0) if fit > 0 else (255, 100, 100)
            self._draw_centered_text(f"Best Acumulado: {fit:.2f}", y_cursor, color=c)

        # Gráfico
        if self.cached_graph_surface:
            img_x = self.x_start + (self.width - self.cached_graph_surface.get_width()) // 2
            self.screen.blit(self.cached_graph_surface, (img_x, 160))

        # Rede Neural
        if best_agent:
            self._draw_neural_net(best_agent.brain, self.margin_x, self.net_y_start, self.width - 2*self.margin_x, 300)

    def _draw_centered_text(self, text, y, size=14, color=(220, 220, 220)):
        font = self.font_title if size > 18 else self.font_text
        if size < 14: font = self.font_tiny
        surf = font.render(str(text), True, color)
        x = self.x_start + (self.width - surf.get_width()) // 2
        self.screen.blit(surf, (x, y))

    def _draw_neural_net(self, brain, x_rel, y_abs, w, h):
        abs_x = self.x_start + x_rel
        t_surf = self.font_tiny.render("Rede Neural (Melhor Global)", True, (120, 120, 120))
        self.screen.blit(t_surf, (self.x_start + (self.width/2) - t_surf.get_width()/2, y_abs - 20))

        if not hasattr(brain, 'last_activations') or not brain.last_activations: return

        activations = brain.last_activations
        weights = brain.weights
        layer_sizes = [brain.input_size] + brain.hidden_sizes + [brain.output_size]
        
        node_positions = []
        layer_gap = w / (len(layer_sizes) - 1)
        
        for i, size in enumerate(layer_sizes):
            lx = abs_x + i * layer_gap
            v_step = h / (size + 1)
            layer_nodes = []
            for j in range(size):
                ly = y_abs + (j + 1) * v_step
                layer_nodes.append((lx, ly))
            node_positions.append(layer_nodes)

        for i, layer_weights in enumerate(weights):
            rows, cols = layer_weights.shape
            for s in range(rows):
                for t in range(cols):
                    val = layer_weights[s][t]
                    if abs(val) > 0.3:
                        start, end = node_positions[i][s], node_positions[i+1][t]
                        color = (0, 200, 0) if val > 0 else (200, 0, 0)
                        width_line = max(1, int(abs(val)*1.5))
                        pygame.draw.line(self.screen, color, start, end, width_line)

        for i, nodes in enumerate(node_positions):
            for j, pos in enumerate(nodes):
                val = activations[i][j]
                intensity = max(0, min(255, int(((val + 1) / 2) * 255)))
                if i == 0: color = (intensity, intensity, 255)
                elif i == len(layer_sizes)-1: color = (intensity, 0, 0) if j==0 else (0, intensity, 0)
                else: color = (intensity, intensity, intensity)
                pygame.draw.circle(self.screen, color, (int(pos[0]), int(pos[1])), 6)
                pygame.draw.circle(self.screen, (80,80,80), (int(pos[0]), int(pos[1])), 6, 1)