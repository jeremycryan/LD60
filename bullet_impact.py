import pygame

from image_manager import ImageManager
from primitives import GameObject, Pose

class BulletImpact(GameObject):
    def __init__(self, game):
        super().__init__(game)
        self.impact_surf = ImageManager.load("images/impact.png")
        self.frame_count = 999
        self.bullet_mark = ImageManager.load("images/bullet_mark.png")
        self.since_shot = 999

    def update(self, dt, events):
        self.since_shot += dt

    def draw(self, surf, offset=(0, 0)):
        if self.frame_count == 0:
            surf.fill((0, 0, 0))
        elif self.frame_count == 1:
            x = self.position.x - self.impact_surf.get_width()//2
            y = self.position.y - self.impact_surf.get_height()//2
            surf.fill((255, 255, 255))
            surf.blit(self.impact_surf, (x, y))
        elif self.frame_count == 3:
            surf.fill((0, 0, 0))
        else:
            x = self.position.x - self.bullet_mark.get_width()//2
            y = self.position.y - self.bullet_mark.get_height()//2
            showing = max(0, (3 - self.since_shot)/3)
            self.bullet_mark.set_alpha(255 * (showing**3))
            surf.blit(self.bullet_mark, (x, y))

        self.frame_count += 1

    def impact_at(self, xy):
        self.position = Pose(xy)
        self.frame_count = 0
        self.since_shot = 0
        self.game.gunshot.play()