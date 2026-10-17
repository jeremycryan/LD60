import json
import random


class TextsManager:
    TEXTS = []

    @staticmethod
    def init():
        with open("texts/texts.json") as f:
            TextsManager.TEXTS = json.loads(f.read())

    @staticmethod
    def get_text_from_key(name):
        for item in TextsManager.TEXTS:
            if item.get("name") == name:
                return item.get("text")

    @staticmethod
    def get_display_name_from_key(name):
        for item in TextsManager.TEXTS:
            if item.get("name") == name:
                return item.get("display_name")

    @staticmethod
    def get_random_key():
        return random.choice(TextsManager.TEXTS).get("name")


