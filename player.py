import math
import pygame
from settings import SOFT_RED, OFF_WHITE
from utils import load_texture

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, ground_y):
        super().__init__(groups)

        # On initialise les propriétés de la fusée :
        # On initialise la position de spawn de la fusée
        self.spawn_position = pygame.Vector2(pos)
        # On initialise les les coordonnées du sol
        self.ground_y = ground_y
        # On initialise la taille de la fusée 
        self.rocket_size = (56, 133)

        # On gère les graphiques :
        # On affiche une fusée de secours si les sprites sont introuvables
        fallback_image = pygame.Surface((26, 46), pygame.SRCALPHA)
        # On dessine le corps de la fusée
        pygame.draw.polygon(fallback_image, OFF_WHITE, [(13, 0), (26, 40), (0, 40)])
        # On dessine les flammes de la fusée
        pygame.draw.rect(fallback_image, SOFT_RED, pygame.Rect(7, 32, 12, 12))

        # On charge les sprites de la fusée (au sol et en vol)
        # On utilise une image de secours si le fichier est introuvable
        self.rocket_ground_image = self._load_rocket_sprite('Fusee_NF.png', fallback_image)
        self.rocket_flight_images = (
            self._load_rocket_sprite('Fusee_M1.png', self.rocket_ground_image),
            self._load_rocket_sprite('Fusee_M2.png', self.rocket_ground_image),
        )

        # On commence avec l'image de la fusée au sol
        self.base_image = self.rocket_ground_image

        # On initialise l'image
        self.image = self.base_image
        # On centre le rectangle de collision sur la position de spawn
        self.rect = self.image.get_rect(center=pos)

        # On initialise les propriétés physiques de la fusée
        self.position = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)

        # On initialise les propriétés de rotation de la fusée
        self.angle = 0.0
        self.angular_velocity = 0.0

        # Toutes les variables en dessous servent à régler la conduite de la fusée (poids, poussée, etc.). À vous de jouer pour l'équilibrage !
        self.launch_impulse = -500.0
        self.gravity = 300.0
        self.thrust_power = 600.0
        self.linear_drag = 0.55

        # Ces variables contrôlent la rotation de la fusée en vol (plus les valeurs sont élevées, plus la fusée tourne vite et se stabilise rapidement)
        self.turn_acceleration = 400.0
        self.turn_damping = 7.0
        self.max_turn_speed = 120.0
        self.max_tilt = 65.0

        # Ces variables limitent la vitesse maximale de la fusée pour éviter les comportements incontrôlables
        self.max_horizontal_speed = 260.0
        self.max_vertical_speed = 360.0

        # On initialise l'état de lancement de la fusée (au départ, elle n'est pas lancée)
        self.launched = False


    # On définit une méthode pour charger les sprites de la fusée, avec une image de secours en cas d'erreur de chargement
    def _load_rocket_sprite(self, file_name, fallback_image):
        # On renvoie l'image chargée, redimensionnée à la taille de la fusée, ou l'image de secours si le chargement échoue
        return load_texture(
            file_name,
            convert_alpha=True,
            scale_to=self.rocket_size,
            fallback_surface=fallback_image,
        )


    # On définit une méthode pour réinitialiser la fusée à sa position de spawn, utilisée lorsqu'elle touche le sol
    def reset_to_pad(self):
        # On remet la fusée à sa position de spawn, on réinitialise sa vitesse et sa rotation, et on marque qu'elle n'est plus lancée
        self.position.update(self.spawn_position)
        self.velocity.update(0, 0)
        self.angle = 0.0
        self.angular_velocity = 0.0
        self.launched = False


    # On définit une méthode pour gérer les entrées du joueur et contrôler la fusée en vol
    def handle_input(self, dt):
        # On récupère l'état des touches du clavier
        keys = pygame.key.get_pressed()

        # Si la fusée n'est pas encore lancée et que le joueur appuie sur la barre d'espace, on lance la fusée en lui donnant une impulsion vers le haut
        if not self.launched and keys[pygame.K_SPACE]:
            self.launched = True
            self.velocity.y = self.launch_impulse

        # Si la fusée n'est pas lancée, on bloque la rotation pour éviter que la fusée tourne sur elle-même au sol
        if not self.launched:
            # On bloque la rotation tant qu'on est sur le pad de lancement pour éviter que la fusée tourne sur elle-même au sol.
            self.angular_velocity = 0.0
            self.angle = 0.0
            return

        # On gère la rotation de la fusée en fonction des touches gauche/droite (ou Q/D) pour faire pencher la fusée et lui donner une direction de vol
        steer = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            steer += 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            steer -= 1.0

        # On applique une accélération angulaire en fonction de l'entrée du joueur, puis on applique un amortissement pour stabiliser la fusée en vol
        self.angular_velocity += steer * self.turn_acceleration * dt
        self.angular_velocity -= self.angular_velocity * self.turn_damping * dt
        self.angular_velocity = max(-self.max_turn_speed, min(self.max_turn_speed, self.angular_velocity))


    # On définit une méthode pour appliquer les lois de la physique à la fusée, en tenant compte de la gravité, de la poussée, de la résistance de l'air, et des limites de vitesse
    def apply_physics(self, dt):
        if not self.launched:
            self.position.update(self.spawn_position)
            return

        # On met à jour l'angle de la fusée en fonction de sa vitesse de rotation, puis on limite l'angle pour éviter que la fusée ne se penche trop et devienne incontrôlable
        self.angle += self.angular_velocity * dt
        self.angle = max(-self.max_tilt, min(self.max_tilt, self.angle))

        # On calcule la direction de la poussée en fonction de l'angle de la fusée, puis on applique la gravité, la poussée, et la résistance de l'air pour mettre à jour la vitesse de la fusée
        radians = math.radians(self.angle)
        forward = pygame.Vector2(-math.sin(radians), -math.cos(radians))
        
        # L'accélération est la somme de la gravité (qui tire vers le bas) et de la poussée (qui pousse dans la direction de la fusée)
        acceleration = pygame.Vector2(0, self.gravity) + forward * self.thrust_power
        self.velocity += acceleration * dt
        self.velocity *= (1.0 - self.linear_drag * dt)

        # On limite la vitesse de la fusée pour éviter les comportements incontrôlables à haute vitesse
        self.velocity.x = max(-self.max_horizontal_speed, min(self.max_horizontal_speed, self.velocity.x))
        self.velocity.y = max(-self.max_vertical_speed, min(self.max_vertical_speed, self.velocity.y))

        # On met à jour la position de la fusée en fonction de sa vitesse
        self.position += self.velocity * dt

        # Si la fusée touche le sol, on la réinitialise à sa position de spawn
        if self.position.y >= self.ground_y and self.velocity.y > 0:
            self.reset_to_pad()


    # On définit une méthode pour mettre à jour l'image de la fusée en fonction de son état (au sol ou en vol) et de son angle de rotation
    def update_sprite(self):
        if not self.launched:
            self.base_image = self.rocket_ground_image
        else:
            animation_frame = (pygame.time.get_ticks() // 200) % 2
            self.base_image = self.rocket_flight_images[animation_frame]

        # On fait pivoter l'image de la fusée en fonction de son angle, puis on met à jour le rectangle de collision pour qu'il soit centré sur la position actuelle de la fusée
        self.image = pygame.transform.rotozoom(self.base_image, self.angle, 1)
        self.rect = self.image.get_rect(center=self.position)


    # On définit une méthode pour mettre à jour la fusée à chaque frame, en gérant les entrées du joueur, en appliquant la physique, et en mettant à jour l'image de la fusée
    def update(self, dt):
        #Le "stable_dt" est un garde-fou. Si le PC rame un gros coup, ça évite que la fusée se téléporte à travers les murs
        stable_dt = min(dt, 1 / 30)
        self.handle_input(stable_dt)
        self.apply_physics(stable_dt)
        self.update_sprite()