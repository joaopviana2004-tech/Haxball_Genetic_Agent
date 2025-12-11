import pygame

class Entity:
    def __init__(self, x, y, begin, end, screen,radius,color=(255, 255, 255), speed=5):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed = speed
        self.begin= begin
        self.end= end
        self.screen = screen

    def draw(self):
        pygame.draw.circle(self.screen, self.color, (int(self.x), int(self.y)), self.radius)

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        if(self.x >= self.end[0] + self.radius):
            self.x = self.end[0] + self.radius
        if(self.x <= self.begin[0] - self.radius):
            self.x = self.begin[0] - self.radius

        if(self.y >= self.end[1] + self.radius):
            self.y = self.end[1] + self.radius
        if(self.y <= self.begin[1] - self.radius):
            self.y =  self.begin[1] - self.radius

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def get_position(self):
        return (self.x, self.y)
