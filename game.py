import sys
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, FPS
from level import Level

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.level = Level()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def update(self):
        self.level.update()

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.level.draw(self.screen)
        pygame.display.update()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == '__main__':
    game = Game()
    game.run()
