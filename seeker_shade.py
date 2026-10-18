from primitives import GameObject
import pygame
import constants as c

class SeekerShade(GameObject):

    def __init__(self, game):
        super().__init__(game)
        self.surf = pygame.Surface(c.WINDOW_SIZE)
        self.surf.fill((0, 0, 0))
        text = self.game.word_font.render("  You're the seeker!\nWait for the hiders.", True, (255, 255, 255))
        self.surf.blit(text, (c.WINDOW_WIDTH//2 - text.get_width()//2, c.WINDOW_HEIGHT//2 - text.get_height()//2))
        self.visible = True
        self.showing = 1

    def draw(self, surf, offset=(0, 0)):
        if self.showing <= 0:
            return
        x = c.WINDOW_WIDTH//2 + offset[0] - self.surf.get_width()//2
        y = c.WINDOW_HEIGHT//2 + offset[1] - self.surf.get_height()//2
        self.surf.set_alpha(self.showing * 255)
        surf.blit(self.surf, (x, y))

    def set_visible(self, visible=True):
        self.visible = visible

    def update(self, dt, events):
        if not self.visible:
            self.showing -= dt*2
            if self.showing < 0:
                self.showing = 0