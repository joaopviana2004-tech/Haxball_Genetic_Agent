import pygame
import config
import numpy as np

class Sidebar:
    def __init__(self, screen, x_start, width, height):
        self.screen = screen
        self.x_start = x_start
        self.total_width = width
        self.total_height = height
        
        # Fontes
        self.font_title = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_text = pygame.font.SysFont("Consolas", 14)
        self.font_tiny = pygame.font.SysFont("Arial", 10)
        
        self.fitness_history = [] 

        # ==========================================
        # CONFIGURAÇÕES DE POSICIONAMENTO E TAMANHO
        # ==========================================
        self.layout = {
            # Margens Gerais
            'margin_x': 25,          # Espaço nas laterais (esquerda/direita)
            'margin_top': 20,        # Espaço no topo
            
            # Gráfico
            'graph_y': 140,          # Posição Y onde começa o gráfico
            'graph_height': 120,     # Altura do gráfico (encurtar/alongar)
            
            # Rede Neural
            'net_y': 380,            # Posição Y onde começa a rede
            'net_height': 350,       # Altura da rede (encurtar/alongar verticalmente)
            'net_width_scale': 0.8,  # 1.0 = largura total disponivel. 0.8 = mais estreita.
            
            # Estilo dos Nós
            'node_radius': 6,        # Tamanho da bolinha
            'node_border': 1         # Grossura da borda
        }

    def draw(self, generation, best_agent, elapsed_time):
        L = self.layout 
        
        # 1. Fundo e Linha Divisória
        pygame.draw.rect(self.screen, config.BG_COLOR, (self.x_start, 0, self.total_width, self.total_height))
        pygame.draw.line(self.screen, (80, 80, 80), (self.x_start, 0), (self.x_start, self.total_height), 2)

        # 2. Cabeçalho
        curr_y = L['margin_top']
        self._draw_text(f"GERAÇÃO: {generation}", 0, curr_y, align='center', size=20, color=(255, 215, 0))
        
        curr_y += 30
        self._draw_text(f"Tempo: {int(elapsed_time)}s", 0, curr_y, align='center')
        
        curr_y += 25
        current_fit = 0
        if best_agent:
            current_fit = best_agent.fitness
            fit_color = (0, 255, 0) if current_fit > 0 else (255, 100, 100)
            self._draw_text(f"Best Fitness: {current_fit:.2f}", 0, curr_y, align='center', color=fit_color)

        # 3. Gráfico de Evolução (AGORA COM DADOS EM TEMPO REAL)
        graph_w = self.total_width - (L['margin_x'] * 2)
        # Passamos o fitness atual para ele desenhar a linha "viva"
        self._draw_evolution_graph(L['margin_x'], L['graph_y'], graph_w, L['graph_height'], current_fit)

        # 4. Rede Neural
        if best_agent:
            net_full_width = self.total_width - (L['margin_x'] * 2)
            net_actual_width = net_full_width * L['net_width_scale']
            offset_x = L['margin_x'] + (net_full_width - net_actual_width) / 2
            
            self._draw_neural_net(best_agent.brain, offset_x, L['net_y'], net_actual_width, L['net_height'])

    def update_history(self, best_fitness):
        self.fitness_history.append(best_fitness)

    def _draw_text(self, text, x_offset, y, align='left', size=14, color=config.TEXT_COLOR):
        """
        Helper melhorado com alinhamento 'center'
        """
        font = self.font_title if size >= 20 else self.font_text
        surface = font.render(text, True, color)
        
        final_x = self.x_start + x_offset
        
        if align == 'center':
            # Calcula o centro da sidebar
            center_x = self.x_start + (self.total_width / 2)
            final_x = center_x - (surface.get_width() / 2)
            
        self.screen.blit(surface, (final_x, y))

    def _draw_evolution_graph(self, x_rel, y_rel, w, h, current_val):
        abs_x = self.x_start + x_rel
        
        # 1. Fundo e Grade (Estilo Sci-Fi)
        pygame.draw.rect(self.screen, (40, 40, 45), (abs_x, y_rel, w, h))
        pygame.draw.rect(self.screen, (100, 100, 100), (abs_x, y_rel, w, h), 1)

        # Grade
        grid_color = (60, 60, 60)
        for i in range(1, 4): # Horizontais
            ly = y_rel + (h / 4) * i
            pygame.draw.line(self.screen, grid_color, (abs_x, ly), (abs_x + w, ly))
        for i in range(1, 5): # Verticais
            lx = abs_x + (w / 5) * i
            pygame.draw.line(self.screen, grid_color, (lx, y_rel), (lx, y_rel + h))

        # Título
        title_surf = self.font_tiny.render("Histórico de Fitness (Evolução)", True, (180, 180, 180))
        self.screen.blit(title_surf, (abs_x, y_rel - 15))

        # 2. TRATAMENTO DE DADOS
        data_to_plot = self.fitness_history + [current_val]
        
        # [TRUQUE] Se for a primeira geração (só 1 ponto), duplicamos o ponto
        # para criar uma linha reta que sobe e desce, dando feedback visual imediato.
        if len(data_to_plot) == 1:
            data_to_plot.append(current_val)

        # Se ainda assim estiver vazio (segurança), retorna
        if not data_to_plot: return

        # 3. ESCALA (ZOOM AUTOMÁTICO)
        max_val = max(data_to_plot)
        min_val = min(data_to_plot)
        
        # Margem de 10% para não colar no teto
        margin = (max_val - min_val) * 0.1
        if margin == 0: margin = 1.0 

        display_max = max_val + margin
        display_min = min_val - margin
        val_range = display_max - display_min

        # 4. CONSTRUÇÃO DOS PONTOS
        points = []
        for i, val in enumerate(data_to_plot):
            # Normaliza X
            px = abs_x + (i / (len(data_to_plot) - 1)) * w
            # Normaliza Y (Invertido)
            py = y_rel + h - ((val - display_min) / val_range) * h 
            points.append((px, max(y_rel, min(y_rel + h, py))))

        # 5. DESENHO (PREENCHIMENTO E LINHA)
        if len(points) > 1:
            # Efeito de Preenchimento Transparente (Glow)
            fill_surf = pygame.Surface((self.total_width, self.total_height), pygame.SRCALPHA)
            poly_points = [(points[0][0], y_rel + h)] + points + [(points[-1][0], y_rel + h)]
            pygame.draw.polygon(fill_surf, (0, 255, 255, 30), poly_points)
            self.screen.blit(fill_surf, (0, 0))

            # Linha Principal
            pygame.draw.lines(self.screen, config.GRAPH_LINE_COLOR, False, points, 2)
            
            # Ponto Pulsante na ponta
            last_pt = points[-1]
            pygame.draw.circle(self.screen, (255, 255, 255), (int(last_pt[0]), int(last_pt[1])), 3)
            # Halo ao redor do ponto
            pygame.draw.circle(self.screen, config.GRAPH_LINE_COLOR, (int(last_pt[0]), int(last_pt[1])), 6, 1)

            # 6. ETIQUETAS
            # Mostra o valor atual flutuando ao lado da linha
            lbl_color = (255, 255, 0) # Amarelo
            lbl_surf = self.font_tiny.render(f"{current_val:.1f}", True, lbl_color)
            self.screen.blit(lbl_surf, (last_pt[0] - 20, last_pt[1] - 20))

        # Max e Min no eixo Y
        self._draw_text(f"{max_val:.1f}", x_rel + 2, y_rel + 2, size=10, color=(150, 255, 150))
        self._draw_text(f"{min_val:.1f}", x_rel + 2, y_rel + h - 12, size=10, color=(255, 100, 100))

    def _draw_neural_net(self, brain, x_rel, y_rel, w, h):
        L = self.layout
        abs_x = self.x_start + x_rel
        
        # Título
        title_surf = self.font_tiny.render("Cérebro do Melhor Agente (Ao Vivo)", True, (150, 150, 150))
        self.screen.blit(title_surf, (self.x_start + (self.total_width/2) - title_surf.get_width()/2, y_rel - 20))

        if not hasattr(brain, 'last_activations') or not brain.last_activations:
            return

        activations = brain.last_activations
        weights = brain.weights
        
        layer_sizes = [brain.input_size] + brain.hidden_sizes + [brain.output_size]
        
        # --- Lógica de Posicionamento dos Nós ---
        node_positions = []
        
        # Espaçamento horizontal entre camadas
        layer_gap = w / (len(layer_sizes) - 1)
        
        for i, size in enumerate(layer_sizes):
            layer_x = abs_x + i * layer_gap
            
            # Espaçamento vertical entre neurônios desta camada
            # Aqui está o segredo para "alongar/encurtar": usamos 'h'
            vertical_step = h / (size + 1)
            
            current_layer_nodes = []
            for j in range(size):
                node_y = y_rel + (j + 1) * vertical_step
                current_layer_nodes.append((layer_x, node_y))
            node_positions.append(current_layer_nodes)

        # 1. Desenhar Conexões (Linhas)
        for i, layer_weights in enumerate(weights):
            for source_idx in range(layer_weights.shape[0]):
                for target_idx in range(layer_weights.shape[1]):
                    w_val = layer_weights[source_idx][target_idx]
                    
                    # Otimização visual: só desenha se o peso for relevante
                    if abs(w_val) > 0.2:
                        start = node_positions[i][source_idx]
                        end = node_positions[i+1][target_idx]
                        
                        color = config.WEIGHT_POS_COLOR if w_val > 0 else config.WEIGHT_NEG_COLOR
                        # Espessura baseada na força do peso (max 3px)
                        thick = max(1, min(3, int(abs(w_val) * 1.5)))
                        
                        pygame.draw.line(self.screen, color, start, end, thick)

        # 2. Desenhar Nós (Bolinhas)
        input_labels = ["D.Bola", "A.Bola", "V.Bola", "D.Adv", "A.Adv", "V.Adv", "D.Gol", "A.Gol", "Lado"]
        output_labels = ["Acel X", "Acel Y"]

        for i, layer_nodes in enumerate(node_positions):
            for j, pos in enumerate(layer_nodes):
                # Cor baseada na ativação (-1 preto, 1 branco/cor)
                val = activations[i][j]
                
                # Mapeia [-1, 1] para [0, 255]
                intensity = int(((val + 1) / 2) * 255)
                intensity = max(0, min(255, intensity))
                
                fill_color = (intensity, intensity, intensity)
                
                # Cor especial para Input (Azulado) e Output (Vermelho/Verde)
                if i == 0: # Input
                    fill_color = (intensity, intensity, min(255, intensity + 50))
                elif i == len(layer_sizes) - 1: # Output
                    if j == 0: fill_color = (intensity, 0, 0) # X
                    else: fill_color = (0, intensity, 0)      # Y
                
                pygame.draw.circle(self.screen, fill_color, (int(pos[0]), int(pos[1])), L['node_radius'])
                pygame.draw.circle(self.screen, (150, 150, 150), (int(pos[0]), int(pos[1])), L['node_radius'], L['node_border'])

                # Labels (Texto)
                label = None
                if i == 0: 
                    label = input_labels[j] if j < len(input_labels) else ""
                    self._draw_text(label, 0, 0, size=10) # Só pra pegar surface size n é o ideal mas ok
                    # Desenha label à esquerda
                    l_surf = self.font_tiny.render(label, True, (180,180,180))
                    self.screen.blit(l_surf, (pos[0] - l_surf.get_width() - 8, pos[1] - 5))
                    
                elif i == len(layer_sizes) - 1:
                    label = output_labels[j] if j < len(output_labels) else ""
                    # Desenha label à direita
                    l_surf = self.font_tiny.render(label, True, (180,180,180))
                    self.screen.blit(l_surf, (pos[0] + 10, pos[1] - 5))