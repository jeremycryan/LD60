from primitives import GameObject
import pygame
import constants as c
from word import Word


class TextField(GameObject):
    WIDTH = 125

    def __init__(self, game):
        super().__init__(game)

        self.text = ""
        self.regenerate_text_surface()
        self.state = Word.DEFAULT

    def update(self, dt, events):
        hovered = self.mouse_in_rect()
        if self.state == Word.DEFAULT:
            if hovered:
                self.state = Word.HOVERED
        elif self.state == Word.HOVERED:
            if not hovered:
                self.state = Word.DEFAULT
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if hovered:
                        self.state = Word.SELECTED
                    else:
                        self.state = Word.DEFAULT
            if event.type == pygame.KEYDOWN:
                self.on_keypress(event)

    def on_keypress(self, event):
        key = event.key
        character = event.unicode.upper()
        if self.state == Word.SELECTED:
            modified = False
            if key is pygame.K_BACKSPACE:
                self.text = "" if len(self.text) <= 1 else self.text[:-1]
                modified = True
            else:
                if character in " " or len(self.text) >= 4:
                    pass
                else:
                    self.text += character
                    modified = True
            if modified:
                self.regenerate_text_surface()

    def mouse_in_rect(self):
        mpos = pygame.mouse.get_pos()
        x, y, w, h = self.surf.get_rect()
        w0 = w
        w = self.WIDTH
        rect = pygame.Rect(
            x + self.position.x - c.WORD_HOVER_MARGIN,
            y + self.position.y - h//2 - c.WORD_HOVER_MARGIN,
            w + c.WORD_HOVER_MARGIN * 2,
            h + c.WORD_HOVER_MARGIN * 2
        )
        if rect.collidepoint(mpos):
            return True
        return False

    def regenerate_text_surface(self):
        if self.text:
            self.surf = self.game.type_code_font.render(self.text, True, (255, 255, 255))
        else:
            self.surf = self.game.type_code_font.render("XXXX", True, (76, 69, 60))

    def draw(self, surf, offset=(0, 0)):
        x = self.position.x + offset[0]
        y = self.position.y + offset[1] - self.surf.get_height()//2
        surf.blit(self.surf, (x + self.WIDTH//2 - self.surf.get_width()//2, y + 2))

        rect_color = (0, 0, 0)
        if self.state == Word.HOVERED:
            rect_color = (255, 255, 255)
        elif self.state == Word.SELECTED:
            rect_color = (255, 255, 0)
        elif self.state == Word.DISABLED:
            rect_color = (0, 255, 0)
        pygame.draw.rect(surf, rect_color, (x - c.WORD_HOVER_MARGIN, y - c.WORD_HOVER_MARGIN, self.WIDTH + 2*c.WORD_HOVER_MARGIN, self.surf.get_height() + 2*c.WORD_HOVER_MARGIN), width=2)
