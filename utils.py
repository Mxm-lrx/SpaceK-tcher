import os
import pygame
from typing import List


ASSETS_DIR = 'assets'
MISSING_TEXTURE_NAME = 'MissingTexture.jpg'


def _load_surface(path):
	try:
		return pygame.image.load(path)
	except (pygame.error, FileNotFoundError):
		return None


def _fallback_checkerboard(size=(64, 64)):
	surface = pygame.Surface(size)
	tile = max(8, min(size) // 4)
	colors = ((255, 0, 255), (0, 0, 0))
	for y in range(0, size[1], tile):
		for x in range(0, size[0], tile):
			color_index = ((x // tile) + (y // tile)) % 2
			pygame.draw.rect(surface, colors[color_index], (x, y, tile, tile))
	return surface


def _prepare_surface(surface, convert_alpha):
	if surface is None:
		return None
	if pygame.display.get_surface() is None:
		return surface
	if convert_alpha:
		return surface.convert_alpha()
	return surface.convert()


def load_texture(file_name, convert_alpha=True, scale_to=None, fallback_surface=None):
	texture_path = os.path.join(ASSETS_DIR, file_name)
	surface = _load_surface(texture_path)

	if surface is None and file_name != MISSING_TEXTURE_NAME:
		missing_path = os.path.join(ASSETS_DIR, MISSING_TEXTURE_NAME)
		surface = _load_surface(missing_path)

	if surface is None:
		surface = fallback_surface if fallback_surface is not None else _fallback_checkerboard()

	surface = _prepare_surface(surface, convert_alpha)
	if scale_to is not None:
		surface = pygame.transform.smoothscale(surface, scale_to)
	return surface

####################################################################################################

def import_image(path: str) -> pygame.Surface:
    # convert_alpha() : optimise l'image pour Pygame et gère la transparence
    return pygame.image.load(path).convert_alpha()

def import_folder(path: str) -> List[pygame.Surface]:
    surface_list = []
    
    # sorted() : permet de forcer le bon ordre du chargement des frames d'animation (ex: 0.png, 1.png...)
    for file_name in sorted(os.listdir(path)):
        full_path = os.path.join(path, file_name)
        
        # Vérifie que ce soit un fichier (pas un dossier)
        if os.path.isfile(full_path):
            try:
                image_surf = pygame.image.load(full_path).convert_alpha()
                surface_list.append(image_surf)
            except pygame.error:
                # Ignore les fichiers qui ne sont pas des images
                pass
                
    return surface_list