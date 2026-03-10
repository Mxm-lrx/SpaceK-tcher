import sys
import pygame
from settings import BG_COLOR
from level import Level

class Game:
    def __init__(self, screen):
        self.screen = screen
        # Équipe: ajouter les prochains niveaux dans cette liste (Level2, Level3, etc.).
        self.levels = [Level()]
        self.current_level_index = 0

    @property
    def current_level(self):
        return self.levels[self.current_level_index]

    def run(self, dt):
        self.screen.fill(BG_COLOR)
        self.current_level.run(dt)

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    game = Game(screen)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        game.run(clock.tick(60) / 1000)
        pygame.display.update()
