import sys                  # Importation de la bibliothèque sys pour gérer les arguments et les fonctions système
import pygame               # Importation de la bibliothèque Pygame pour le développement du jeu
from settings import *      # Importation des paramètres du jeu
from game import Game       # Importation de la classe Game qui contient la logique du jeu

# Définition de la classe Main qui gère le lancement du jeu
class Main:     
    # Constructeur de la classe Main            
    def __init__(self):    
        # Initialisation de Pygame
        pygame.init() 

        # Création de la fenêtre du jeu avec les dimensions définies
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) 
        # Définition du titre de la fenêtre
        pygame.display.set_caption(TITLE)  
        # Création d'un objet Clock pour gérer le temps et les FPS
        self.clock = pygame.time.Clock()   
        # Création d'une instance de la classe Game
        self.game = Game(self.screen)      

    # Méthode pour lancer la boucle principale du jeu
    def run(self):  
        # Boucle principale du jeu    
        while True:
            # Gestion des événements (clavier, souris, etc.)      
            for event in pygame.event.get():
                # Si l'utilisateur ferme la fenêtre
                if event.type == pygame.QUIT:  
                    # Alors la boucle du jeu s'arrête
                    pygame.quit()
                    sys.exit()            

            # Remplie l'écran avec la couleur de fond
            self.screen.fill(CHARCOAL) 

            # Appel de la méthode principale de ta classe Game
            self.game.run() 
            
            # Actualisation de l'écran et contrôle du framerate
            pygame.display.update()
            self.clock.tick(FPS)

# Point d'entrée du programme
if __name__ == '__main__':
    main = Main()
    main.run()
