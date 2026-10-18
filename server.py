from py_sprocket_web.packet import Packet
from py_sprocket_web.web_servo import WebServo
import time
import pygame
import constants as c
import random

from texts_manager import TextsManager


class Server:
    class Room:
        STATE_LOBBY = 0
        STATE_SELECTING_TEXT = 1
        STATE_PLAYING = 2
        STATE_REVIEW = 3

        def __init__(self, join_code):
            self.state = self.STATE_LOBBY
            self.join_code = join_code
            self.clients = []
            self.selected_words = {}
            self.locked_in_words = {}
            self.hiding_timed_out_clients = set()
            self.client_usernames = {}

        def on_round_start(self):
            self.clear_word_state()
            self.clients.append(self.clients.pop(0))
            self.seeker = self.clients[0]
            print(f"ROUND START! NEW SEEKER: {self.clients[0]}")

        def on_game_start(self):
            self.clear_word_state()
            random.shuffle(self.clients)

        def add_client(self, client, username=""):
            self.clients.append(client)
            self.client_usernames[client] = username

        def remove_client(self, client):
            self.clients.remove(client)
            if client in self.client_usernames:
                self.client_usernames.pop(client)

        def time_out_client(self, client):
            self.hiding_timed_out_clients.add(client)

        def set_selected_word(self, client_id, word_index):
            if client_id in self.selected_words:
                self.selected_words.pop(client_id)
            for index in self.selected_words.values():
                if index == word_index:
                    return False # Collision
            self.selected_words[client_id] = word_index
            return True

        def set_locked_in_word(self, client_id, word_index, word_string):
            for index, string in self.locked_in_words.values():
                if index == word_index:
                    return False # Collision
            self.locked_in_words[client_id] = (word_index, word_string)
            return True

        def clear_word_state(self):
            self.locked_in_words = {}
            self.selected_words = {}
            self.hiding_timed_out_clients = set()

        def all_players_locked_in(self):
            for client in self.clients:
                if client in self.locked_in_words:
                    continue
                if client in self.hiding_timed_out_clients:
                    continue
                if client is self.seeker:
                    continue
                # Client must be hiding and not done yet
                return False
            return True

    def __init__(self):
        self.servo = WebServo("localhost", 60000)
        self.servo.start()
        self.clock = pygame.time.Clock()
        self.rooms = {}
        self.client_id_to_room = {}

        self.main()

    def main(self):
        TextsManager.init()
        while True:
            packets = self.servo.get()

            for packet in packets:
                self.process_packet(packet)

            self.check_for_disconnections()

            self.clock.tick(60)

    def check_for_disconnections(self):
        for client in list(self.client_id_to_room.keys()):
            if self.servo.client_is_disconnected(client):
                self.handle_disconnect(client)

    def handle_disconnect(self, client):
        if client in self.client_id_to_room:
            room = self.rooms[self.client_id_to_room[client]]
            self.client_id_to_room.pop(client)
            if client in room.clients:
                room.remove_client(client)
            if not room.clients:
                self.rooms.pop(room.join_code)
            else:
                self.send_client_disconnect(room.join_code, client)

    def process_packet(self, packet):
        client = packet.get(Packet.CLIENT_ID_KEY)
        if packet.get("type") == "hello":
            self.servo.send(client, type="hello", client_id=client)
        if packet.get("type") == "new_room":
            if client not in self.client_id_to_room:
                room = self.create_new_room()
                self.add_client_to_room(client, room.join_code, username=packet.get("username"))
                self.servo.send(client, type="new_room_success", code=room.join_code)
                self.send_room_list(room.join_code)
            else:
                self.servo.send(client, type="new_room_fail")
        if packet.get("type") == "join_room":
            code = packet.get("code")
            username = packet.get("username")
            if self.add_client_to_room(client, code, username=username):
                self.servo.send(client, type="join_room_success", code=code)
                self.send_room_list(code)
            else:
                self.servo.send(client, type="join_room_fail")

        # Everything below here requires you to be in a room
        if client not in self.client_id_to_room:
            return
        room_code = self.client_id_to_room[client]
        room = self.rooms[room_code]
        if packet.get("type") == "start_game":
            if len(room.clients) < 2:
                self.send_to_all_clients_in_room(room_code, Packet(type="start_game_fail"))
            elif room.state == Server.Room.STATE_LOBBY:
                room.state = Server.Room.STATE_PLAYING # TODO go to selection first
                room.on_game_start()
                room.on_round_start()
                texts = TextsManager.get_random_keys_no_overlap(3)
                self.send_to_all_clients_in_room(room_code, Packet(type="category_options", texts=texts, seeker=room.seeker))
                self.send_to_all_clients_in_room(room_code, Packet(type="start_game", seeker=room.seeker))
        if packet.get("type") == "leave_room":
            self.handle_disconnect(client)
            self.send_room_list(room_code)

        if packet.get("type") == "lock_in_word":
            if room.set_locked_in_word(client, packet.get("word"), packet.get("value")):
                self.send_to_all_clients_in_room(room_code,
                                                 Packet(type="lock_in_word_success",
                                                        word=packet.get("word"),
                                                        value=packet.get("value"),
                                                        client_id=client))
                if room.all_players_locked_in():
                    self.send_all_players_locked_in(room_code)
            else:
                client.send_packet(type="lock_in_word_fail")
        if packet.get("type") == "select_word":
            if room.set_selected_word(client, packet.get("word")):
                self.send_to_all_clients_in_room(room_code,
                                                 Packet(type="select_word_success",
                                                        word=packet.get("word"),
                                                        client_id=client),
                                                 )
            else:
                client.send_packet(type="select_word_fail")
        if packet.get("type") == "hiding_timeout":
            room.time_out_client(client)
            self.send_to_all_clients_in_room_but(room_code, Packet(type="hiding_timeout", client=client), client)
            if room.all_players_locked_in():
                self.send_all_players_locked_in(room_code)
        if packet.get("type") == "seeker_guess":
            self.send_to_all_clients_in_room_but(room_code, Packet(type="seeker_guess", word=packet.get("word")), client)
        if packet.get("type") == "seek_over":
            room.state = Server.Room.STATE_REVIEW
            self.send_to_all_clients_in_room_but(room_code, Packet(type="seek_over"), client)
        if packet.get("type") == "review_over":
            if room.state != Server.Room.STATE_SELECTING_TEXT:
                room.state = Server.Room.STATE_SELECTING_TEXT
                room.on_round_start()
                texts = TextsManager.get_random_keys_no_overlap(3)
                self.send_to_all_clients_in_room(room_code, Packet(type="category_options",
                                                                   texts=texts,
                                                                   seeker=room.seeker))
        if packet.get("type") == "seeker_hover":
            self.send_to_all_clients_in_room_but(room_code, Packet(type="seeker_hover", word=packet.get("word")), client)
        if packet.get("type") == "text_choice":
            self.send_to_all_clients_in_room_but(room_code, Packet(type="text_choice", text=packet.get("text")),
                                                 client)

    def send_all_players_locked_in(self, room_code):
        answers = self.rooms[room_code].locked_in_words
        self.send_to_all_clients_in_room(room_code, Packet(type="all_locked_in", answers=answers))

    def send_room_list(self, room_code):
        if room_code not in self.rooms:
            return
        usernames = self.rooms[room_code].client_usernames
        print(f"Usernames: {usernames}")
        packet = Packet(type="room_list", clients=self.rooms[room_code].clients, usernames=usernames)
        self.send_to_all_clients_in_room(room_code, packet)

    def send_client_disconnect(self, room_code, client):
        if room_code not in self.rooms:
            return
        packet = Packet(type="client_disconnect", cliend_id=client, clients=self.rooms[room_code].clients)
        self.send_to_all_clients_in_room(room_code, packet)

    def send_to_all_clients_in_room(self, room_code, packet):
        if room_code not in self.rooms:
            return False
        for client in self.rooms[room_code].clients:
            self.servo.send(client, **packet.__dict__)

    def send_to_all_clients_in_room_but(self, room_code, packet, client_id):
        if room_code not in self.rooms:
            return False
        for client in self.rooms[room_code].clients:
            if client == client_id:
                continue
            self.servo.send(client, **packet.__dict__)

    def add_client_to_room(self, client_id, room_code, username=""):
        if client_id in self.client_id_to_room:
            return False
        if room_code not in self.rooms:
            return False
        if username is None:
            username = ""
        room = self.rooms[room_code]
        if room.state != Server.Room.STATE_LOBBY:
            return False # Can't late join
        self.client_id_to_room[client_id] = room_code
        self.rooms[room_code].add_client(client_id, username=username)
        return True

    def new_join_code(self):
        code = random.choice(c.CONSONANTS) + random.choice(c.CONSONANTS) + random.choice(c.CONSONANTS) + random.choice(c.CONSONANTS)
        if code in self.rooms:
            return self.new_join_code()
        return code

    def create_new_room(self):
        code = self.new_join_code()
        new_room = Server.Room(code)
        self.rooms[code] = new_room
        return new_room


if __name__=="__main__":
    Server()