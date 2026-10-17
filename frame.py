import pygame

from main import Game
from primitives import Pose

from texts_manager import TextsManager
from timer import Timer
from word import Word
from word_collection import WordCollection
from button import Button
import constants as c
from text_field import TextField


class Frame:
    def __init__(self, game):
        self.game = game
        self.done = False

    def load(self):
        pass

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        surface.fill((128, 128, 128))

    def next_frame(self):
        return Frame(self.game)

    def name(self):
        return self.__class__.__name__

    def receive_packet(self, packet):
        pass

class MainMenu(Frame):
    def __init__(self, game):
        super().__init__(game)
        self.room_code = ""
        self.hello_sent = False

    def load(self):
        button_surf = pygame.Surface((180, 50))
        button_surf.fill((0, 255, 0))
        self.create_room_button = Button(button_surf, (c.WINDOW_WIDTH - 130, c.WINDOW_HEIGHT - 80), "Create Room", self.try_create_room)

        button_surf = pygame.Surface((150, 50))
        button_surf.fill((0, 128, 200))
        self.join_room_button = Button(button_surf, (c.WINDOW_WIDTH - 320, c.WINDOW_HEIGHT - 80), "Join Room", self.try_join_room)

        self.join_text_field = TextField(self.game)
        self.join_text_field.position = Pose((c.WINDOW_WIDTH - 500, c.WINDOW_HEIGHT - 80))


    def update(self, dt, events):
        self.create_room_button.update(dt, events)
        self.join_room_button.update(dt, events)
        self.join_text_field.update(dt, events)

        if not self.hello_sent and self.game.sprocket is not None and self.game.sprocket.is_ready():
            self.game.sprocket.send(type="hello")
            self.hello_sent = True


    def draw(self, surf, offset=(0, 0)):
        surf.fill((0, 0, 0))
        self.create_room_button.draw(surf, *offset)
        self.join_room_button.draw(surf, *offset)
        self.join_text_field.draw(surf, offset)

    def has_connected(self):
        return self.hello_sent and self.game.active_client_id != -1

    def try_create_room(self):
        if not self.has_connected():
            return
        self.game.sprocket.send(type="new_room")

    def try_join_room(self):
        if not self.has_connected():
            return
        self.game.sprocket.send(type="join_room", code=self.join_text_field.text)

    def receive_packet(self, packet):
        if packet.get("type") == "new_room_success":
            self.game.active_room = packet.get("code")
            self.done = True
        elif packet.get("type") == "join_room_success":
            self.game.active_room = packet.get("code")
            self.done = True
        elif packet.get("type") == "hello":
            self.game.active_client_id = packet.get("client_id")

    def next_frame(self):
        return RoomFrame(self.game)


class RoomFrame(Frame):
    def load(self):
        self.game.sprocket.send(type="hello")
        button_surf = pygame.Surface((180, 50))
        button_surf.fill((0, 255, 0))
        self.create_room_button = Button(button_surf, (c.WINDOW_WIDTH//2 - 90, c.WINDOW_HEIGHT - 80), "Start Game", self.try_start_game)

        button_surf = pygame.Surface((180, 50))
        button_surf.fill((255, 0, 0))
        self.leave_button = Button(button_surf, (c.WINDOW_WIDTH//2 - 300, c.WINDOW_HEIGHT - 80), "Leave Room", self.leave_room)

        self.text = self.game.room_code_font.render(self.game.active_room, True, (0, 0, 0))
        self.canceled = False

    def update(self, dt, events):
        self.create_room_button.update(dt, events)
        self.leave_button.update(dt, events)

    def draw(self, surf, offset=(0, 0)):
        surf.fill((100, 180, 130))
        surf.blit(self.text, (400, 100))
        self.create_room_button.draw(surf, *offset)
        self.leave_button.draw(surf, *offset)

    def try_start_game(self):
        self.game.sprocket.send(type="start_game")

    def leave_room(self):
        self.game.sprocket.send(type="leave_room")
        self.done = True
        self.canceled = True

    def receive_packet(self, packet):
        if packet.get("type") == "start_game":
            self.done = True

    def next_frame(self):
        if not self.canceled:
            return MainGameplayFrame(self.game)
        else:
            return MainMenu(self.game)


class MainGameplayFrame(Frame):
    def __init__(self, game):
        super().__init__(game)
        self.active_text_key = ""
        self.display_text = ""
        self.all_players_locked_in = False
        self.age = 0
        self.since_all_players_locked_in = 0
        self.other_players_selected_words = {}

    def load(self):
        self.active_text_key = self.game.active_text_key
        self.display_text = TextsManager.get_text_from_key(self.active_text_key)
        self.word_collection = WordCollection(self.game, self.display_text)

        button_surf = pygame.Surface((100, 50))
        button_surf.fill((0, 255, 0))
        self.lock_in_button = Button(button_surf, (c.WINDOW_WIDTH - 130, c.WINDOW_HEIGHT - 80), "Lock In", self.lock_in_clicked)

        self.hiding_timer = Timer(self.game)
        self.hiding_timer.position = Pose((c.WINDOW_WIDTH - 70, 70))

        self.seeking_timer = Timer(self.game, start_time=60)
        self.seeking_timer.position = Pose((c.WINDOW_WIDTH - 70, 160))

    def lock_in_clicked(self):
        if self.can_lock_in():
            self.word_collection.lock_in()
            self.lock_in_button.disable()

    def can_lock_in(self):
        if not self.word_collection.can_lock_in():
            return False
        return True

    def undo_lock_in(self):
        self.word_collection.lock_in(False)
        self.lock_in_button.enable()

    def update(self, dt, events):
        self.age += dt
        if self.all_players_locked_in:
            self.since_all_players_locked_in += dt
            if self.since_all_players_locked_in > 2:
                self.seeking_timer.start()
        self.word_collection.update(dt, events)
        self.lock_in_button.update(dt, events)
        self.hiding_timer.update(dt, events)
        self.seeking_timer.update(dt, events)
        if self.age > 2 and not self.hiding_timer.started:
            self.hiding_timer.start()

        if self.lock_in_button.enabled and self.hiding_timer.has_run_out():
            if self.can_lock_in():
                self.lock_in_clicked()
            else:
                if self.game.sprocket:
                    self.game.sprocket.send(type="hiding_timeout")
            self.lock_in_button.disable()

    def draw(self, surface, offset=(0, 0)):
        surface.fill((100, 25, 25))

        self.word_collection.draw(surface, offset)
        self.lock_in_button.draw(surface, *offset)
        self.hiding_timer.draw(surface, offset)
        self.seeking_timer.draw(surface, offset)

    def on_all_players_locked_in(self):
        self.all_players_locked_in = True
        self.hiding_timer.time = min(1, self.hiding_timer.time)
        Game.web_log("All players locked in!")

    def other_player_select_word(self, client_id, idx, value=None):
        if client_id in self.other_players_selected_words:
            # Clear old
            word_idx = self.other_players_selected_words[client_id]
            if word_idx in self.word_collection.word_index:
                word = self.word_collection.word_index[word_idx]
                if word and word.state == Word.DISABLED:
                    word.update_state(Word.DEFAULT)
        if idx in self.word_collection.word_index:
            word = self.word_collection.word_index[idx]
            if word:
                if value:
                    word.modified_inner_text = value
                else:
                    word.reset_to_base_text()
                word.regenerate_text_surface()
                self.word_collection.recalculate_word_splitting_behavior()
                self.word_collection.update_word_target_positions()
                word.update_state(Word.DISABLED)
                self.other_players_selected_words[client_id] = idx

    def unselect(self):
        self.word_collection.deselect_all_words()

    def receive_packet(self, packet):
        if packet.get("type") == "all_locked_in":
            self.on_all_players_locked_in()
        if packet.get("type") == "lock_in_word_success":
            if packet.get("client_id") != self.game.active_client_id:
                self.other_player_select_word(packet.get("client_id"), packet.get("word"), packet.get("value"))
        if packet.get("type") == "select_word_success":
            if packet.get("client_id") != self.game.active_client_id:
                self.other_player_select_word(packet.get("client_id"), packet.get("word"))
        if packet.get("type") == "lock_in_word_fail":
            self.undo_lock_in()
        if packet.get("type") == "select_word_fail":
            self.unselect()
        if packet.get("type") == "hiding_timeout":
            self.other_player_select_word(packet.get("client"), -1)




