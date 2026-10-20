import time

import pygame

from bullet_impact import BulletImpact
from category_toast import CategoryToast
from image_manager import ImageManager
from main import Game
from message_toast import MessageToast
from primitives import Pose
from py_sprocket_web.web_sprocket import WebSprocket
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


class NameFrame(Frame):
    def __init__(self, game):
        super().__init__(game)
        self.background_color = 111, 104, 94

        self.age = 0
        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))

    def load(self):

        self.name_prompt = ImageManager.load("images/what_is_your_name.png")

        button_surf = pygame.Surface((250, 50))
        button_surf.fill((1, 15, 22))
        disabled_surf = button_surf.copy()
        disabled_surf.set_alpha(50)
        self.join_room_button = Button(button_surf, (c.WINDOW_WIDTH//2, c.WINDOW_HEIGHT//2 + 60), "Submit", self.try_submit_name, disabled_surf=disabled_surf)

        self.join_text_field = TextField(self.game)
        self.join_text_field.set_width(430)
        self.join_text_field.set_char_limit(15)
        self.join_text_field.position = Pose((c.WINDOW_WIDTH//2-self.join_text_field.WIDTH//2, c.WINDOW_HEIGHT//2 - 6))

        self.since_left = 0
        self.leaving = False


    def try_submit_name(self):
        name = self.join_text_field.text
        if not name:
            return
        self.game.ding.play()
        self.join_room_button.disable()
        self.game.username = name
        self.leaving = True

    def update(self, dt, events):
        self.join_room_button.update(dt, events)
        self.join_text_field.update(dt, events)

        self.age += dt
        if self.leaving:
            self.since_left += dt
        age_capped = min(1, self.age, 1 - self.since_left)
        self.showing = -(abs((age_capped-1)**3)) + 1

        if self.leaving and self.since_left > 1:
            self.game.piano_music.play(-1)
            self.game.music.play(-1)
            self.done = True

        if len(self.join_text_field.text) < 1:
            self.join_room_button.disable()
        elif not self.leaving:
            self.join_room_button.enable()



    def draw(self, surf, offset=(0, 0)):

        yoff = (1 - self.showing)*1200
        if self.leaving:
            yoff *= -1
        offset = offset[0], offset[1] + yoff

        surf.fill(self.background_color)
        surf.blit(self.name_prompt, (offset[0] - self.name_prompt.get_width()//2 + c.WINDOW_WIDTH//2, offset[1] + c.WINDOW_HEIGHT//2 - 75))
        self.join_room_button.draw(surf, offset[0], offset[1])
        self.join_text_field.draw(surf, (offset[0], offset[1]))

        self.black.set_alpha(255 * (1 - self.showing)**2)
        if self.leaving:
            self.black.set_alpha(0)
        if self.black.get_alpha() > 1:
            surf.blit(self.black, (0, 0))

    def receive_packet(self, packet):
        pass

    def next_frame(self):
        return MainMenu(self.game)

class MainMenu(Frame):
    def __init__(self, game):
        super().__init__(game)
        self.room_code = ""
        self.hello_sent = False

        self.top_back_color = 111, 104, 94
        self.bottom_back_color = 25, 18, 8
        self.first_load = False

        self.age = 0
        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))

    def load(self):
        self.first_load = not self.game.main_menu_has_loaded
        self.game.main_menu_has_loaded = True
        button_surf = pygame.Surface((250, 50))
        button_surf.fill((1, 15, 22))
        disabled_surf = button_surf.copy()
        disabled_surf.set_alpha(50)
        self.create_room_button = Button(button_surf, (175, 184), "Create Room", self.try_create_room, disabled_surf=disabled_surf)

        button_surf = pygame.Surface((250, 50))
        button_surf.fill((1, 15, 22))
        disabled_surf = button_surf.copy()
        disabled_surf.set_alpha(50)
        self.join_room_button = Button(button_surf, (1113, 184), "Join Room", self.try_join_room, disabled_surf=disabled_surf)

        self.join_text_field = TextField(self.game)
        self.join_text_field.position = Pose((1113-self.join_text_field.WIDTH//2, 115))

        self.background = ImageManager.load_copy("images/typewriter.png")
        self.since_left = 0
        self.leaving = False

        self.disconnected = False
        if self.game.sprocket is None or not self.game.sprocket.is_ready():
            self.disconnected = True

        self.error = ImageManager.load("images/error.png")


    def update(self, dt, events):
        self.create_room_button.update(dt, events)
        self.join_room_button.update(dt, events)
        self.join_text_field.update(dt, events)

        if not self.hello_sent and self.game.sprocket is not None and self.game.sprocket.is_ready():
            self.game.sprocket.send(type="hello")
            self.hello_sent = True

        self.age += dt
        if self.leaving:
            self.since_left += dt
        age_capped = min(1, self.age, 1 - self.since_left)
        self.showing = -(abs((age_capped-1)**3)) + 1

        if self.leaving and self.since_left > 1:
            self.done = True

        if self.disconnected:
            self.join_room_button.disable()
            self.create_room_button.disable()
        else:
            if len(self.join_text_field.text) < 4:
                self.join_room_button.disable()
            elif not self.leaving:
                self.join_room_button.enable()



    def draw(self, surf, offset=(0, 0)):

        yoff = (1 - self.showing)*1200
        if not self.first_load or self.leaving:
            yoff *= -1
        offset = offset[0], offset[1] + yoff

        if self.first_load and yoff > 0:
            surf.fill(self.top_back_color)
        else:
            surf.fill(self.bottom_back_color)

        surf.blit(self.background, offset)
        self.create_room_button.draw(surf, offset[0], offset[1]*1.25)
        self.join_room_button.draw(surf, offset[0], offset[1]*1.25)
        self.join_text_field.draw(surf, (offset[0], offset[1]*1.25))

        if self.disconnected:
            surf.blit(self.error, (offset[0] + c.WINDOW_WIDTH//2 - self.error.get_width()//2, offset[1]))

        self.black.set_alpha(255 * (1 - self.showing)**2)
        if self.first_load and not self.leaving:
            self.black.set_alpha(0)
        if self.black.get_alpha() > 1:
            surf.blit(self.black, (0, 0))

    def has_connected(self):
        return self.hello_sent and self.game.active_client_id != -1

    def try_create_room(self):
        if not self.has_connected():
            return
        self.game.sprocket.send(type="new_room", username=self.game.username)

    def try_join_room(self):
        if not self.has_connected():
            return
        self.game.ding.play()
        self.game.sprocket.send(type="join_room", code=self.join_text_field.text, username=self.game.username)

    def receive_packet(self, packet):
        if packet.get("type") == "new_room_success":
            self.game.active_room = packet.get("code")
            self.leaving = True
            self.create_room_button.disable()
        elif packet.get("type") == "join_room_success":
            self.game.active_room = packet.get("code")
            self.leaving = True
            self.join_room_button.disable()
        elif packet.get("type") == "hello":
            self.game.active_client_id = packet.get("client_id")
        if packet.get("type") == "room_list":
            self.game.current_players = packet.get("clients")
            self.game.username_dict = packet.get("usernames")
            if self.game.username_dict == None:
                self.game.username_dict = {}
            self.game.username_dict = {int(key): self.game.username_dict[key] for key in self.game.username_dict}

    def next_frame(self):
        return RoomFrame(self.game)




class RoomFrame(Frame):
    def load(self):
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

        if not self.game.current_players:
            self.game.current_players = [self.game.active_client_id]
        self.current_player_texts = []
        self.update_current_player_texts()

        self.leaving = False
        self.since_left = 0

        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))

    def update_current_player_texts(self):
        self.current_player_texts = []
        self.game.web_log(f"Username dict: {self.game.username_dict} | players: {self.game.current_players}")
        for player in self.game.current_players:
            if player in self.game.username_dict:
                name = self.game.username_dict[player]
            else:
                name = f"Player {player}" # TODO get actual name
            text = self.game.player_list_font.render(name, True, (178, 192, 199))
            self.current_player_texts.append(text)

    def update(self, dt, events):
        self.create_room_button.update(dt, events)
        self.leave_button.update(dt, events)
        self.age += dt
        age_capped = min(1, self.age, 1 - self.since_left)
        self.showing = -(abs((age_capped-1)**3)) + 1

        self.game.balance_toward = self.showing

        if self.leaving:
            self.since_left += dt

        if self.since_left > 1:
            self.done = True
            if not self.canceled:
                self.game.set_target_balance(-1)
                self.game.music.fadeout(1000)
                self.game.piano_music.fadeout(1000)

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

        if len(self.game.current_players) < 2:
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
            self.game.seeker = int(packet.get("seeker"))
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
            self.game.seeker = int(packet.get("seeker"))
        if packet.get("type") == "room_list":
            self.game.current_players = packet.get("clients")
            self.game.username_dict = packet.get("usernames")
            if self.game.username_dict == None:
                self.game.username_dict = {}
            self.game.username_dict = {int(key): self.game.username_dict[key] for key in self.game.username_dict}
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
        self.header = self.game.category_header_font.render("You're seeking next.\n Choose a category.", True, (101, 99, 127), )
        seeker_num = self.game.seeker
        if seeker_num in self.game.username_dict:
            seeker_name = self.game.username_dict[seeker_num]
        else:
            seeker_name = f"Player {seeker_num}"
        self.nonseeker_headers = [self.game.player_list_font.render(f"Waiting for {seeker_name} to choose a category." + ("."* i), True, (200, 200, 200)) for i in range(3)]

        self.buttons = []
        x = c.WINDOW_WIDTH//2
        y = c.WINDOW_HEIGHT//2
        for item in self.game.category_options:
            category_string = TextsManager.get_display_name_from_key(item)
            hover = ImageManager.load("images/category_select_hover.png")
            surf = hover.copy()
            surf.set_alpha(0)
            self.buttons.append(Button(surf, (x, y), category_string, on_click=self.category_selected, on_click_args=[item], hover_surf=hover))
            if not self.game.is_seeker:
                self.buttons[-1].disable()
            y += 70
        self.age = 0
        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))
        self.since_leave = 0
        self.leaving = False
        self.background = ImageManager.load("images/category_select_background.png")



    def category_selected(self, key):
        if self.leaving:
            return
        if self.game.sprocket:
            self.game.sprocket.send(type="text_choice", text=key, i_think_i_am=self.game.active_client_id)
        self.leaving = True
        self.game.active_text_key = key
        for button in self.buttons:
            button.disable()

    def update(self, dt, events):
        if self.game.is_seeker:
            for button in self.buttons:
                button.update(dt, events)
        self.age += dt
        if self.leaving:
            self.since_leave += dt
            if self.since_leave > 1:
                self.done = True

    def draw(self, surface, offset=(0, 0)):
        if self.game.is_seeker:
            surface.blit(self.background, (0, 0))
            surface.blit(self.header, (c.WINDOW_WIDTH//2 - self.header.get_width()//2, 150))
            for button in self.buttons:
                button.draw(surface, *offset)
        else:
            surface.fill((0, 0, 0))
            header_idx = int(time.time()*3) % 3
            header = self.nonseeker_headers[header_idx]
            surface.blit(header, (c.WINDOW_WIDTH//2 - header.get_width()//2, c.WINDOW_HEIGHT//2 - header.get_height()//2))

        black_showing = max(0, 1 - self.age, self.since_leave)
        self.black.set_alpha(255*black_showing)
        if self.black.get_alpha() > 1:
            surface.blit(self.black, (0, 0))

    def receive_packet(self, packet):
        if packet.get("type") == "text_choice":
            self.game.active_text_key = packet.get("text")
            self.leaving = True

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
        self.found_words = {}
        self.revealed = set()
        self.ammo = 3
        self.starting_ammo = self.ammo
        self.seek_over = False
        self.since_seek_over = 0
        self.moving_to_next_frame = False
        self.since_last_crosshairs_message = 0
        self.skip_category_select = False

    def draw_ammo(self, surface, offset = (0, 0)):
        x = 20 + offset[0]
        y = 20 + offset[1] - (1 - self.ammo_showing)**2*300
        for i in range(self.starting_ammo):
            if i < self.ammo:
                surface.blit(self.bullet, (x, y))
            else:
                surface.blit(self.used_bullet, (x, y))
            y += self.bullet.get_height() + 2


    def load(self):
        self.active_text_key = self.game.active_text_key
        self.display_text = TextsManager.get_text_from_key(self.active_text_key)
        self.word_collection = WordCollection(self.game, self, self.display_text)

        button_surf = pygame.Surface((160, 50))
        button_surf.fill((84, 96, 60))
        disabled_button = button_surf.copy()
        disabled_button.set_alpha(80)
        self.lock_in_button = Button(button_surf, (c.WINDOW_WIDTH - 130, c.WINDOW_HEIGHT - 80), "Lock In", self.lock_in_clicked, disabled_surf=disabled_button)

        self.hiding_timer = Timer(self.game, start_time=60, invert_color=self.game.is_seeker)
        self.hiding_timer.position = Pose((c.WINDOW_WIDTH - 70, 70))

        self.seeking_timer = Timer(self.game, start_time=60)
        self.seeking_timer.position = Pose((c.WINDOW_WIDTH - 70, 70))

        self.review_timer = Timer(self.game, start_time=20)
        self.review_timer.position = Pose((c.WINDOW_WIDTH - 70, 70))

        self.seeker_shade = SeekerShade(self.game)
        self.seeker_shade.set_visible(self.game.is_seeker)

        self.seeker_crosshairs = SeekerCrosshairs(self.game)
        self.seeker_crosshairs.position = Pose((-50, -50))

        if self.game.is_seeker:
            self.word_collection.set_word_seeker_status(Word.SEEKER_HIDING_PHASE)
            self.lock_in_button.x = 50000

        self.category_toast = CategoryToast(self.game, TextsManager.get_display_name_from_key(self.game.active_text_key), self.game.active_text_key)

        self.lock_in_button_showing = 1
        self.ammo_showing = 0

        self.paper = ImageManager.load("images/paper.png")
        self.bullet = ImageManager.load("images/bullet.png")
        self.used_bullet = self.bullet.copy()
        self.used_bullet.set_alpha(80)

        self.bullet_impact = BulletImpact(self.game)
        self.hide_warning = ImageManager.load("images/hide_instructions.png")
        self.hide_warning_y = 0

        self.next_round = ImageManager.load("images/next_round.png")
        self.next_round_x = c.WINDOW_WIDTH

        self.lock_in_button.disable()
        self.hiding_timer_run_out_flag = False

        self.message_toast = MessageToast(self.game)

        self.was_seeker_at_start = self.game.is_seeker

    def lock_in_clicked(self):
        if self.can_lock_in():
            self.game.shake(7)
            self.word_collection.lock_in()
            self.lock_in_button.disable()
            self.game.ding.play()

    def can_lock_in(self):
        if not self.word_collection.can_lock_in():
            return False
        return True

    def undo_lock_in(self):
        self.word_collection.lock_in(False)
        self.lock_in_button.enable()

    def update(self, dt, events):
        self.age += dt
        self.category_toast.update(dt, events)
        self.message_toast.update(dt, events)

        if self.all_players_locked_in:
            self.since_all_players_locked_in += dt
            if self.since_all_players_locked_in > 2 and not self.seeking_timer.started:
                self.seeking_timer.start()
                self.game.seeking_music.play()
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
            self.game.hiding_music.play()


        if self.hiding_timer.has_run_out() and not self.hiding_timer_run_out_flag and not self.was_seeker_at_start:
            if self.can_lock_in() and self.lock_in_button.enabled:
                self.lock_in_clicked()
            elif not self.word_collection.locked_in:
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

        if self.since_all_players_locked_in < 1.5:
            self.lock_in_button_showing += 3*dt
            if self.lock_in_button_showing > 1:
                self.lock_in_button_showing = 1
        else:
            self.lock_in_button_showing -= 3*dt
            if self.lock_in_button_showing < 0:
                self.lock_in_button_showing = 0

        if self.since_all_players_locked_in > 3 and not self.seek_over:
            self.ammo_showing += 3*dt
            if self.ammo_showing > 1:
                self.ammo_showing = 1
        else:
            self.ammo_showing -= 3*dt
            if self.ammo_showing < 0:
                self.ammo_showing = 0

        self.bullet_impact.update(dt, events)
        if self.all_players_locked_in:
            self.hide_warning_y -= 800*dt
        if self.review_timer.started:
            self.next_round_x -= 500*dt
            if self.next_round_x < c.WINDOW_WIDTH - self.next_round.get_width():
                self.next_round_x = c.WINDOW_WIDTH - self.next_round.get_width()

        if self.seek_over:
            self.since_seek_over += dt
            if self.since_seek_over > 2:
                self.review_timer.start()

    def on_seeker_start(self):
        self.word_collection.lock_in(False)
        self.word_collection.deselect_all_words()
        self.word_collection.force_all_words_default()
        self.word_collection.set_word_seeker_status(Word.SEEKER_SEEKING_PHASE)

    def draw(self, surface, offset=(0, 0)):
        surface.blit(self.paper, (0, 0))
        if (self.hide_warning_y > -300 and not self.game.is_seeker):
            surface.blit(self.hide_warning, (offset[0], self.hide_warning_y + offset[1]))
        if self.next_round_x < c.WINDOW_WIDTH:
            surface.blit(self.next_round, (self.next_round_x, 0))


        self.word_collection.draw(surface, offset)
        self.lock_in_button.draw(surface, offset[0], offset[1] + 300*(1 - self.lock_in_button_showing)**2)



        if self.all_players_locked_in:
            self.draw_ammo(surface, offset)

        self.seeker_shade.draw(surface, offset)
        self.hiding_timer.draw(surface, offset)
        self.seeking_timer.draw(surface, offset)
        self.review_timer.draw(surface, offset)

        if not self.seek_over:
            pass
            #self.seeker_crosshairs.draw(surface, offset)

        self.message_toast.draw(surface, offset)

        self.category_toast.draw(surface, offset)
        self.bullet_impact.draw(surface, offset)

    def on_all_players_locked_in(self):
        self.all_players_locked_in = True
        self.hiding_timer.time = min(1, self.hiding_timer.time)
        Game.web_log("All players locked in!")
        self.game.hiding_music.fadeout(1000)


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
            self.game.seeker = int(packet.get("seeker"))
            self.done = True

        if packet.get("type") == "text_choice" and self.seek_over:
            self.game.active_text_key = packet.get("text")
            self.done = True
            self.skip_category_select = True

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
            if index in self.word_collection.word_index:
                word = self.word_collection.word_index[index]
                self.found_words[index] = word.modified_inner_text
                word.owner = int(found)

                if word.owner in self.game.username_dict:
                    found_name = self.game.username_dict[word.owner]
                    if self.game.seeker in self.game.username_dict:
                        seeker_name = self.game.username_dict[self.game.seeker]
                        self.message_toast.add_message(f"{seeker_name} FOUND {found_name}!")
            self.seeker_guess_success(index)
            self.answers.pop(found)
        else:
            self.seeker_guess_failure(index)

        if not self.ammo or not self.answers:
            self.end_seeker_mode()

        if index in self.word_collection.word_index:
            word = self.word_collection.word_index[index]
            self.bullet_impact.impact_at(word.position.get_position())
        self.game.shake(20)

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
        self.game.seeking_music.fadeout(1000)

    def on_end_seeker_mode(self):
        self.seek_over = True
        self.word_collection.set_word_seeker_status(Word.SEEK_OVER)
        self.seeking_timer.time = 0
        for client in self.answers:
            word_idx = self.answers[client][0]
            if word_idx not in self.word_collection.word_index:
                continue
            word = self.word_collection.word_index[word_idx]
            word.revealed = True
            word.unfound = True
            word.owner = int(client)
            word.regenerate_text_surface()

    def next_frame(self):
        if self.skip_category_select:
            return MainGameplayFrame(self.game)
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






