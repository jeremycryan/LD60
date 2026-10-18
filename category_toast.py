import primitives
from primitives import GameObject
import pygame
import constants as c

class CategoryToast(GameObject):

    ANIM_POINT_1 = 0.5
    ANIM_POINT_2 = 2.7
    ANIM_POINT_3 = 3.2

    def __init__(self, game, display_name, text_name, ):
        self.game = game
        self.display_name = display_name
        self.text_name = text_name

        self.age = 0

        self.shown_characters = 0
        self.text_surf = None
        self.white = pygame.Surface(c.WINDOW_SIZE)
        self.white.fill(c.WHITE)

    def update_text_surf(self):
        shown_characters = int((self.through_middle() * 2) * len(self.text_name))
        if shown_characters != self.shown_characters:
            self.text_surf = self.game.toast_font.render(self.text_name[:shown_characters], True, (0, 0, 0))

    def update(self, dt, events):
        self.age += dt
        self.update_text_surf()

    def through_middle(self):
        if self.age < self.ANIM_POINT_1:
            return 0
        if self.age > self.ANIM_POINT_2:
            return 1
        return (self.age - self.ANIM_POINT_1)/(self.ANIM_POINT_2 - self.ANIM_POINT_1)

    def through_end(self):
        if self.age < self.ANIM_POINT_2:
            return 0
        return (self.age - self.ANIM_POINT_2)/(self.ANIM_POINT_3 - self.ANIM_POINT_2)

    def draw(self, surf, offset=(0, 0)):
        if self.age <= self.ANIM_POINT_1:
            black_width_factor = -(abs((self.age/self.ANIM_POINT_1 - 1)**3)) + 1
        elif self.age < self.ANIM_POINT_2:
            black_width_factor = 1
        elif self.age < self.ANIM_POINT_3:
            black_width_factor = 1 + self.through_end()**2 * 5
        else:
            return

        self.white.fill((255, 255, 255))

        if self.text_surf and self.age < 5:
            copy = primitives.scale_surface_by(self.text_surf, 1 - 0.5*(self.through_end())**2)
            x = c.WINDOW_WIDTH // 2 - copy.get_width() // 2
            #x += self.through_end()**2*250
            self.white.blit(copy, (x, c.WINDOW_HEIGHT//2 - copy.get_height()//2))

        base_width = 125
        if black_width_factor > 0:
            width = base_width * black_width_factor
            each_bar_width = c.WINDOW_HEIGHT//2 - width//2
            if each_bar_width >= 1:
                rect_1 = (0, 0, c.WINDOW_WIDTH, each_bar_width)
                rect_2 = (0, c.WINDOW_HEIGHT - each_bar_width, c.WINDOW_WIDTH, each_bar_width)
                pygame.draw.rect(self.white, (0, 0, 0), rect_1)
                pygame.draw.rect(self.white, (0, 0, 0), rect_2)

        white_showing = (1 - self.through_end())**2
        self.white.set_alpha(white_showing * 255)
        if self.white.get_alpha() > 1:
            surf.blit(self.white, (0, 0))



        pass