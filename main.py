import sys
import pygame
from settings import *
from game import Game

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        # Équipe: si vous ajoutez menu/crédits, faites un gestionnaire de scènes au lieu de gonfler Main.
        self.game = Game(self.screen)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.screen.fill(CHARCOAL)

            dt = self.clock.tick(FPS) / 1000
            self.game.run(dt)
            pygame.display.update()

if __name__ == '__main__':
    main = Main()
    main.run()
