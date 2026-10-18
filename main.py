import math
import platform

import pygame

import frame as f
import sys
import constants as c

from sound_manager import SoundManager
from image_manager import ImageManager
import asyncio
from primitives import Pose

import webbrowser

from texts_manager import TextsManager
from py_sprocket_web.web_sprocket import WebSprocket


class Game:
    def __init__(self):
        pygame.init()
        SoundManager.init()
        ImageManager.init()
        TextsManager.init()

        self.active_text_key = "Smoking"
        self.category_options = ["Smoking"]
        self.word_font = pygame.font.Font("fonts/ELEGANT TYPEWRITER Regular.ttf", 28)
        self.player_list_font = pygame.font.Font("fonts/ELEGANT TYPEWRITER Regular.ttf", 24)
        self.category_button_font = pygame.font.Font("fonts/ELEGANT TYPEWRITER Regular.ttf", 50)
        self.category_header_font = pygame.font.Font("fonts/ELEGANT TYPEWRITER Regular.ttf", 50)
        self.category_loading_font = pygame.font.Font("fonts/ELEGANT TYPEWRITER Regular.ttf", 26)
        self.timer_font = pygame.font.Font("fonts/SEBASTIAN_INFORMAL.otf", 64)
        self.room_code_font = pygame.font.Font("fonts/Kingthings Trypewriter 2.ttf", 185)


        self.small_screen = pygame.Surface(c.WINDOW_SIZE)
        self.screen = pygame.display.set_mode(c.SCALED_WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        pygame.mixer.init()

        self.shake_amp = 0
        self.since_shake = 999
        self.reset()
        self.current_level = 0
        self.scale = 0.5
        self.active_room = ""
        self.active_client_id = -1
        self.is_seeker = False

        self.sprocket = None

        pygame.display.set_caption(f"{c.CAPTION}")

        asyncio.run(self.main())

    async def initialize_sprocket(self):
        if not self.is_web_build():
            return
        self.sprocket = WebSprocket("https://giveaway-handful-frustrate.ngrok-free.dev")
        await self.sprocket.start()

    def shake(self, amt=15):
        self.shake_amp = amt
        self.since_shake = 0

    @staticmethod
    def web_log(string):
        if not Game.is_web_build():
            return
        platform.console.log(string)

    @staticmethod
    def is_web_build():
        return sys.platform == "emscripten"

    def open_steam_page(self):
        if not self.is_web_build():
            webbrowser.open('https://store.steampowered.com/app/3284290/Moonsigil_Atlas/')
        else:
            webbrowser.open('https://store.steampowered.com/app/3284290/Moonsigil_Atlas/')

    def get_shake_offset(self):
        magnitude = math.cos(self.since_shake * 50) * self.shake_amp
        direction = Pose((1, 1))
        if abs(magnitude) < 0.25:
            magnitude = 0
        return direction * magnitude

    def reset(self):
        pass

    async def main(self):
        try:
            await self.main_inner()
        except Exception as e:
            Game.web_log(f"Error: {e}")
            raise (e)


    async def main_inner(self):
        await self.initialize_sprocket()
        current_frame = f.MainMenu(self)
        current_frame.load()
        self.clock.tick(60)

        while True:
            dt, events = self.get_events()
            if dt == 0:
                dt = 1/100000
            if dt > 0.05:
                dt = 0.05

            if self.sprocket:
                packets = self.sprocket.get()
                for packet in packets:
                    current_frame.receive_packet(packet)

            current_frame.update(dt, events)
            current_frame.draw(self.screen, self.get_shake_offset().get_position())
            pygame.display.flip()
            await asyncio.sleep(0)

            if current_frame.done:
                current_frame = current_frame.next_frame()
                current_frame.load()


    def get_events(self):

        dt = self.clock.tick(c.FRAMERATE)/1000

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.scale *= 0.9
                if event.key == pygame.K_2:
                    self.scale /= 0.9

        self.since_shake += dt
        self.shake_amp -= 5*dt
        self.shake_amp *= 0.001 ** dt
        if (self.shake_amp < 0):
            self.shake_amp = 0

        return dt, events


if __name__ == "__main__":
    try:
        Game()
    except Exception as e:
        Game.web_log(f"Error: {e}")
        raise(e)
