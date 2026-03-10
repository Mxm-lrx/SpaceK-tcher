import math
import pygame
from settings import SOFT_RED, OFF_WHITE
from utils import load_texture

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, ground_y):
        super().__init__(groups)
        self.spawn_position = pygame.Vector2(pos)
        self.ground_y = ground_y
        self.rocket_size = (56, 133)

        fallback_image = pygame.Surface((26, 46), pygame.SRCALPHA)
        pygame.draw.polygon(fallback_image, OFF_WHITE, [(13, 0), (26, 40), (0, 40)])
        pygame.draw.rect(fallback_image, SOFT_RED, pygame.Rect(7, 32, 12, 12))

        self.rocket_ground_image = self._load_rocket_sprite('Fusee_NF.png', fallback_image)
        self.rocket_flight_images = (
            self._load_rocket_sprite('Fusee_M1.png', self.rocket_ground_image),
            self._load_rocket_sprite('Fusee_M2.png', self.rocket_ground_image),
        )

        self.base_image = self.rocket_ground_image

        self.image = self.base_image
        self.rect = self.image.get_rect(center=pos)

        self.position = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)

        self.angle = 0.0
        self.angular_velocity = 0.0

        # Équipe : Toutes les variables en dessous servent à régler la conduite de la fusée (poids, poussée, etc.). À vous de jouer pour l'équilibrage !
        self.launch_impulse = -500.0
        self.gravity = 300.0
        self.thrust_power = 600.0
        self.linear_drag = 0.55

        self.turn_acceleration = 400.0
        self.turn_damping = 7.0
        self.max_turn_speed = 120.0
        self.max_tilt = 65.0

        self.max_horizontal_speed = 260.0
        self.max_vertical_speed = 360.0

        self.launched = False

    def _load_rocket_sprite(self, file_name, fallback_image):
        return load_texture(
            file_name,
            convert_alpha=True,
            scale_to=self.rocket_size,
            fallback_surface=fallback_image,
        )

    def reset_to_pad(self):
        self.position.update(self.spawn_position)
        self.velocity.update(0, 0)
        self.angle = 0.0
        self.angular_velocity = 0.0
        self.launched = False

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()

        if not self.launched and keys[pygame.K_SPACE]:
            self.launched = True
            self.velocity.y = self.launch_impulse

        if not self.launched:
            # Équipe : On bloque la rotation tant qu'on est sur le pad de lancement pour éviter que la fusée tourne sur elle-même au sol.
            self.angular_velocity = 0.0
            self.angle = 0.0
            return

        steer = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            steer += 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            steer -= 1.0

        self.angular_velocity += steer * self.turn_acceleration * dt
        self.angular_velocity -= self.angular_velocity * self.turn_damping * dt
        self.angular_velocity = max(-self.max_turn_speed, min(self.max_turn_speed, self.angular_velocity))

    def apply_physics(self, dt):
        if not self.launched:
            self.position.update(self.spawn_position)
            return

        self.angle += self.angular_velocity * dt
        self.angle = max(-self.max_tilt, min(self.max_tilt, self.angle))

        radians = math.radians(self.angle)
        forward = pygame.Vector2(-math.sin(radians), -math.cos(radians))
        
        acceleration = pygame.Vector2(0, self.gravity) + forward * self.thrust_power
        self.velocity += acceleration * dt
        self.velocity *= (1.0 - self.linear_drag * dt)

        self.velocity.x = max(-self.max_horizontal_speed, min(self.max_horizontal_speed, self.velocity.x))
        self.velocity.y = max(-self.max_vertical_speed, min(self.max_vertical_speed, self.velocity.y))

        self.position += self.velocity * dt

        if self.position.y >= self.ground_y and self.velocity.y > 0:
            self.reset_to_pad()

    def update_sprite(self):
        if not self.launched:
            self.base_image = self.rocket_ground_image
        else:
            animation_frame = (pygame.time.get_ticks() // 200) % 2
            self.base_image = self.rocket_flight_images[animation_frame]

        self.image = pygame.transform.rotozoom(self.base_image, self.angle, 1)
        self.rect = self.image.get_rect(center=self.position)

    def update(self, dt):
        # Équipe : Le "stable_dt" est un garde-fou. Si le PC rame un gros coup, ça évite que la fusée se téléporte à travers les murs.
        stable_dt = min(dt, 1 / 30)
        self.handle_input(stable_dt)
        self.apply_physics(stable_dt)
        self.update_sprite()