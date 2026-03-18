import os
import pygame
from typing import List, Tuple, Optional


ASSETS_DIR = 'assets'
MISSING_TEXTURE_NAME = 'MissingTexture.jpg'

# Cette fonction charge une image depuis le dossier assets, elle gère les erreurs de chargement et peut retourner une surface de remplacement si l'image est introuvable. Elle est utilisée dans level.py pour charger les textures des sprites.
def _load_surface(path):
	# Tente de charger l'image, retourne None si elle est introuvable ou si une erreur se produit
	try:
		return pygame.image.load(path)
	except (pygame.error, FileNotFoundError):
		return None


# Cette fonction génère une surface de remplacement en damier, utilisée lorsque le chargement d'une texture échoue. Elle est appelée par load_texture() dans le cas où l'image ne peut pas être chargée.	
def _fallback_checkerboard(size=(64, 64)):
	# Crée une surface de remplacement avec un motif de damier pour indiquer une texture manquante
	surface = pygame.Surface(size)
	tile = max(8, min(size) // 4)
	colors = ((255, 0, 255), (0, 0, 0))
	for y in range(0, size[1], tile):
		for x in range(0, size[0], tile):
			color_index = ((x // tile) + (y // tile)) % 2
			pygame.draw.rect(surface, colors[color_index], (x, y, tile, tile))
	return surface

# Cette fonction est la fonction principale pour charger une texture, elle utilise les fonctions précédentes pour gérer les erreurs et préparer la surface pour l'affichage. Elle est utilisée dans level.py pour charger les textures des sprites et peut être utilisée ailleurs dans le projet pour charger d'autres images.
def _prepare_surface(surface, convert_alpha):
	# Si la surface est None, retourne None. Sinon, convertit la surface pour une meilleure performance
	if surface is None:
		return None
	if pygame.display.get_surface() is None:
		return surface
	if convert_alpha:
		return surface.convert_alpha()
	return surface.convert()

# Cette fonction est la fonction publique pour charger une texture, elle gère les erreurs de chargement et peut retourner une surface de remplacement si l'image est introuvable. Elle est utilisée dans level.py pour charger les textures des sprites et peut être utilisée ailleurs dans le projet pour charger d'autres images.
def load_texture(file_name, convert_alpha=True, scale_to=None, fallback_surface=None):
	# Tente de charger la texture depuis le dossier des assets, utilise une texture de remplacement si elle est introuvable
	texture_path = os.path.join(ASSETS_DIR, file_name)
	surface = _load_surface(texture_path)

	if surface is None and file_name != MISSING_TEXTURE_NAME:
		missing_path = os.path.join(ASSETS_DIR, MISSING_TEXTURE_NAME)
		surface = _load_surface(missing_path)

	if surface is None:
		surface = fallback_surface if fallback_surface is not None else _fallback_checkerboard()

	surface = _prepare_surface(surface, convert_alpha)
	# Si scale_to est spécifié, redimensionne la surface à la taille souhaitée
	if scale_to is not None:
		surface = pygame.transform.smoothscale(surface, scale_to)
	return surface

####################################################################################################

def import_image(path: str) -> pygame.Surface:
    # convert_alpha() : optimise l'image pour Pygame et gère la transparence
    return pygame.image.load(path).convert_alpha()

def import_folder(path: str, scale_to: Optional[Tuple[int, int]] = None):
	# Importe toutes les images d'un dossier, les convertit pour Pygame et les redimensionne si nécessaire
    surface_list = []
    
    # Force l'ordre de chargement des fichiers (ex: 0.png, 1.png, 2.png...) pour les animations
    for file_name in sorted(os.listdir(path)):
        full_path = os.path.join(path, file_name)

    # Vérifie que le chemin correspond à un fichier (et pas à un dossier)    
        if os.path.isfile(full_path):
            try:
                image_surf = pygame.image.load(full_path).convert_alpha()

                if scale_to is not None:
                    image_surf = pygame.transform.smoothscale(image_surf, scale_to)
                
                surface_list.append(image_surf)
			# Ignore les fichiers qui ne sont pas des images
            except pygame.error:
                pass
                
    return surface_list
