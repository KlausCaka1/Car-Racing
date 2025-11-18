import pygame
import time
import math
from utils import scaleImage, blit_rotate_img

GRASS = scaleImage(pygame.image.load("imgs/grass.jpg"), 2.5)
TRACK = scaleImage(pygame.image.load("imgs/track.png"), 1)

TRACK_BOARD = scaleImage(pygame.image.load("imgs/track-border.png"), 1)
TRACK_BOARD_MASK = pygame.mask.from_surface(TRACK_BOARD)

FINISH_LINE = scaleImage(pygame.image.load("imgs/finish.png"), 1.2)
FINISH_LINE_MASK = pygame.mask.from_surface(FINISH_LINE)
FINISH_LINE_POS = (130, 250)

RED_CAR = scaleImage(pygame.image.load("imgs/red-car.png"), 0.5)
GREEN_CAR = scaleImage(pygame.image.load("imgs/green-car.png"), 0.5)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RACE GAME")


FPS = 60

class AbstractCar:
    def __init__(self, max_vel, rotation_vel):
        self.img = self.IMG
        self.max_vel = max_vel
        self.rotation_vel = rotation_vel
        self.angle = 0
        self.speed = 0
        self.vel = 0
        self.acceleration = 0.1
        self.x, self.y = self.START_POS

    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.rotation_vel
        elif right:
            self.angle -= self.rotation_vel

    def draw(self, win):
        blit_rotate_img(win, self.img, (self.x, self.y), self.angle)

    def move(self):
        radius = math.radians(self.angle)
        veritcal = math.cos(radius) * self.vel
        horisontal = math.sin(radius) * self.vel

        self.x -= horisontal
        self.y -= veritcal

    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.move()

    def reduce_speed(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)
        self.move()


class Car(AbstractCar):
    IMG = RED_CAR
    START_POS = (180, 200)

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


def draw(win, images, player_car):
    for img, pos in images:
        win.blit(img, pos)

    player_car.draw(win)
    pygame.display.update()



run = True
clock = pygame.time.Clock()
images = [(GRASS, (0, 0)), (TRACK, (0, 0)),
          (FINISH_LINE, FINISH_LINE_POS), (TRACK_BOARD, (0, 0))]

player_car = Car(4, 4)



while run:
    clock.tick(FPS)

    draw(WIN, images, player_car)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            break

    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_a]:
        player_car.rotate(left=True)
    if keys[pygame.K_d]:
        player_car.rotate(right=True)
    if keys[pygame.K_w]:
        moved = True
        player_car.move_forward()

    if not moved:
        player_car.reduce_speed()


pygame.quit()
