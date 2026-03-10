import pygame
from settings import BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, SOFT_YELLOW
from level import Level
from utils import load_texture

class Game:
    def __init__(self, screen):
        self.screen = screen
        # Équipe : C'est ici qu'on listera tous nos niveaux plus tard (Level2, Level3...). Pour l'instant on n'en a qu'un seul de prêt.
        self.levels = [Level(self.screen)]
        self.current_level_index = 0

        # Équipe : Gestion des états du jeu (menu principal vs niveau en cours)
        self.state = 'menu'

        # Équipe : Initialisation des éléments graphiques du menu
        self.font = pygame.font.Font(None, 48)
        self.logo = load_texture('MissingTexture.jpg', scale_to=(350, 350))

    @property
    def current_level(self):
        return self.levels[self.current_level_index]

    def draw_menu(self):
        # Équipe : Affichage du logo au centre de l'écran s'il est trouvé
        logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(self.logo, logo_rect)

        # Équipe : Affichage de l'instruction pour lancer la partie
        text_surf = self.font.render("Appuie sur ESPACE pour Jouer", True, SOFT_YELLOW)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 180))
        self.screen.blit(text_surf, text_rect)

    def handle_menu_input(self):
        # Équipe : Transition vers le jeu quand on appuie sur ESPACE
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.state = 'playing'

    def run(self, dt):
        self.screen.fill(BG_COLOR)
        
        if self.state == 'menu':
            self.handle_menu_input()
            self.draw_menu()
        else:
            self.current_level.run(dt)