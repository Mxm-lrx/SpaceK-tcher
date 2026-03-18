import pygame
from settings import TILESIZE, CHARCOAL

# On définit la classe Tile, qui représente une tuile du monde du jeu (un mur). Elle hérite de pygame.sprite.Sprite pour pouvoir être utilisée dans des groupes de sprites et bénéficier de fonctionnalités comme la détection de collisions.
class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        # On crée une surface pour représenter la tuile
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        # On remplit la surface avec une couleur sombre pour représenter un mur
        self.image.fill(CHARCOAL)
        # On positionne le rectangle de collision de la tuile à la position donnée
        self.rect = self.image.get_rect(topleft=pos)
