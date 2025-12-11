import pygame


class Goal:
    """Representa uma trave/goal em uma das extremidades da quadra.

    - side: 'left' ou 'right'
    - score_for: índice do time que marca quando a bola entrar aqui
    """
    def __init__(self, begin, end, side, screen, height_ratio=0.35, depth_pixels=None):
        self.begin = begin
        self.end = end
        self.screen = screen
        self.side = side

        largura = end[0] - begin[0]
        altura = end[1] - begin[1]

        self.height = int(altura * height_ratio)
        self.y_top = begin[1] + (altura - self.height) // 2
        self.y_bottom = self.y_top + self.height

        # profundeza da trave em pixels (quanto a abertura 'entra' na quadra)
        # proporcional à largura da quadra local para escalar com ROWS/COLUMNS
        default_depth = max(6, int(largura * 0.04))
        self.depth = depth_pixels if depth_pixels is not None else default_depth

        if side == 'left':
            # rect posicionada dentro da quadra, à esquerda, expandida para detectabilidade
            self.rect = pygame.Rect(begin[0] - self.depth, self.y_top, self.depth * 2, self.height)
            # quando a bola entra na trave esquerda, o time da direita (1) pontua
            self.score_for = 1
        else:
            # rect posicionada dentro da quadra, à direita, expandida para detectabilidade
            self.rect = pygame.Rect(end[0] - self.depth, self.y_top, self.depth * 2, self.height)
            self.score_for = 0

    def draw(self):
        # Desenha trave preenchida e borda para maior visibilidade
        goal_fill = (255, 255, 255)
        border_color = (200, 50, 50)
        pygame.draw.rect(self.screen, goal_fill, self.rect)
        border_w = max(1, int(self.depth * 0.3))
        pygame.draw.rect(self.screen, border_color, self.rect, border_w)

        # Desenha 'postes' superior e inferior (marcadores internos)
        post_thickness = max(1, int(self.height * 0.06))
        left_x = self.rect.left
        right_x = self.rect.right
        top_y = self.rect.top
        bottom_y = self.rect.bottom

        # desenha pequenas linhas brancas indicando os postes (internas)
        pygame.draw.line(self.screen, (255, 255, 255), (left_x, top_y), (right_x, top_y), post_thickness)
        pygame.draw.line(self.screen, (255, 255, 255), (left_x, bottom_y), (right_x, bottom_y), post_thickness)

    def contains_ball(self, ball):
        return self.rect.collidepoint(int(ball.x), int(ball.y))
