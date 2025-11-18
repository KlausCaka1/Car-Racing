import pygame
import time
import math
from utils import scaleImage

GRASS = scaleImage(pygame.image.load("imgs/grass.jpg"), 1)
TRACK = scaleImage(pygame.image.load("imgs/track.png"), 1)

TRACK_BOARD = scaleImage(pygame.image.load("imgs/track-border.png"), 1)
TRACK_BOARD_MASK = pygame.mask.from_surface(TRACK_BOARD)

FINISH_LINE = scaleImage(pygame.image.load("imgs/finish.png"), 1)
FINISH_LINE_MASK = pygame.mask.from_surface(FINISH_LINE)
FINISH_LINE_POS = (130, 250)

RED_CAR = scaleImage(pygame.image.load("imgs/red-car.png"), 1)
GREEN_CAR = scaleImage(pygame.image.load("imgs/green-car.png"), 1)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RACE GAME")

MAIN_FONT = pygame.font.SysFont("comicsans", 44)

FPS = 60
PATH = [(175, 119), (110, 70), (56, 133), (70, 481), (318, 731), (404, 680), (418, 521), (507, 475), (600, 551), (613, 715), (736, 713),
        (734, 399), (611, 357), (409, 343), (433, 257), (697, 258), (738, 123), (581, 71), (303, 78), (275, 377), (176, 388), (178, 260)]

class GameInfo:
    LEVELS = 5
    def __init__(self):
        self.level = 1
        self.started = False
        self.time = 0

    def start(self):
        self.started = True
        self.time = time.time()

    def finishGame(self):
        self.started = False
        return self.level > self.LEVELS

    def next_level(self):
        self.level += 1
        self.started = False

    def reset_game(self):
        self.started = False
        self.time = 0
        self.level = 1

    def get_time_game(self):
        if not self.started:
            return 0
        return round(time.time() - self.time)