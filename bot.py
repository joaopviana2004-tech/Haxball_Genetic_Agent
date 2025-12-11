from entity import Entity

class Bot(Entity):
    def __init__(self, x, y, color=(255, 0, 0), target=None):
        super().__init__(x, y, radius=20, color=color, speed=4)
        self.target = target  # entidade que o bot vai seguir

    def update(self):
        if self.target is None:
            return

        dx = dy = 0

        if self.x < self.target.x:
            dx = 1
        elif self.x > self.target.x:
            dx = -1
        
        if self.y < self.target.y:
            dy = 1
        elif self.y > self.target.y:
            dy = -1

        self.move(dx, dy)
