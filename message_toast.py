from primitives import GameObject
import time
import constants as c

class MessageToast(GameObject):
    def __init__(self, game):
        super().__init__(game)
        self.messages = []

    def add_message(self, string):
        surf = self.game.message_toast_font.render(string, True, (255, 38, 74))
        self.messages.append((surf, time.time()))

    def update(self, dt, events):
        for message in self.messages[:]:
            age = time.time() - message[1]
            if age > 2:
                self.messages.remove(message)

    def draw(self, surf, offset=(0, 0)):
        for message in self.messages[:]:
            age = time.time() - message[1]
            alpha = (abs(1-(age/2)))**0.5 * 255
            msurf = message[0]
            y = c.WINDOW_HEIGHT - 35 - (age/2)**0.3 * 30 + offset[1]
            msurf.set_alpha(alpha)
            x = c.WINDOW_WIDTH//2 - msurf.get_width()//2
            self.game.web_log(f"XY: {(x, y)}")
            surf.blit(msurf, (c.WINDOW_WIDTH//2 - msurf.get_width()//2, y))