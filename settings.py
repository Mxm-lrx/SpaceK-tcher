# Ce fichier contient les paramètres de base du jeu :
# On définit les dimensions de la fenêtre
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
# On définit le framerate du jeu 
FPS = 60
# On définit le titre de la fenêtre du jeu
TITLE = "SpaceK'tcher"

# On définit les couleurs utilisées dans le jeu (en format RGB)
OFF_WHITE = (250, 250, 250)		#Blanc cassé
DEEP_DARK = (30, 30, 35)		#Gris sombre
CHARCOAL  = (50, 55, 65)		#Gris charbon

# On définit une palette de couleurs douces pour les éléments du jeu (fusée, flammes, etc.)
SOFT_RED    = (230, 90, 90)		#Rouge doux
SOFT_GREEN  = (110, 210, 140)	#Vert doux
SOFT_BLUE   = (100, 160, 240)	#Bleu doux
SOFT_YELLOW = (245, 230, 100)	#Jaune doux
SOFT_PURPLE = (180, 120, 220)	#Violet doux
SOFT_CYAN   = (100, 220, 220)	#Cyan doux

# On définit la couleur de fond du jeu
BG_COLOR = (20, 20, 40)

# On définit la taille des tuiles du monde
TILESIZE = 64
# On définit la carte du monde du jeu, où 'X' représente les murs et les espaces vides représentent les zones où la fusée peut se déplacer
WORLD_MAP = [
	['X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X'],
	['X', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'X'],
	['X', ' ', 'X', ' ', 'X', ' ', 'X', ' ', ' ', 'X'],
	['X', ' ', 'X', ' ', 'X', ' ', 'X', ' ', ' ', 'X'],
	['X', ' ', ' ', ' ', ' ', ' ', 'X', ' ', ' ', 'X'],
	['X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X'],
]