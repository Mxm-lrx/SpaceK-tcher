import pygame
from settings import TILESIZE, CHARCOAL


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(CHARCOAL)
        self.rect = self.image.get_rect(topleft=pos)
