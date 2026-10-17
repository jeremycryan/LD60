from primitives import GameObject, Pose
from word import Word
import constants as c

class WordCollection(GameObject):
    def __init__(self, game, text):
        super().__init__(game)
        self.text = text
        self.text_lines = self.text.split("\n")
        self.words = [
            [
                Word(self.game, self, word) for word in line.split()
            ]
            for line in self.text_lines
        ]
        self.word_index = {}
        self.index_words()
        self.split_long_lines()
        self.update_word_target_positions()
        self.snap_word_positions_to_target()
        self.locked_in = False


    def recalculate_word_splitting_behavior(self):
        self.words = [
            [
                None for _ in line.split()
            ]
            for line in self.text_lines
        ]
        idx = 0
        for line in self.words:
            for i, _ in enumerate(line[:]):
                line[i] = self.word_index[idx]
                idx += 1
        self.split_long_lines()

    def index_words(self):
        idx = 0
        for line in self.words:
            for word in line:
                word.index = idx
                self.word_index[idx] = word
                idx += 1

    def split_long_lines(self):
        words_updated = []
        for line in self.words:
            width = 0
            new_line = []
            for word in line:
                width += word.width()
                if width > c.MAXIMUM_LINE_WIDTH and new_line:
                    words_updated.append(new_line)
                    new_line = [word]
                    width = word.width() + c.SPACE_WIDTH
                    continue
                new_line.append(word)
                width += c.SPACE_WIDTH
            words_updated.append(new_line)
        self.words = words_updated


    def update_word_target_positions(self):
        y = c.WINDOW_HEIGHT//2 - c.LINE_HEIGHT * (len(self.words) - 1)//2
        for line in self.words:
            total_width = sum([word.width() for word in line])
            total_width += c.SPACE_WIDTH * (len(line) - 1)
            x = c.WINDOW_WIDTH//2 - total_width//2
            for word in line:
                my_x = x + word.width()//2
                word.target_position = Pose((my_x, y))
                x += word.width() + c.SPACE_WIDTH
            y += c.LINE_HEIGHT


    def snap_word_positions_to_target(self):
        for line in self.words:
            for word in line:
                word.position = word.target_position.copy()

    def update(self, dt, events):
        for line in self.words:
            for word in line:
                word.update(dt, events)

    def draw(self, surf, offset=(0, 0)):
        for line in self.words:
            for word in line:
                word.draw(surf, offset)

    def deselect_all_words(self):
        for line in self.words:
            for word in line:
                if word.state == Word.SELECTED:
                    word.update_state(Word.DEFAULT)

    def lock_in(self, lock = True):
        has_locked_in_word = False
        for word in self.word_index.values():
            if word.state == Word.SELECTED and lock and not has_locked_in_word:
                word.update_state(Word.DISABLED)
                self.on_lock_in_word(word)
                has_locked_in_word = True
            word.lock_in(lock)
        self.locked_in = lock

    def on_lock_in_word(self, word):
        if self.game.sprocket:
            self.game.sprocket.send(type="lock_in_word", word=word.index, value=word.modified_inner_text)

    def can_lock_in(self):
        selected = [word for word in self.word_index.values() if word.state == Word.SELECTED]
        if len(selected) == 0:
            print("NOT")
            return False
        if not selected[0].word_valid():
            print("VALID")
            return False
        return True



