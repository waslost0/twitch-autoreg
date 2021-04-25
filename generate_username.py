import os
import random
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def generate_username(num_results=1):
    adjectives, nouns = [], []
    with open(r'data/adjectives.txt', 'r') as file_adjective:
        with open(r'data/nouns.txt', 'r') as file_noun:
            for line in file_adjective:
                adjectives.append(line.strip())
            for line in file_noun:
                nouns.append(line.strip())

    usernames = []
    for _ in range(num_results):
        adjective = random.choice(adjectives)
        noun = random.choice(nouns).capitalize()
        num = str(random.randrange(500))
        usernames.append(adjective + random.choice(['', '_']) + noun + num)

    return usernames
