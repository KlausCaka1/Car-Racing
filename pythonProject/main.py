import os
import re

import pygame
import math
from utils import scaleImage, blit_rotate_img
import neat

TRACK = scaleImage(pygame.image.load("imgs/track2.png"), 1)

TRACK_BOARD = scaleImage(pygame.image.load("imgs/track-border.png"), 1)
TRACK_BOARD_MASK = pygame.mask.from_surface(TRACK_BOARD)

FINISH_LINE = scaleImage(pygame.image.load("imgs/finish.png"), 1)
FINISH_LINE =  pygame.transform.scale(FINISH_LINE, (100, 116))
FINISH_LINE = pygame.transform.rotate(FINISH_LINE, 180)
FINISH_LINE_MASK = pygame.mask.from_surface(FINISH_LINE)
FINISH_LINE_POS = [770, 878]


WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RACE GAME")

TRACKS = ['./imgs/track.png', './imgs/track1.png', './imgs/track2.png']
global INDEX_TRACK

FPS = 60
generation = 1
BORDER_COLOR = (255, 255, 255, 255)  # Color To Crash on Hit

CAR_SIZE_X = 40
CAR_SIZE_Y = 40


# Color To Crash on Hit


class AbstractCar:
    def __init__(self):

        self.sprite = pygame.image.load('./imgs/car.png').convert()  # Convert Speeds Up A Lot
        self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
        self.mask = pygame.mask.from_surface(self.sprite)
        self.rotated_sprite = self.sprite

        self.position = [860, 920]  # Starting Position
        self.angle = 0
        self.speed = 0

        self.speed_set = False  # Flag For Default Speed Later on

        self.center = [self.position[0] + CAR_SIZE_X / 2, self.position[1] + CAR_SIZE_Y / 2]  # Calculate Center

        self.radars = []  # List For Sensors / Radars
        self.drawing_radars = []  # Radars To Be Drawn

        self.alive = True  # Boolean To Check If Car is Crashed

        self.distance = 0  # Distance Driven
        self.time = 0  # Time Passed

    def isAlive(self):
        return self.alive

    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.position)  # Draw Sprite
        self.draw_radar(screen)

    def draw_radar(self, win):
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(win, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(win, (255, 0, 0), position, 3)

    def check_radar(self, degree, game_map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # While We Don't Hit BORDER_COLOR AND length < 300 (just a max) -> go further and further
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 300:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])

    def get_data(self):
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values

    def get_reward(self):
        return self.distance / CAR_SIZE_X / 2

    def update(self, game_map):
        if not self.speed_set:
            self.speed = 20
            self.speed_set = True

        self.rotated_sprite = rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians((self.angle + 30))) * length,
                    self.center[1] + math.sin(math.radians((self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians((self.angle + 150))) * length,
                     self.center[1] + math.sin(math.radians((self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians((self.angle + 210))) * length,
                       self.center[1] + math.sin(math.radians((self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians((self.angle + 330))) * length,
                        self.center[1] + math.sin(math.radians((self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        self.distance += self.speed
        self.time += 1

        # Same For Y-Position
        self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], WIDTH - 120)

        self.center = [int(self.position[0]) + CAR_SIZE_X / 2, int(self.position[1]) + CAR_SIZE_Y / 2]

        self.check_collision(game_map)

        self.radars.clear()

        for degree in range(-90, 120, 45):
            self.check_radar(degree, game_map)

    def check_collision(self, game_map):
        self.alive = True
        for point in self.corners:
            # If Any Corner Touches Border Color -> Crash
            # Assumes Rectangle
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break

    def finish_line(self, finish_mask):
        offset = (int(self.position[0]) - FINISH_LINE_POS[0], int(self.position[1]) - FINISH_LINE_POS[1])

        overlap = finish_mask.overlap(self.mask, offset)

        if overlap:
            return True
        else:
            return False


def rotate_center(image, angle):
    # Rotate The Rectangle
    rectangle = image.get_rect()
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_rectangle = rectangle.copy()
    rotated_rectangle.center = rotated_image.get_rect().center
    rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
    return rotated_image


def run_simulation(genomes, config, counter=0):
    # Empty Collections For Nets and Cars
    nets = []
    cars = []
    global INDEX_TRACK

    # Initialize PyGame And The Display
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

    # For All Genomes Passed Create A New Neural Network
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(AbstractCar())

    # Clock Settings
    # Font Settings & Loading Map
    clock = pygame.time.Clock()
    game_map = pygame.image.load(TRACKS[INDEX_TRACK]).convert()


    # Simple Counter To Roughly Limit Time (Not Good Practice)

    print(counter, 'started.')

    while True:
        finished = False

        # Exit On Quit Event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # For Each Car Get The Acton It Takes
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.angle += 10  # Left
            elif choice == 1:
                car.angle -= 10  # Right
            elif choice == 2:
                if (car.speed - 2 >= 12):
                    car.speed -= 2  # Slow Down
            else:
                car.speed += 2  # Speed Up

        # Check If Car Is Still Alive
        # Increase Fitness If Yes And Break Loop If Not
        still_alive = 0
        for i, car in enumerate(cars):
            if car.isAlive():
                still_alive += 1
                car.update(game_map)
                genomes[i][1].fitness += car.get_reward()

        if still_alive == 0:
            break

        # Draw Map And All Cars That Are Alive
        screen.blit(game_map, (0, 0))
        screen.blit(FINISH_LINE, (FINISH_LINE_POS[0], FINISH_LINE_POS[1]))

        for car in cars:
            if car.isAlive():
                car.draw(screen)
                if car.finish_line(FINISH_LINE_MASK):
                    print("you won")
                    INDEX_TRACK += 1
                    finished = True

        # Display Info
        if finished:
            print(counter, 'changed')
            break

        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    return counter


def get_latest_checkpoint(prefix="neat-checkpoint"):
    files = os.listdir('.')
    checkpoints = []

    pattern = re.compile(rf"{prefix}(\d+)$")

    for f in files:
        match = pattern.match(f)
        if match:
            number = int(match.group(1))
            checkpoints.append((number, f))

    if not checkpoints:
        return None

    checkpoints.sort(key=lambda x: x[0])
    return checkpoints[-1][1]


def remove_checkpoint(prefix="neat-checkpoint"):
    files = os.listdir('.')

    pattern = re.compile(rf"{prefix}(\d+)$")

    for f in files:
        match = pattern.match(f)
        if match:
            os.remove(f)


if __name__ == "__main__":
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    checkpoint = get_latest_checkpoint()

    INDEX_TRACK = 0

    if checkpoint:
        population = neat.Checkpointer.restore_checkpoint(checkpoint)
        population.generation = 0
        population.reporters = neat.reporting.ReporterSet()
        remove_checkpoint()
    else:
        population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    population.add_reporter(neat.Checkpointer(generation_interval=5,
                                              filename_prefix="neat-checkpoint"))

    population.run(run_simulation, 9000)
