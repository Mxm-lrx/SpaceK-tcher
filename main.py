import sys
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS
from game import Game
from utils import load_texture

class Main:
    def __init__(self):
        pygame.init()
        
        # Équipe : Chargement et assignation de l'icône de la fenêtre du jeu
        icon_img = load_texture('logo_rvb.png', convert_alpha=False)
        pygame.display.set_icon(icon_img)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.game = Game(self.screen)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            dt = self.clock.tick(FPS) / 1000.0
            self.game.run(dt)
            pygame.display.update()

if __name__ == '__main__':
    main = Main()
    main.run()