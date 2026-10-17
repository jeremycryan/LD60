import pygame

from primitives import GameObject
import constants as c


class Word(GameObject):
    PUNCTUATION = ".,;!?-():'\"[]"

    DEFAULT = 0
    HOVERED = 1
    DISABLED = 2
    SELECTED = 3
    COMPLETED = 4

    HIDER = 0
    SEEKER_HIDING_PHASE = 1
    SEEKER_SEEKING_PHASE = 2
    SEEK_OVER = 3

    def __init__(self, game, frame, collection, text):
        super().__init__(game)
        self.text = text
        self.prefix = self.get_prefix()
        self.suffix = self.get_suffix()
        self.inner_text = text.strip(self.PUNCTUATION)

        self.base_color = 0, 0, 0
        self.surf = self.game.word_font.render(text, True, self.base_color)
        self.target_position = self.position
        self.index = 0

        self.state = self.DEFAULT
        self.collection = collection
        self.modified_inner_text = self.inner_text
        self.locked_in = False
        self.seeker_state = Word.HIDER
        self.frame = frame
        self.revealed = False
        self.found = False
        self.unfound = False

    def has_been_changed(self):
        return self.inner_text.lower().strip() != self.modified_inner_text.lower().strip()

    def word_valid(self):
        return self.modified_inner_text != "" and self.has_been_changed()

    def set_index(self, idx):
        self.index = idx

    def reset_to_base_text(self):
        self.modified_inner_text = self.inner_text
        self.recalculate_display_text()
        self.regenerate_text_surface()
        self.collection.recalculate_word_splitting_behavior()
        self.collection.update_word_target_positions()

    def recalculate_display_text(self):
        self.text = self.prefix + self.modified_inner_text + self.suffix

    def regenerate_text_surface(self):
        self.recalculate_display_text()
        color = self.base_color
        if self.revealed:
            color = 150, 150, 150
        if self.found:
            color = 0, 255, 0
        if self.unfound:
            color = 255, 0, 255
        self.surf = self.game.word_font.render(self.text, True, color)

    def mouse_in_rect(self):
        mpos = pygame.mouse.get_pos()
        x, y, w, h = self.surf.get_rect()
        rect = pygame.Rect(
            x + self.position.x - w//2 - c.WORD_HOVER_MARGIN,
            y + self.position.y - h//2 - c.WORD_HOVER_MARGIN,
            w + c.WORD_HOVER_MARGIN * 2,
            h + c.WORD_HOVER_MARGIN * 2
        )
        if rect.collidepoint(mpos):
            return True
        return False


    def update_state(self, new_state):

        if self.state in (self.SELECTED, self.DISABLED, self.COMPLETED):
            if new_state not in (self.SELECTED, self.DISABLED, self.COMPLETED):
                self.reset_to_base_text()

        if new_state == self.DISABLED:
            self.collection.recalculate_word_splitting_behavior()
            self.collection.update_word_target_positions()


        if new_state == self.SELECTED:
            self.collection.deselect_all_words()
            self.modified_inner_text = ""
            self.on_select_new_word()

        self.state = new_state

    def update(self, dt, events):
        hovered = self.mouse_in_rect() and not self.locked_in and not self.seeker_state == self.SEEK_OVER
        if self.state == self.DEFAULT:
            if hovered:
                self.update_state(self.HOVERED)
                if self.game.is_seeker:
                    self.frame.on_seeker_hover(self.index)
        elif self.state == self.HOVERED:
            if not hovered:
                self.update_state(self.DEFAULT)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if hovered and not self.locked_in:
                        self.on_click()
            if event.type == pygame.KEYDOWN:
                self.on_keypress(event)

        self.update_position(dt)

    def update_position(self, dt):
        diff = self.target_position - self.position
        if diff.magnitude() < 2:
            self.position = self.target_position.copy()
        else:
            self.position += diff * dt * 15

    def on_keypress(self, event):
        if self.locked_in:
            return
        key = event.key
        character = event.unicode
        if self.state == self.SELECTED:
            modified = False
            if key is pygame.K_BACKSPACE:
                self.modified_inner_text = "" if len(self.modified_inner_text) <= 1 else self.modified_inner_text[:-1]
                modified = True
            else:
                if character in " ":
                    pass
                else:
                    self.modified_inner_text += character
                    modified = True
            if modified:
                self.regenerate_text_surface()
                self.collection.recalculate_word_splitting_behavior()
                self.collection.update_word_target_positions()

    def on_click_seeker(self):
        if self.seeker_state == Word.SEEKER_HIDING_PHASE or self.seeker_state == Word.SEEK_OVER:
            return

        if self.seeker_state == Word.SEEKER_SEEKING_PHASE:
            self.seeker_shoot_here()

    def seeker_shoot_here(self):
        if self.game.sprocket:
            self.game.sprocket.send(type="seeker_guess", word=self.index)
        self.frame.seeker_guess(self.index)

    def on_click(self):
        if self.seeker_state == Word.HIDER:
            if self.state == self.DEFAULT or self.state == self.HOVERED:
                self.update_state(self.SELECTED)
        else:
            self.on_click_seeker()

    def draw(self, surf, offset=(0, 0)):

        x = self.position.x + offset[0] - self.surf.get_width()//2
        y = self.position.y + offset[1] - self.surf.get_height()//2

        rect_color = (255, 0, 0)
        if self.state == self.HOVERED:
            rect_color = (0, 0, 0)
        elif self.state == self.SELECTED:
            rect_color = (128, 100, 0)
        elif self.state == self.DISABLED:
            rect_color = (0, 255, 0)

        if self.state in [self.DISABLED, self.SELECTED] or self.found or self.unfound:
            background = (0, 0, 0)
            if self.state == self.DISABLED:
                background = (128, 128, 128)
            if self.found:
                background = (140, 10, 50)
            if self.unfound:
                background = (50, 10, 140)
            pygame.draw.rect(surf, background, (x - c.WORD_HOVER_MARGIN, y - c.WORD_HOVER_MARGIN, self.width() + 2*c.WORD_HOVER_MARGIN, self.height() + 2*c.WORD_HOVER_MARGIN))
            surf.blit(self.game.word_font.render(self.text, True, c.WHITE), (x, y))
        else:
            surf.blit(self.surf, (x, y))

        if not self.state in [self.DEFAULT, self.DISABLED, self.SELECTED]:
            pygame.draw.rect(surf, rect_color, (x - c.WORD_HOVER_MARGIN, y - c.WORD_HOVER_MARGIN, self.width() + 2*c.WORD_HOVER_MARGIN, self.height() + 2*c.WORD_HOVER_MARGIN), width=2)

    def force_default_state(self):
        self.state = Word.DEFAULT

    def width(self):
        return self.surf.get_width()

    def height(self):
        return self.surf.get_height()

    def get_prefix(self):
        prefix = ""
        text_copy = self.text
        while text_copy and text_copy[0] in self.PUNCTUATION:
            prefix += text_copy[0]
            text_copy = text_copy[1:]
        return prefix

    def get_suffix(self):
        suffix = ""
        text_copy = self.text
        while text_copy and text_copy[-1] in self.PUNCTUATION:
            suffix = text_copy[-1] + suffix
            text_copy = text_copy[:-1]
        return suffix

    def lock_in(self, lock=True):
        self.locked_in = lock

    def on_select_new_word(self):
        if self.game.sprocket:
            self.game.sprocket.send(type="select_word", word=self.index)