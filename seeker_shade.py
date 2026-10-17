from primitives import GameObject
import pygame
import constants as c

class SeekerShade(GameObject):

    def __init__(self, game):
        super().__init__(game)
        self.surf = pygame.Surface(c.WINDOW_SIZE)
        self.surf.fill((0, 0, 0))
        text = self.game.word_font.render("You're Seeker! Wait for hiders!", True, (255, 255, 255))
        self.surf.blit(text, (10, 10))
        self.visible = True

    def draw(self, surf, offset=(0, 0)):
        if not self.visible:
            return
        surf.blit(self.surf, (0, 0))

    def set_visible(self, visible=True):
        self.visible = visible

    def update(self, dt, events):
        pass