import pygame
import time
import math
from utils import scaleImage, blit_rotate_img
import neat

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
generation = 1
BORDER_COLOR = (0, 0, 0, 255) # Color To Crash on Hit


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
        self.radars = []

        self.center = [self.x + RED_CAR.get_width() / 2, self.y + RED_CAR.get_height() / 2] # Calculate Center


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

    def move_backward(self):
        self.vel = max(self.vel - self.acceleration, -self.max_vel / 2)
        self.move()

    def reduce_speed(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)
        self.move()

    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.img)
        offset = (int(self.x - x), int(self.y - y))
        poi = mask.overlap(car_mask, offset)
        return poi

    def check_radar(self, game_map):
        self.radars.clear()
        self.center = [int(self.x + RED_CAR.get_width() / 2), int(self.y + RED_CAR.get_height() / 2)]

        # Use -60 to 60 for a cleaner "Front View" cone
        map_width, map_height = game_map.get_width(), game_map.get_height()

        for degree in range(-180, 81, 30):
            length = 0

            # Calculate initial x, y
            x = int(self.center[0] - math.cos(math.radians(360 - (self.angle + degree))))
            y = int(self.center[1] - math.sin(math.radians(360 - (self.angle + degree))))

            # We change the loop to strictly check length first
            while length < 100:

                # 1. SAFETY CHECK: Ensure coordinates are within the map boundaries
                if x < 0 or x >= map_width or y < 0 or y >= map_height:
                    break  # Stop the ray if it goes off the screen

                # 2. WALL CHECK: Check for collision
                if game_map.get_at((x, y)) == BORDER_COLOR:
                    break  # Stop the ray if it hits a wall

                # 3. Extend the ray
                length += 1
                x = int(self.center[0] - math.cos(math.radians(360 - (self.angle + degree))) * length)
                y = int(self.center[1] - math.sin(math.radians(360 - (self.angle + degree))) * length)

            # Calculate distance and append
            dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
            self.radars.append([(x, y), dist])

    def draw_radar(self, win):
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(win, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(win, (255, 0, 0), position, 3)


    def get_data(self):
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values



class Car(AbstractCar):
    IMG = RED_CAR
    START_POS = (180, 200)

    def bounce(self):
        self.vel = -self.vel
        self.move()




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


def player_move(player_car):
    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_a]:
        player_car.rotate(left=True)
    if keys[pygame.K_d]:
        player_car.rotate(right=True)
    if keys[pygame.K_w]:
        moved = True
        player_car.move_forward()
    if keys[pygame.K_s]:
        moved = True
        player_car.move_backward()

    if not moved:
        player_car.reduce_speed()


def draw(win, images, cars):
    for img, pos in images:
        win.blit(img, pos)

    for i, car in enumerate(cars):
        car.draw(win)
        car.draw_radar(WIN)

    pygame.display.update()


def run_simulation(genomes, config):
    nets = []
    cars = []

    run = True
    clock = pygame.time.Clock()
    images = [(GRASS, (0, 0)), (TRACK, (0, 0)),
              (FINISH_LINE, FINISH_LINE_POS), (TRACK_BOARD, (0, 0))]
    GAME_MAP = TRACK_BOARD.convert()

    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)

        player_car = Car(4, 5)
        g.fitness = 0

        cars.append(player_car)


    while run:
        clock.tick(FPS)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        for i, car in enumerate(cars):
            car.check_radar(GAME_MAP)

            if car.collide(TRACK_BOARD_MASK) != None:
                car.bounce()



        draw(WIN, images, cars)
        player_move(cars[0])


        # for i, car in enumerate(cars):
        #     output = nets[i].activate(car.get_data())
        #     choice = output.index(max(output))
        #     if choice == 0:
        #         car.angle += 10  # Left
        #     elif choice == 1:
        #         car.angle -= 10  # Right
        #     elif choice == 2:
        #         if (car.speed - 2 >= 12):
        #             car.speed -= 2  # Slow Down
        #     else:
        #         car.speed += 2


        still_alive = 0




    pygame.quit()


if __name__ == "__main__":
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # Create Population And Add Reporters
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    population.run(run_simulation, 1)

