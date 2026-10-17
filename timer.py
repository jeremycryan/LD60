import math

from primitives import GameObject, scale_surface_by
import pygame
import pygame.gfxdraw

class Timer(GameObject):
    def __init__(self, game, start_time=45):
        super().__init__(game)
        self.start_time = start_time
        self.time = start_time
        self.last_shown_time = start_time
        self.text_surf = self.game.timer_font.render(f"{int(self.time)}", True, (255, 255, 255))
        self.started = False

    def update(self, dt, events):
        if self.started:
            self.time -= dt

        if self.time < 0:
            self.time = 0

        if int(self.time) != self.last_shown_time:
            self.last_shown_time = int(self.time)
            self.text_surf = self.game.timer_font.render(f"{int(self.time)}", True, (255, 255, 255))

    def percent_left(self):
        return self.time/self.start_time

    def has_run_out(self):
        return self.percent_left() < 0.001

    def remainder(self):
        return self.time % 1.0

    def start(self):
        print("START")
        self.started = True

    def calculate_scale(self):
        base = 0.7
        if not self.started:
            return base
        return (base + self.remainder()**3*0.5) * min(1, self.time**0.5)

    def draw(self, surf, offset=(0, 0)):
        x = self.position.x + offset[0]
        y = self.position.y + offset[1]

        pygame.draw.circle(surf, (50, 50, 50), (x, y), 35)
        draw_pie_slice(surf, x, y, 35, self.percent_left(), (50, 50, 175), (0, 0, 0))

        text_surf = scale_surface_by(self.text_surf, self.calculate_scale())
        surf.blit(text_surf, (x - text_surf.get_width()//2, y - text_surf.get_height()//2 + 4))


def draw_pie_slice(surf, x, y, radius, val, color, background_color):
    pygame.draw.circle(surf, background_color, (x, y), radius -1)
    angle = val*360
    p = [(x, y)]
    for n in range(0, int(angle)):
        xd = x + int(radius*math.cos(n*math.pi/180 - math.pi/2))
        yd = y+int(radius*math.sin(n*math.pi/180 - math.pi/2))
        p.append((xd, yd))
    p.append((x, y))
    if len(p) > 2:
        pygame.draw.polygon(surf, (color), p)