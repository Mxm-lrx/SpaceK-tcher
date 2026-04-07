from pathlib import Path
import math
import random
import pygame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH, SOFT_YELLOW, OFF_WHITE, SOFT_CYAN
from player import Player

class FloatingObstacle(pygame.sprite.Sprite):
    obstacle_type = "base"
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



class DebrisItem(FloatingObstacle):
    obstacle_type = "debris"
    def __init__(self, position, image, groups):
        super().__init__(position, image, groups)
        w, h = image.get_size()
        scale = min(80.0 / max(1, w), 80.0 / max(1, h)) 
        self.image = pygame.transform.smoothscale(image, (max(12, int(w * scale)), max(12, int(h * scale))))
        self.collision_radius = max(10, min(self.image.get_width(), self.image.get_height()) * 0.33)

class DechetItem(FloatingObstacle):
    obstacle_type = "dechet"
    def __init__(self, position, image, groups):
        super().__init__(position, image, groups)
        w, h = image.get_size()
        scale = min(40.0 / max(1, w), 40.0 / max(1, h)) 
        self.image = pygame.transform.smoothscale(image, (max(12, int(w * scale)), max(12, int(h * scale))))
        self.collision_radius = max(10, min(self.image.get_width(), self.image.get_height()) * 0.33)

class Level:
    # C'est la classe qui fait tout le travaille pour faire tourner le niveau, elle gère la caméra, les étoiles de fond, le score, etc. C'est un peu la classe centrale du projet.
    def __init__(self, surface, level_type='mixed', end_y=None, player_start_pos=None, player_velocity=None):
        self.display_surface = surface
        self.ground_y = 0
        self.level_type = level_type
        self.end_y = end_y

        from utils import load_sound
        self.crash_sound = load_sound('bruit de collision.wav')

        self.visible_sprites = pygame.sprite.Group()
        start_y = player_start_pos[1] if player_start_pos else self.ground_y
        start_x = player_start_pos[0] if player_start_pos else 0
        
        self.player = Player(
            (start_x, start_y),
            [self.visible_sprites],
            self.ground_y
        )
        if player_velocity:
            self.player.velocity = pygame.Vector2(player_velocity)
            self.player.launched = True

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
        
        # Charger Sol.png pour la phase de décollage
        sol_path = self.assets_dir / "Sol.png"
        self.ground_image = None
        if sol_path.exists():
            try:
                self.ground_image = pygame.image.load(sol_path.as_posix()).convert_alpha()
            except pygame.error:
                pass
        
        if self.level_type == 'debris':
            # Level 1 première phase : moins de débris pour être plus facile
            self.max_obstacles = 30
            self.obstacle_spawn_interval = 0.20
        else:
            self.max_obstacles = 45
            self.obstacle_spawn_interval = 0.15
            
        self.obstacle_spawn_timer = 0.0
        self.collision_cooldown = 0.0
        
        # Limite d'atmosphère : pas de débris en-dessous de cette altitude (Y négatif en montée)
        # En Y=-4000, on est en atmosphère, pas de débris générés
        if self.level_type == 'debris':
            self.atmosphere_altitude = -4000  # Y du début de l'atmosphère (l'espace)
        else:
            self.atmosphere_altitude = -5000  # Niveau 2 : atmosphère plus haute

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
        # Gradient du ciel bleu au ciel noir (espace) basé sur l'altitude du joueur
        player_y = self.player.position.y
        
        # Transition smooth du bleu vers le noir
        # À Y=0 (sol): bleu (135, 206, 235)
        # À atmosphere_altitude: noir (20, 20, 40)
        if self.level_type == 'debris':
            sky_blue = (135, 206, 235)  # Ciel bleu classique
            atmosphere_start = 0  # Début du dégradé au sol
        else:
            sky_blue = (100, 160, 240)  # Bleu doux
            atmosphere_start = -1000
        
        space_black = (20, 20, 40)  # Noir de l'espace
        
        # Calcul de la transition (0.0 = bleu pur, 1.0 = noir pur)
        transition_range = self.atmosphere_altitude - atmosphere_start
        if transition_range == 0:
            transition = 0.0 if player_y > self.atmosphere_altitude else 1.0
        else:
            transition = max(0.0, min(1.0, (player_y - atmosphere_start) / transition_range))
        
        # Interpolation linéaire entre ciel bleu et noir de l'espace
        bg_color = (
            int(sky_blue[0] + (space_black[0] - sky_blue[0]) * transition),
            int(sky_blue[1] + (space_black[1] - sky_blue[1]) * transition),
            int(sky_blue[2] + (space_black[2] - sky_blue[2]) * transition),
        )
        self.display_surface.fill(bg_color)
        
        # Afficher le sol (Sol.png) s'il existe et si on est en phase de décollage
        if self.ground_image and self.player.position.y > self.atmosphere_altitude:
            ground_width, ground_height = self.ground_image.get_size()
            # Position du sol au ground_y, tile horizontalement avec la caméra
            screen_ground_y = int(self.ground_y - self.camera_y)
            
            # Boucle de tiling horizontal
            x_offset = int(self.camera_x) % ground_width
            screen_x = -x_offset
            while screen_x < SCREEN_WIDTH:
                screen_rect = self.ground_image.get_rect(topleft=(screen_x, screen_ground_y))
                self.display_surface.blit(self.ground_image, screen_rect)
                screen_x += ground_width
        
        # Équipe : étoiles procédurales, calculées seulement autour de la caméra (RAM quasi constante).
        # Les étoiles apparaissent quand transition > 0.3 (environ -1400 pour le niveau 1)
        if transition > 0.3:
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
        images = {"debris": [], "dechet": []}
        if not self.assets_dir.exists(): return images
        allowed_ext = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        
        for p in self.assets_dir.rglob("*"):
            if not p.is_dir(): continue
            name_lower = p.name.lower()
            if name_lower in ("déchets", "dechets"):
                cat = "dechet"
            elif name_lower in ("débris", "debris"):
                cat = "debris"
            else:
                continue
                
            for path in sorted(p.rglob("*")):
                if path.suffix.lower() not in allowed_ext: continue
                try:
                    images[cat].append((path.stem, pygame.image.load(path.as_posix()).convert_alpha()))
                except pygame.error: continue
        return images

    def spawn_obstacle(self):
        all_imgs = self.obstacle_images.get("debris", []) + self.obstacle_images.get("dechet", [])
        if not all_imgs: return
        
        # Pas de débris tant qu'on est dans l'atmosphère (Y > atmosphere_altitude)
        if self.player.position.y > self.atmosphere_altitude:
            return
        
        if self.level_type == 'debris':
            is_debris = True
        else:
            is_debris = random.random() < 0.4
            
        choices = self.obstacle_images.get("debris", []) if is_debris else self.obstacle_images.get("dechet", [])
        if not choices: choices = all_imgs
        
        item_name, image = random.choice(choices)
        
        cam_center_x = self.camera_x + SCREEN_WIDTH * 0.5
        cam_center_y = self.camera_y + SCREEN_HEIGHT * 0.5
        spawn_radius_x = SCREEN_WIDTH * 1.2
        spawn_radius_y = SCREEN_HEIGHT * 1.2
        
        # Apparition majoritairement au-dessus car la fusée monte (65%)
        rand_val = random.random()
        if rand_val < 0.65:
            # Apparition au-dessus (Haut)
            x = self.camera_x + random.uniform(-200, SCREEN_WIDTH + 200)
            y = self.camera_y - random.uniform(100, 1000)
        elif rand_val < 0.85:
            # Apparition sur les côtés (Gauche / Droite)
            base_x = self.camera_x - random.uniform(100, 400) if random.random() < 0.5 else self.camera_x + SCREEN_WIDTH + random.uniform(100, 400)
            x = base_x
            y = self.camera_y + random.uniform(-500, SCREEN_HEIGHT + 200)
        else:
            # Apparition en-dessous (Bas)
            x = self.camera_x + random.uniform(-200, SCREEN_WIDTH + 200)
            y = self.camera_y + SCREEN_HEIGHT + random.uniform(100, 600)
            
        cls = DebrisItem if is_debris else DechetItem
        obj = cls((x, y), image, [self.visible_sprites, self.obstacles])
        obj.item_name = item_name

    def update_obstacles(self, dt):
        if not self.obstacle_images.get("debris") and not self.obstacle_images.get("dechet"):
            return

        self.obstacle_spawn_timer += dt
        while (
            self.obstacle_spawn_timer >= self.obstacle_spawn_interval
            and len(self.obstacles) < self.max_obstacles
        ):
            self.obstacle_spawn_timer -= self.obstacle_spawn_interval
            self.spawn_obstacle()

        for obstacle in list(self.obstacles):
            # Nettoie les obstacles trop éloignés (notamment trop bas puisque la fusée monte)
            if (obstacle.position.x < self.camera_x - SCREEN_WIDTH) or \
               (obstacle.position.x > self.camera_x + SCREEN_WIDTH * 2) or \
               (obstacle.position.y > self.camera_y + SCREEN_HEIGHT * 1.8) or \
               (obstacle.position.y < self.camera_y - SCREEN_HEIGHT * 2.5):
                obstacle.kill()
            # Retire les obstacles tant qu'on est dans l'atmosphère
            elif self.player.position.y > self.atmosphere_altitude:
                obstacle.kill()
            elif random.random() < 0.002:
                obstacle.base_velocity.rotate_ip(random.uniform(-35, 35))

    def is_player_in_flight(self):
        velocity = getattr(self.player, "velocity", None)
        vy = getattr(velocity, "y", 0.0) if velocity is not None else 0.0
        return self.player.position.y < self.ground_y - 5 or abs(vy) > 15

    def handle_obstacle_collisions(self, dt, game_instance):
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
                if obstacle.obstacle_type == "debris":
                    import utils
                    img = utils.load_texture("explode.png")
                    w, h = self.player.image.get_size()
                    self.player.image = pygame.transform.smoothscale(img, (w, h))
                    
                    if hasattr(self, 'crash_sound') and self.crash_sound:
                        self.crash_sound.play()
                        
                    if len(game_instance.collected_trash) > 0:
                        game_instance.change_state("sorting_level")
                    else:
                        game_instance.change_state("game_over")
                    break
                elif obstacle.obstacle_type == "dechet":
                    game_instance.collected_trash.append((getattr(obstacle, "item_name", "Inconnu"), obstacle.image.copy()))
                    game_instance.score += 10
                    obstacle.kill()
                    # on ne break pas, on continue la collecte !

    # C'est la fonction qui met à jour le niveau, elle est appelée à chaque frame depuis run() dans game.py
    def run(self, dt, game_instance=None):
        self.visible_sprites.update(dt)
        self.update_camera()
        self.update_obstacles(dt)
        if game_instance:
            self.handle_obstacle_collisions(dt, game_instance)
        # Met à jour le HUD avec le score
        if game_instance:
            self.score = game_instance.score
            self.high_score = game_instance.high_score
        self.draw_background()
        self.draw_sprites()
        self.draw_hud()
        
        if self.end_y is not None and self.player.position.y < self.end_y:
            return "completed"