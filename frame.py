import pygame

from image_manager import ImageManager
from main import Game
from primitives import Pose
from seeker_crosshairs import SeekerCrosshairs
from seeker_shade import SeekerShade

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
        button_surf = pygame.Surface((410, 50))
        button_surf.fill((0, 255, 0))
        button_surf.set_alpha(0)
        self.create_room_button = Button(button_surf, (c.WINDOW_WIDTH//2 + 130, c.WINDOW_HEIGHT - 63), "Start Game", self.try_start_game, disabled_surf=button_surf,  hover_surf=ImageManager.load_copy("images/start_button_frame.png"))

        button_surf = pygame.Surface((230, 50))
        button_surf.fill((255, 0, 0))
        button_surf.set_alpha(0)
        self.leave_button = Button(button_surf, (c.WINDOW_WIDTH//2 - 430, c.WINDOW_HEIGHT - 63), "Leave Room", self.leave_room, hover_surf=ImageManager.load_copy("images/start_button_frame.png"))

        self.text = self.game.room_code_font.render(self.game.active_room, True, (0, 0, 0))
        self.canceled = False

        self.background = ImageManager.load("images/room_background.png")
        self.additive_overlay_1 = ImageManager.load("images/room_additive.png")
        self.additive_overlay_2 = ImageManager.load("images/lamp_add.png")
        self.age = 0

        self.current_players = [self.game.active_client_id]
        self.current_player_texts = []
        self.update_current_player_texts()

        self.leaving = False
        self.since_left = 0

        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))

    def update_current_player_texts(self):
        self.current_player_texts = []
        for player in self.current_players:
            name = f"{player}" # TODO get actual name
            text = self.game.player_list_font.render(name, True, (178, 192, 199))
            self.current_player_texts.append(text)

    def update(self, dt, events):
        self.create_room_button.update(dt, events)
        self.leave_button.update(dt, events)
        self.age += dt
        age_capped = min(1, self.age, 1 - self.since_left)
        self.showing = -(abs((age_capped-1)**3)) + 1

        if self.leaving:
            self.since_left += dt

        if self.since_left > 1:
            self.done = True

    def draw(self, surf, offset=(0, 0)):
        surf.fill((1, 15, 22))

        yoff = (1 - self.showing)*1200
        if self.leaving and not self.canceled:
            yoff *= -1
        offset = offset[0], offset[1] + yoff
        partial_offset = offset[0], offset[1]*1.25
        surf.blit(self.background, offset)
        surf.blit(self.text, (410 + offset[0], 123 + partial_offset[1]))
        #.blit(self.additive_overlay_1, (0, 0), special_flags=pygame.BLEND_ADD)
        surf.blit(self.additive_overlay_2, (offset[0] +854, offset[1] + 392) , special_flags=pygame.BLEND_ADD)

        self.create_room_button.draw(surf, *offset)
        self.leave_button.draw(surf, *offset)

        if len(self.current_players) < 2:
            self.create_room_button.disable()
        else:
            self.create_room_button.enable()

        x = 200
        y = 90
        for text in self.current_player_texts:
            surf.blit(text, (x + offset[0] - text.get_width()//2, y + offset[1] - text.get_height()//2))
            y += 38

        self.black.set_alpha(255 * (1 - self.showing)**2)
        if self.black.get_alpha() > 1:
            surf.blit(self.black, (0, 0))

    def try_start_game(self):
        self.game.sprocket.send(type="start_game")

    def leave_room(self):
        self.game.sprocket.send(type="leave_room")
        self.canceled = True
        self.leaving = True
        self.create_room_button.disable()
        self.leave_button.disable()

    def receive_packet(self, packet):
        if packet.get("type") == "start_game":
            if packet.get("seeker") == self.game.active_client_id:
                self.game.is_seeker = True
            else:
                self.game.is_seeker = False
            self.leaving = True
        if packet.get("type") == "text_choice":
            self.game.active_text_key = packet.get("text")
        if packet.get("type") == "category_options":
            self.game.category_options = packet.get("texts")
            if packet.get("seeker") == self.game.active_client_id:
                self.game.web_log(f"Becoming seeker! {packet}, {self.game.active_client_id}")
                self.game.is_seeker = True
            else:
                self.game.is_seeker = False
        if packet.get("type") == "room_list":
            self.current_players = packet.get("clients")
            self.update_current_player_texts()

    def next_frame(self):
        if not self.canceled:
            return CategorySelectFrame(self.game)
        else:
            return MainMenu(self.game)


class CategorySelectFrame(Frame):
    def __init__(self, game):
        super().__init__(game)

    def load(self):
        self.header = self.game.category_header_font.render("   You're seeking.\nChoose a category.", True, (150, 150, 150), )
        self.nonseeker_header = self.game.category_header_font.render("Waiting for seeker to\n  choose a category...", True, (150, 150, 150))

        self.buttons = []
        x = c.WINDOW_WIDTH//2
        y = c.WINDOW_HEIGHT//2 - 100
        for item in self.game.category_options:
            category_string = TextsManager.get_display_name_from_key(item)
            surf = pygame.Surface((300, 100))
            surf.set_alpha(0)
            self.buttons.append(Button(surf, (x, y), category_string, on_click=self.category_selected, on_click_args=[item]))
            if not self.game.is_seeker:
                self.buttons[-1].disable()
            y += 100

    def category_selected(self, key):
        if self.game.sprocket:
            self.game.sprocket.send(type="text_choice", text=key, i_think_i_am=self.game.active_client_id)
        self.done = True
        self.game.active_text_key = key

    def update(self, dt, events):
        for button in self.buttons:
            button.update(dt, events)

    def draw(self, surface, offset=(0, 0)):
        surface.fill((100, 100, 128))
        if self.game.is_seeker:
            surface.blit(self.header, (c.WINDOW_WIDTH//2 - self.header.get_width()//2, 50))
            for button in self.buttons:
                button.draw(surface, *offset)
        else:
            surface.blit(self.nonseeker_header, (c.WINDOW_WIDTH//2 - self.header.get_width()//2, 50))

    def receive_packet(self, packet):
        if packet.get("type") == "text_choice":
            self.game.active_text_key = packet.get("text")
            self.done = True

    def next_frame(self):
        return MainGameplayFrame(self.game)

class MainGameplayFrame(Frame):
    def __init__(self, game):
        super().__init__(game)
        self.active_text_key = ""
        self.display_text = ""
        self.all_players_locked_in = False
        self.age = 0
        self.since_all_players_locked_in = 0
        self.other_players_selected_words = {}
        self.answers = {}
        self.revealed = set()
        self.ammo = 3
        self.seek_over = False
        self.moving_to_next_frame = False
        self.since_last_crosshairs_message = 0

    def draw_ammo(self, surface, offset = (0, 0)):
        x = 10 + offset[0]
        y = 10 + offset[1]
        surf = pygame.Surface((10, 20))
        surf.fill(c.YELLOW)
        for i in range(self.ammo):
            surface.blit(surf, (x, y))
            x += 13

    def load(self):
        self.active_text_key = self.game.active_text_key
        self.display_text = TextsManager.get_text_from_key(self.active_text_key)
        self.word_collection = WordCollection(self.game, self, self.display_text)

        button_surf = pygame.Surface((100, 50))
        button_surf.fill((0, 255, 0))
        self.lock_in_button = Button(button_surf, (c.WINDOW_WIDTH - 130, c.WINDOW_HEIGHT - 80), "Lock In", self.lock_in_clicked)

        self.hiding_timer = Timer(self.game)
        self.hiding_timer.position = Pose((c.WINDOW_WIDTH - 70, 70))

        self.seeking_timer = Timer(self.game, start_time=60)
        self.seeking_timer.position = Pose((c.WINDOW_WIDTH - 70, 160))

        self.review_timer = Timer(self.game, start_time=20)
        self.review_timer.position = Pose((c.WINDOW_WIDTH - 70, 250))

        self.seeker_shade = SeekerShade(self.game)
        self.seeker_shade.set_visible(self.game.is_seeker)

        self.seeker_crosshairs = SeekerCrosshairs(self.game)
        self.seeker_crosshairs.position = Pose((-50, -50))

        if self.game.is_seeker:
            self.word_collection.set_word_seeker_status(Word.SEEKER_HIDING_PHASE)
            self.lock_in_button.x = 50000

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
            if self.since_all_players_locked_in > 2 and not self.seeking_timer.started:
                self.seeking_timer.start()
                self.seeker_shade.set_visible(visible=False)
                if self.game.is_seeker:
                    self.on_seeker_start()

        if (not self.game.is_seeker) or self.all_players_locked_in:
            self.word_collection.update(dt, events)


        self.lock_in_button.update(dt, events)
        self.hiding_timer.update(dt, events)
        self.seeking_timer.update(dt, events)
        self.review_timer.update(dt, events)

        if self.age > 2 and not self.hiding_timer.started:
            self.hiding_timer.start()


        if self.lock_in_button.enabled and self.hiding_timer.has_run_out():
            if self.can_lock_in():
                self.lock_in_clicked()
            else:
                if self.game.sprocket:
                    self.game.sprocket.send(type="hiding_timeout")
                self.word_collection.deselect_all_words()
                self.word_collection.lock_in(True)
            self.lock_in_button.disable()

        self.seeker_shade.update(dt, events)

        if self.review_timer.has_run_out() and not self.moving_to_next_frame:
            if self.game.is_seeker:
                self.moving_to_next_frame = True
                if self.game.sprocket:
                    self.game.sprocket.send(type="review_over")

        if not self.seek_over and self.seeking_timer.has_run_out():
            self.end_seeker_mode()

        self.seeker_crosshairs.update(dt, events)
        if self.game.is_seeker:
            if self.all_players_locked_in and self.seeking_timer.started and not self.seek_over:
                self.since_last_crosshairs_message += dt
                if self.since_last_crosshairs_message > 0.25:
                    self.since_last_crosshairs_message = 0
                    self.give_seeker_hovering_update()

    def on_seeker_start(self):
        self.word_collection.lock_in(False)
        self.word_collection.deselect_all_words()
        self.word_collection.force_all_words_default()
        self.word_collection.set_word_seeker_status(Word.SEEKER_SEEKING_PHASE)

    def draw(self, surface, offset=(0, 0)):
        surface.fill((225, 220, 217))

        self.word_collection.draw(surface, offset)
        self.lock_in_button.draw(surface, *offset)

        if self.all_players_locked_in:
            self.draw_ammo(surface, offset)

        self.seeker_shade.draw(surface, offset)
        self.hiding_timer.draw(surface, offset)
        self.seeking_timer.draw(surface, offset)
        self.review_timer.draw(surface, offset)

        if not self.seek_over:
            self.seeker_crosshairs.draw(surface, offset)

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
            self.answers = packet.get("answers")
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
        if packet.get("type") == "seeker_guess":
            self.seeker_guess(packet.get("word"))
        if packet.get("type") == "seek_over":
            self.on_end_seeker_mode()
        if packet.get("type") == "seeker_hover":
            word_idx = packet.get("word")
            self.show_seeker_hovering(word_idx)
        if packet.get("type") == "category_options":
            self.game.category_options = packet.get("texts")
            if packet.get("seeker") == self.game.active_client_id:
                self.game.web_log(f"Becoming seeker! {packet}, {self.game.active_client_id}")
                self.game.is_seeker = True
            else:
                self.game.is_seeker = False
            self.done = True

    def seeker_guess(self, index):
        if index in self.revealed:
            return
        if not self.ammo:
            return
        found = -1
        for client in self.answers:
            answer = self.answers[client]
            if answer and answer[0] == index:
                found = client
                break

        if found != -1:
            self.seeker_guess_success(index)
            self.answers.pop(found)
        else:
            self.seeker_guess_failure(index)

        if not self.ammo or not self.answers:
            self.end_seeker_mode()

    def seeker_guess_success(self, index):
        self.revealed.add(index)
        word = self.word_collection.word_index[index]
        word.revealed = True
        word.found = True
        word.reset_to_base_text()

    def seeker_guess_failure(self, index):
        self.ammo -= 1
        self.revealed.add(index)
        word = self.word_collection.word_index[index]
        word.revealed = True
        word.regenerate_text_surface()

    def end_seeker_mode(self):
        if self.game.sprocket:
            self.game.sprocket.send(type="seek_over")
        self.on_end_seeker_mode()

    def on_end_seeker_mode(self):
        self.seek_over = True
        self.word_collection.set_word_seeker_status(Word.SEEK_OVER)
        self.review_timer.start()
        self.seeking_timer.time = 0
        for client in self.answers:
            word_idx = self.answers[client][0]
            if word_idx not in self.word_collection.word_index:
                continue
            word = self.word_collection.word_index[word_idx]
            word.revealed = True
            word.unfound = True
            word.regenerate_text_surface()

    def next_frame(self):
        return CategorySelectFrame(self.game)

    def on_seeker_hover(self, word_idx):
        if self.game.is_seeker:
            self.show_seeker_hovering(word_idx)

    def give_seeker_hovering_update(self):
        return
        if not self.seeker_crosshairs.word_to_follow:
            return
        if self.game.sprocket:
            self.game.sprocket.send(type="seeker_hover", word=self.seeker_crosshairs.word_to_follow.index)

    def show_seeker_hovering(self, word_idx):
        if word_idx in self.word_collection.word_index and self.seeking_timer.started:
            word = self.word_collection.word_index[word_idx]
            self.seeker_crosshairs.word_to_follow = word






