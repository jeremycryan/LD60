from primitives import GameObject
import pygame


class SeekerCrosshairs(GameObject):
    def __init__(self, game):
        super().__init__(game)
        self.surf = pygame.Surface((10, 10))
        self.surf.fill((255, 255, 0))
        self.target_position = self.position.copy()
        self.word_to_follow = None

    def update(self, dt, events):
        diff = self.target_position - self.position
        self.position += diff * dt * 10
        if self.word_to_follow:
            self.target_position = self.word_to_follow.position

    def draw(self, surf, offset=(0, 0)):
        x = self.position.x + offset[0] - self.surf.get_width()//2
        y = self.position.y + offset[1] - self.surf.get_height()//2
        surf.blit(self.surf, (x, y))
