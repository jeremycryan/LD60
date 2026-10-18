import math

from primitives import GameObject, scale_surface_by
import pygame
import pygame.gfxdraw
import constants as c

class Timer(GameObject):
    def __init__(self, game, start_time=45, invert_color = False):
        super().__init__(game)
        self.start_time = start_time
        self.time = start_time
        self.last_shown_time = start_time
        self.started = False
        self.invert_color = invert_color
        text_color = c.WHITE if self.invert_color else (0, 0, 0)
        self.text_surf = self.game.timer_font.render(f"{int(self.time)}", True, text_color)
        self.x_off = 120

    def update(self, dt, events):
        if self.started:
            self.time -= dt

        if self.time < 0:
            self.time = 0

        if int(self.time) != self.last_shown_time:
            self.last_shown_time = int(self.time)
            text_color = c.WHITE if self.invert_color else (0, 0, 0)
            self.text_surf = self.game.timer_font.render(f"{int(self.time)}", True, text_color)

        if self.started and not self.has_run_out():
            target = 0
        else:
            target = 110

        d = target - self.x_off
        self.x_off += 6*d*dt
        if self.x_off < 0:
            self.x_off = 0
        if self.x_off > 120:
            self.x_off = 120

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
        x = self.position.x + offset[0] + self.x_off
        y = self.position.y + offset[1]

        #pygame.draw.circle(surf, (50, 50, 50), (x, y), 35)
        color = (185, 185, 185) if not self.invert_color else (70, 70, 70)
        draw_pie_slice(surf, x, y, 35, self.percent_left(), color, (0, 0, 0, 0), invert_color=self.invert_color)

        text_surf = scale_surface_by(self.text_surf, self.calculate_scale())
        surf.blit(text_surf, (x - text_surf.get_width()//2, y - text_surf.get_height()//2 + 4))


def draw_pie_slice(surf, x, y, radius, val, color, background_color, invert_color = False):
    temp = pygame.Surface((2*radius, 2*radius))
    fill_color = c.WHITE if not invert_color else (0, 0, 0)
    temp.fill(fill_color)
    #pygame.draw.circle(surf, background_color, (x, y), radius -1)
    angle = val*360
    p = [(radius, radius)]
    for n in range(0, int(angle)):
        xd = radius + int(radius*math.cos(n*math.pi/180 - math.pi/2))
        yd = radius+int(radius*math.sin(n*math.pi/180 - math.pi/2))
        p.append((xd, yd))
    p.append((radius, radius))
    if len(p) > 2:
        pygame.draw.polygon(temp, (color), p)
    flag = pygame.BLEND_MULT if not invert_color else pygame.BLEND_ADD
    surf.blit(temp, (x - radius, y - radius), special_flags=flag)