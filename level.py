from pathlib import Path
import math
import random
import pygame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH, SOFT_YELLOW, OFF_WHITE, SOFT_CYAN
from player import Player

class FloatingObstacle(pygame.sprite.Sprite):
    def __init__(self, position, image, groups):
        super().__init__(groups)
        scale = random.uniform(0.18, 0.42)  # plus petit qu'avant
        w, h = image.get_size()
        self.image = pygame.transform.smoothscale(
            image, (max(12, int(w * scale)), max(12, int(h * scale)))
        )
        self.position = pygame.Vector2(position)
        self.base_velocity = pygame.Vector2(
            random.uniform(-120, 120),
            random.uniform(-100, 140),
        )
        self.frequency = random.uniform(0.6, 1.8)
        self.phase = random.uniform(0, math.tau)
        self.wobble_strength = random.uniform(15, 65)
        self.age = 0.0
        self.collision_radius = max(10, min(self.image.get_width(), self.image.get_height()) * 0.33)

    def update(self, dt):
        self.age += dt
        wobble = pygame.Vector2(
            math.sin(self.age * self.frequency + self.phase),
            math.cos(self.age * (self.frequency * 0.83) + self.phase),
        ) * self.wobble_strength
        self.position += (self.base_velocity + wobble) * dt


class Level:
    # C'est la classe qui fait tout le travaille pour faire tourner le niveau, elle gère la caméra, les étoiles de fond, le score, etc. C'est un peu la classe centrale du projet.
    def __init__(self, surface):
        self.display_surface = surface
        self.ground_y = 0

        self.visible_sprites = pygame.sprite.Group()
        self.player = Player(
            (0, self.ground_y),
            [self.visible_sprites],
            self.ground_y
        )

        self.font = pygame.font.Font(None, 32)
        self.camera_x = self.player.position.x - SCREEN_WIDTH * 0.5
        self.camera_y = self.player.position.y - SCREEN_HEIGHT * 0.65
        self.score = 0
        self.score_file = Path(__file__).with_name('score.txt')
        self.high_score = self.load_high_score()
        self.px_to_meter = 1.0  # Ajuste cette valeur selon l'échelle réelle du jeu (1 px = 1 m par défaut)

        self.assets_dir = Path(__file__).with_name("assets")
        self.obstacle_images = self.load_obstacle_images()
        self.obstacles = pygame.sprite.Group()
        self.max_obstacles = 18
        self.obstacle_spawn_interval = 0.35
        self.obstacle_spawn_timer = 0.0
        self.collision_cooldown = 0.0

        for _ in range(min(8, self.max_obstacles)):
            self.spawn_obstacle()

    def load_high_score(self):
        # Équipe : On sauvegarde le meilleur score dans un bête fichier texte pour l'instant, c'est amplement suffisant, pas besoin de base de données.
        if not self.score_file.exists():
            self.score_file.write_text('0', encoding='utf-8')
            return 0
        content = self.score_file.read_text(encoding='utf-8').strip()
        if content.isdigit():
            return int(content)
        self.score_file.write_text('0', encoding='utf-8')
        return 0

    # C'est la fonction qui met à jour la position de la caméra pour suivre le joueur, elle est appelée à chaque frame depuis run()
    def update_camera(self):
        self.camera_x = self.player.position.x - SCREEN_WIDTH * 0.5
        self.camera_y = self.player.position.y - SCREEN_HEIGHT * 0.65

    # C'est la fonction qui génère une étoile à partir de coordonnées de cellule, elle utilise une fonction de hachage pour créer une distribution pseudo-aléatoire d'étoiles qui reste constante à chaque exécution du jeu.
    def star_hash(self, col, row):
        return ((col * 73856093) ^ (row * 19349663) ^ 0x9E3779B9) & 0xFFFFFFFF

    def draw_background(self):
        # Équipe : étoiles procédurales, calculées seulement autour de la caméra (RAM quasi constante).
        cell_size = 140
        start_col = math.floor(self.camera_x / cell_size) - 1
        end_col = math.floor((self.camera_x + SCREEN_WIDTH) / cell_size) + 1
        start_row = math.floor(self.camera_y / cell_size) - 1
        end_row = math.floor((self.camera_y + SCREEN_HEIGHT) / cell_size) + 1

        for col in range(start_col, end_col + 1):
            for row in range(start_row, end_row + 1):
                hash_value = self.star_hash(col, row)
                if hash_value % 100 >= 58:
                    continue

                x_offset = (hash_value >> 8) % cell_size
                y_offset = (hash_value >> 16) % cell_size
                world_x = col * cell_size + x_offset
                world_y = row * cell_size + y_offset
                screen_x = int(world_x - self.camera_x)
                screen_y = int(world_y - self.camera_y)

                radius = 1 + (hash_value % 2)
                pygame.draw.circle(self.display_surface, OFF_WHITE, (screen_x, screen_y), radius)

        launch_pad = pygame.Rect(
            int(-90 - self.camera_x),
            int(self.ground_y + 50 - self.camera_y),
            180,
            10,
        )
        pygame.draw.rect(self.display_surface, SOFT_CYAN, launch_pad, border_radius=4)

    # C'est la fonction qui dessine tous les sprites à l'écran, elle est appelée à chaque frame depuis run()
    def draw_sprites(self):
        for sprite in self.visible_sprites:
            screen_pos = (sprite.position.x - self.camera_x, sprite.position.y - self.camera_y)
            screen_rect = sprite.image.get_rect(center=screen_pos)
            self.display_surface.blit(sprite.image, screen_rect)

    #C'est la fonction qui dessine le score et les instructions à l'écran, elle est appelée à chaque frame depuis run()
    def draw_hud(self):
        score_text = self.font.render(f"Score : {self.score}   Meilleur score : {self.high_score}", True, SOFT_YELLOW)
        controls_text = self.font.render("Appuie sur ESPACE pour décoller | Gauche/Droite pour diriger", True, SOFT_YELLOW)
        speed_text = self.font.render(f"Vitesse : {self.get_speed_kmh():.1f} km/h", True, SOFT_YELLOW)

        self.display_surface.blit(score_text, (20, 18))
        self.display_surface.blit(controls_text, (20, 48))
        self.display_surface.blit(speed_text, (20, 78))

    def get_speed_kmh(self):
        velocity = getattr(self.player, "velocity", None)
        if velocity is None:
            return 0.0

        vx = getattr(velocity, "x", 0.0)
        vy = getattr(velocity, "y", 0.0)
        speed_px_s = math.hypot(vx, vy)
        speed_m_s = speed_px_s * self.px_to_meter
        return speed_m_s * 3.6

    def load_obstacle_images(self):
        if not self.assets_dir.exists():
            return []

        # On ne prend QUE les images dans le dossier "Déchets" (ou "Dechets")
        debris_dirs = [
            p for p in self.assets_dir.rglob("*")
            if p.is_dir() and p.name.lower() in ("déchets", "dechets")
        ]
        if not debris_dirs:
            return []

        allowed_ext = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        images = []

        for debris_dir in debris_dirs:
            for path in sorted(debris_dir.rglob("*")):
                if path.suffix.lower() not in allowed_ext:
                    continue
                try:
                    images.append(pygame.image.load(path.as_posix()).convert_alpha())
                except pygame.error:
                    continue

        return images

    def spawn_obstacle(self):
        if not self.obstacle_images:
            return

        cam_center_x = self.camera_x + SCREEN_WIDTH * 0.5
        cam_center_y = self.camera_y + SCREEN_HEIGHT * 0.5
        spawn_radius_x = SCREEN_WIDTH * 0.9
        spawn_radius_y = SCREEN_HEIGHT * 0.9

        x, y = cam_center_x, cam_center_y
        for _ in range(8):
            x = random.uniform(cam_center_x - spawn_radius_x, cam_center_x + spawn_radius_x)
            y = random.uniform(cam_center_y - spawn_radius_y, cam_center_y + spawn_radius_y)
            if pygame.Vector2(x, y).distance_to(self.player.position) > 180:
                break

        image = random.choice(self.obstacle_images)
        FloatingObstacle((x, y), image, [self.visible_sprites, self.obstacles])

    def update_obstacles(self, dt):
        if not self.obstacle_images:
            return

        self.obstacle_spawn_timer += dt
        while (
            self.obstacle_spawn_timer >= self.obstacle_spawn_interval
            and len(self.obstacles) < self.max_obstacles
        ):
            self.obstacle_spawn_timer -= self.obstacle_spawn_interval
            self.spawn_obstacle()

        cam_center = pygame.Vector2(
            self.camera_x + SCREEN_WIDTH * 0.5,
            self.camera_y + SCREEN_HEIGHT * 0.5,
        )
        max_dist = max(SCREEN_WIDTH, SCREEN_HEIGHT) * 1.8

        for obstacle in list(self.obstacles):
            if obstacle.position.distance_to(cam_center) > max_dist:
                obstacle.kill()
            elif random.random() < 0.002:
                obstacle.base_velocity.rotate_ip(random.uniform(-35, 35))

    def is_player_in_flight(self):
        velocity = getattr(self.player, "velocity", None)
        vy = getattr(velocity, "y", 0.0) if velocity is not None else 0.0
        return self.player.position.y < self.ground_y - 5 or abs(vy) > 15

    def handle_obstacle_collisions(self, dt):
        if not self.obstacles:
            return

        if not self.is_player_in_flight():
            self.collision_cooldown = 0.0
            return

        self.collision_cooldown = max(0.0, self.collision_cooldown - dt)
        player_radius = max(14, min(self.player.image.get_width(), self.player.image.get_height()) * 0.28)

        for obstacle in self.obstacles:
            delta = self.player.position - obstacle.position
            hit_dist = player_radius + obstacle.collision_radius

            if delta.length_squared() <= hit_dist * hit_dist:
                if self.collision_cooldown <= 0.0:
                    self.collision_cooldown = 0.45
                    self.score = max(0, self.score - 25)

                    velocity = getattr(self.player, "velocity", None)
                    if velocity is not None:
                        if delta.length_squared() == 0:
                            delta = pygame.Vector2(1, 0)
                        knockback = delta.normalize() * 150
                        velocity.x = velocity.x * 0.55 + knockback.x
                        velocity.y = velocity.y * 0.55 + knockback.y
                break

    # C'est la fonction qui met à jour le niveau, elle est appelée à chaque frame depuis run() dans game.py
    def run(self, dt):
        self.visible_sprites.update(dt)
        self.update_camera()
        self.update_obstacles(dt)
        self.handle_obstacle_collisions(dt)
        self.draw_background()
        self.draw_sprites()
        self.draw_hud()