import sys
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS
from game import Game
from utils import load_texture

# On définit la classe principale du jeu, qui gère l'initialisation de Pygame, la création de la fenêtre, et la boucle principale du jeu
class Main:
    def __init__(self):
        # Initialisation du mixeur audio pour éviter la latence
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.init()
        
        # Chargement et assignation de l'icône de la fenêtre du jeu
        icon_img = load_texture('logo_rvb.png', convert_alpha=False)
        pygame.display.set_icon(icon_img)

        # On initialise la fenêtre du jeu, on lui donne un titre, et on crée une horloge pour gérer le framerate
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.game = Game(self.screen)


    # On définit une méthode quand le jeu tourne, qui gère les événements, met à jour le jeu, et rafraîchit l'affichage à chaque frame
    def run(self):
        # On entre dans la boucle principale du jeu, qui tourne tant que le jeu est actif.
        while True:
            # On gère les événements du jeu, en vérifiant si le joueur a fermé la fenêtre pour quitter proprement le jeu
            for event in pygame.event.get():
                # Si le joueur ferme la fenêtre, on quitte Pygame et on termine le programme
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # On calcule le temps écoulé depuis la dernière frame pour faire en sorte que le jeu tourne à une vitesse constante, même si le framerate varie. On divise par 1000 pour convertir les millisecondes en secondes.
            dt = self.clock.tick(FPS) / 1000.0
            self.game.run(dt)
            pygame.display.update()


# On vérifie si ce script est exécuté directement (plutôt que importé comme module), et si c'est le cas, on crée une instance de la classe Main et on lance le jeu en appelant la méthode run()
if __name__ == '__main__':
    main = Main()
    main.run()