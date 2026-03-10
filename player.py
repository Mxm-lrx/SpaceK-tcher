import math
import pygame
from settings import SOFT_RED, OFF_WHITE


class Player(pygame.sprite.Sprite):
	def __init__(self, pos, groups, world_width, world_height, ground_y):
		super().__init__(groups)
		self.spawn_position = pygame.Vector2(pos)
		self.world_width = world_width
		self.world_height = world_height
		self.ground_y = ground_y

		self.base_image = pygame.Surface((26, 46), pygame.SRCALPHA)
		pygame.draw.polygon(self.base_image, OFF_WHITE, [(13, 0), (26, 40), (0, 40)])
		pygame.draw.rect(self.base_image, SOFT_RED, pygame.Rect(7, 32, 12, 12))

		self.image = self.base_image
		self.rect = self.image.get_rect(center=pos)

		self.position = pygame.Vector2(pos)
		self.velocity = pygame.Vector2(0, 0)

		self.angle = 0.0
		self.angular_velocity = 0.0

		# Réglages de vol.
		# Équipe : commencez par tweak ces valeurs avant de toucher la formule physique.
		self.launch_impulse = -220.0
		self.gravity = 300.0
		self.thrust_power = 360.0
		self.linear_drag = 0.55

		self.turn_acceleration = 260.0
		self.turn_damping = 7.0
		self.max_turn_speed = 120.0
		self.max_tilt = 65.0

		self.max_horizontal_speed = 260.0
		self.max_vertical_speed = 360.0

		self.launched = False

	def reset_to_pad(self):
		# Remet la fusée au point de départ.
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
			# Équipe: pas de rotation au sol pour éviter les mouvements chelous.
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
		self.velocity -= self.velocity * self.linear_drag * dt

		self.velocity.x = max(-self.max_horizontal_speed, min(self.max_horizontal_speed, self.velocity.x))
		self.velocity.y = max(-self.max_vertical_speed, min(self.max_vertical_speed, self.velocity.y))

		self.position += self.velocity * dt

		horizontal_padding = 20
		if self.position.x < horizontal_padding:
			self.position.x = horizontal_padding
			self.velocity.x = 0
		elif self.position.x > self.world_width - horizontal_padding:
			self.position.x = self.world_width - horizontal_padding
			self.velocity.x = 0

		if self.position.y < -120:
			self.position.y = -120
			self.velocity.y = 0

		if self.position.y >= self.ground_y and self.velocity.y > 0:
			self.reset_to_pad()

	def update_sprite(self):
		self.image = pygame.transform.rotozoom(self.base_image, self.angle, 1)
		self.rect = self.image.get_rect(center=self.position)

	def update(self, dt):
		# Petit garde-fou anti gros freeze.
		# Équipe : si ça rame fort, montez ce clamp progressivement (1/30 -> 1/20 max).
		stable_dt = min(dt, 1 / 30)
		self.handle_input(stable_dt)
		self.apply_physics(stable_dt)
		self.update_sprite()
