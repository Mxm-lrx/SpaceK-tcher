"""
========================================================================
                         GESTION DES NIVEAUX - SpaceK'tcher
========================================================================

Ce module gère TOUTE LA PHYSIQUE ET LA LOGIQUE du jeu:
  1. CLASSES D'OBSTACLES: DebrisItem (dommage), DechetItem (collecte)
  2. CLASSE LEVEL: Le cœur du moteur - gère caméra, rendu, collisions
  3. SYSTÈMES VISUELS: Fond étoilé, dégradé ciel→espace, HUD
  4. MÉCANIQUE DE JEU: Spawning obstacles, détection collisions
  5. EFFETS SPÉCIAUX: Particules, shakes, trajectoire prévisionnelle

ARCHITECTURE DU LEVEL:
- FloatingObstacle: Classe de base pour tous les objets volants
  ├─ DebrisItem: Objets dangereux (causent  Game Over si collision)
  └─ DechetItem: Objets à collecter (donnent points)
- Level: Gère un niveau complet (début du jeu jusqu'à atteindre end_y)

FLUX DE JEU:
1. Level.__init__() crée le joueur et les systèmes de particules
2. Level.run(dt) à chaque frame:
   - update_camera() suit le joueur
   - update_obstacles() spawn/tue les obstacles
   - handle_obstacle_collisions() détecte les contacts
   - Rendu: background → sprites → HUD → particles
3. Retour "completed" quand le joueur atteint end_y (altitude max)

SYSTÈME DE PARALLAXE D'ÉTOILES:
- 4 couches avec vitesses différentes (0.15 à 0.8)
- Utilise un système de HACHAGE pour générer les positions sans les stocker
- Les étoiles scintillent progressivement basé sur l'altitude
========================================================================
"""
from pathlib import Path
import math
import random
import pygame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH, SOFT_YELLOW, OFF_WHITE, SOFT_CYAN
from player import Player
from particle_system import (
    ParticleEmitter, ShootingStarManager, ScreenShake,
    SpeedLines, CometManager
)

class FloatingObstacle(pygame.sprite.Sprite):
    """Classe de base pour tous les objets volants dans le niveau (débris, déchets).
    
    Les obstacles "flottent" dans l'espace avec:
    - Une vélocité de base (mouvement rectiligne)
    - Un "wobble" (oscillation sinusoïdale) pour donner l'impression de flottement
    - Des variations aléatoires de taille pour la diversité visuelle
    
    Attributs:
        obstacle_type: Type d'obstacle ("base", "debris", "dechet")
        position: Coordonnées du monde (Vector2)
        base_velocity: Mouvement de base en pixels/seconde
        wobble_strength: Force de l'oscillation (pixels d'amplitude)
        frequency: Fréquence de l'oscillation sin/cos
        collision_radius: Rayon pour détection de collision circulaire
    """
    obstacle_type = "base"
    
    def __init__(self, position, image, groups):
        """Initialise un obstacle.
        
        Args:
            position: Tuple (x, y) de la position de spawn
            image: Image pygame du sprite
            groups: Liste des groupe pygame pour le rendu
        """
        super().__init__(groups)
        
        # REDIMENSIONNEMENT ALÉATOIRE pour éviter que tous les obstacles aient la même taille
        scale = random.uniform(0.18, 0.42)  # Entre 18% et 42% de taille originale
        w, h = image.get_size()
        self.image = pygame.transform.smoothscale(
            image, (max(12, int(w * scale)), max(12, int(h * scale)))
        )
        
        self.position = pygame.Vector2(position)
        
        # MOUVEMENT: chaque obstacle a une direction/vitesse unique
        # Vx: -120 à +120 (gauche-droite)
        # Vy: -100 à +140 (haut-bas, très variable)
        self.base_velocity = pygame.Vector2(
            random.uniform(-120, 120),
            random.uniform(-100, 140),
        )
        
        # WOBBLE (oscillation): crée un mouvement naturel de flottement
        self.frequency = random.uniform(0.6, 1.8)  # Hz d'oscillation
        self.phase = random.uniform(0, math.tau)  # Décalage de phase pour variation
        self.wobble_strength = random.uniform(15, 65)  # Ampleur de l'oscillation
        
        self.age = 0.0  # Temps écoulé depuis la création
        
        # Rayon de collision (cercle): ~33% de la taille du sprite
        self.collision_radius = max(10, min(self.image.get_width(), self.image.get_height()) * 0.33)

    def update(self, dt):
        """Met à jour la position avec mouvement + wobble.
        
        Le wobble crée une oscillation sinusoïdale pour donner l'impression
        que l'objet "lévite" plutôt que de simplement glisser lineairement.
        
        Args:
            dt: Delta time (temps depuis la dernière frame en secondes)
        """
        self.age += dt
        
        # Créer une oscillation 2D (X et Y avec fréquences différentes pour l'effet 3D)
        wobble = pygame.Vector2(
            math.sin(self.age * self.frequency + self.phase),           # Oscillation X
            math.cos(self.age * (self.frequency * 0.83) + self.phase),  # Oscillation Y (fréquence décalée)
        ) * self.wobble_strength  # Appliquer la force
        
        # Mettre à jour la position: mouvement linéaire + oscillation
        self.position += (self.base_velocity + wobble) * dt



class DebrisItem(FloatingObstacle):
    """Débris dangereux qui causent une explosion si la fusée les touche.
    
    Les débris sont plus GRANDS (jusqu'à 80px) et visibles.
    Si le joueur les heurte: Game Over + explosion spectaculaire.
    """
    obstacle_type = "debris"
    
    def __init__(self, position, image, groups):
        """Initialise un débris (plus grand que la classe parente)."""
        super().__init__(position, image, groups)
        w, h = image.get_size()
        # Limiter à max 80px pour pas trop grosse collision visuelle
        scale = min(80.0 / max(1, w), 80.0 / max(1, h)) 
        self.image = pygame.transform.smoothscale(image, (max(12, int(w * scale)), max(12, int(h * scale))))
        self.collision_radius = max(10, min(self.image.get_width(), self.image.get_height()) * 0.33)

class DechetItem(FloatingObstacle):
    """Déchet collectible qui donne des points si la fusée le touche.
    
    Les déchets sont plus PETITS (jusqu'à 40px) que les débris.
    Si le joueur les collecte:
    - +10 points au score
    - Effet visuel d'étincelles jaunes
    - Objet ajouté au tri pour le niveau de tri (sorting_level)
    """
    obstacle_type = "dechet"
    
    def __init__(self, position, image, groups):
        """Initialise un déchet (plus petit que la classe parente)."""
        super().__init__(position, image, groups)
        w, h = image.get_size()
        # Limiter à max 40px (plus petit pour that they're not too dangerous)
        scale = min(40.0 / max(1, w), 40.0 / max(1, h)) 
        self.image = pygame.transform.smoothscale(image, (max(12, int(w * scale)), max(12, int(h * scale))))
        self.collision_radius = max(10, min(self.image.get_width(), self.image.get_height()) * 0.33)

class Level:
    """Gestionnaire complet d'un niveau de jeu.
    
    La classe Level est le CŒUR DU JEU - elle gère:
    - La caméra qui suit le joueur
    - Le spawning et la suppression des obstacles
    - La détection des collisions joueur-obstacles
    - Le rendu complet (fond, sprites, HUD, effets)
    - Les systèmes de particules (explosions, étincelles, flammes)
    - Le système d'étoiles parallaxé
    - Le score et les high scores
    
    DEUX MODE DE NIVEAU:
    - 'debris': Niveau 1 (petit nombre d'obstacles, atmosphère)
    - 'mixed': Niveau 2 (plus d'obstacles, espace pur)
    
    FLUX PRINCIPAL: run(dt) DOIT être appelée à chaque frame depuis main.py
    """
    
    def __init__(self, surface, level_type='mixed', end_y=None, player_start_pos=None, player_velocity=None):
        """Initialise un nouveau niveau.
        
        Args:
            surface: Surface pygame où dessiner (l'écran)
            level_type: 'debris' (niveau 1) ou 'mixed' (niveau 2)
            end_y: Y-coordinate de la ligne d'arrivée (altitude max)
            player_start_pos: Tuple (x, y) position de spawn du joueur
            player_velocity: Tuple (vx, vy) pour continuer avec la vélocité du niveau précédent
        """
        self.display_surface = surface
        self.ground_y = 0  # Position du sol (Y=0 par défaut)
        self.level_type = level_type
        self.end_y = end_y  # Altitude finale à atteindre pour compléter le niveau

        # Timing et textes
        self.level_time = 0.0  # Temps écoulé (pour anims)
        if self.level_type == 'debris':
            self.title_text = "Niveau 1 : L'Échappée Terrestre"
        else:
            self.title_text = "Niveau 2 : Récolte en Orbite"
        self.title_font = pygame.font.Font(None, 64)

        # Charger le son de collision
        from utils import load_sound
        self.crash_sound = load_sound('bruit de collision.wav')

        # CRÉATION DU JOUEUR
        self.visible_sprites = pygame.sprite.Group()
        start_y = player_start_pos[1] if player_start_pos else self.ground_y
        start_x = player_start_pos[0] if player_start_pos else 0
        
        self.player = Player(
            (start_x, start_y),
            [self.visible_sprites],
            self.ground_y
        )
        
        # Si on vient du niveau précédent, garder la vélocité
        if player_velocity:
            self.player.velocity = pygame.Vector2(player_velocity)
            self.player.launched = True

        # INTERFACE UTILISATEUR
        self.font = pygame.font.Font(None, 32)
        
        # CAMÉRA: suit le joueur avec décalage (60% dans la hauteur pour voir devant)
        self.camera_x = self.player.position.x - SCREEN_WIDTH * 0.5
        self.camera_y = self.player.position.y - SCREEN_HEIGHT * 0.65
        
        # SCORE
        self.score = 0
        self.score_file = Path(__file__).with_name('score.txt')
        self.high_score = self.load_high_score()
        self.px_to_meter = 1.0  # Conversion pixel→mètre pour la vitesse (affichage)

        # SYSTÈMES DE PARTICULES AAA (Advanced Visual Effects)
        self.particle_emitter = ParticleEmitter(max_particles=800)
        self.shooting_stars = ShootingStarManager(spawn_rate=0.25)
        self.screen_shake = ScreenShake()
        
        # Effets visuels additionnels
        self.speed_lines = SpeedLines()
        self.comet_manager = CometManager(spawn_rate=0.03)
        
        # PARALLAXE D'ÉTOILES: 4 couches avec vitesses différentes
        # Plus loin = plus lent (parallaxe naturelle)
        self.star_layers = [
            {'speed': 0.15, 'density': 30, 'size_range': (1, 1), 'brightness': 120},  # Très lointaines, petites
            {'speed': 0.3, 'density': 22, 'size_range': (1, 2), 'brightness': 180},   # Lointaines
            {'speed': 0.5, 'density': 15, 'size_range': (1, 2), 'brightness': 220},   # Moyennes
            {'speed': 0.8, 'density': 8, 'size_range': (2, 3), 'brightness': 255},    # Proches, grosses et lumineuses
        ]
        
        # Animation du score (compte lentement vers le vrai score)
        self.displayed_score = 0
        self.score_animation_speed = 100  # points/seconde

        # CHARGEMENT DES IMAGES D'OBSTACLES
        self.assets_dir = Path(__file__).with_name("assets")
        self.obstacle_images = self.load_obstacle_images()
        self.obstacles = pygame.sprite.Group()
        
        # Charger Sol.png pour afficher le terrain au décollage
        sol_path = self.assets_dir / "Sol.png"
        self.ground_image = None
        if sol_path.exists():
            try:
                self.ground_image = pygame.image.load(sol_path.as_posix()).convert_alpha()
            except pygame.error:
                pass
        
        # CONFIGURATION DES NIVEAUX
        if self.level_type == 'debris':
            # Niveau 1: peu d'obstacles, plus facile
            self.max_obstacles = 15
            self.obstacle_spawn_interval = 0.5  # spawn tous les 0.5 sec
        else:
            # Niveau 2: beaucoup d'obstacles, difficile
            self.max_obstacles = 30
            self.obstacle_spawn_interval = 0.25  # spawn tous les 0.25 sec
            
        self.obstacle_spawn_timer = 0.0
        self.collision_cooldown = 0.0
        
        # Limite d'atmosphère: pas de débris en-dessous de cette altitude
        # Y négatif = vers le haut (montée). Quand Y < atmosphere_altitude, on est en espace
        if self.level_type == 'debris':
            self.atmosphere_altitude = -4000  # En-dessous: espace pur
        else:
            self.atmosphere_altitude = -5000  # Altitude plus haute

        # Pré-remplir avec quelques obstacles au démarrage
        for _ in range(min(5, self.max_obstacles)):
            self.spawn_obstacle()

    def load_high_score(self):
        """Charge le best score depuis le fichier score.txt.
        
        Utilise un simple fichier texte au lieu d'une base de données.
        C'est amplement suffisant pour stocker juste un nombre.
        """
        if not self.score_file.exists():
            self.score_file.write_text('0', encoding='utf-8')
            return 0
        content = self.score_file.read_text(encoding='utf-8').strip()
        if content.isdigit():
            return int(content)
        self.score_file.write_text('0', encoding='utf-8')
        return 0

    def update_camera(self):
        """Met à jour la position de la caméra pour suivre le joueur.
        
        La caméra ne suit pas exactement le joueur:
        - X: centré sur le joueur (50% de l'écran)
        - Y: légèrement devant le joueur (65% en bas = voir vers le haut)
        
        Cela donne une meilleure perspective pour anticiper les obstacles.
        """
        self.camera_x = self.player.position.x - SCREEN_WIDTH * 0.5
        self.camera_y = self.player.position.y - SCREEN_HEIGHT * 0.65

    def star_hash(self, col, row):
        """Génère une valeur pseudo-aléatoire basée sur des coordonnées de grille.
        
        SYSTÈME DE PARALAXE D'ÉTOILES:
        Plutôt que de stocker 1000s d'étoiles, on utilise une fonction de hachage
        pour générer les positions procéduralement.
        
        Avantage: Même résultat à chaque run + mémoire constants
        Les étoiles apparaissent au bon endroit automatiquement.
        
        Args:
            col, row: Coordonnées de cellule dans la grille (160x160 pixels)
            
        Returns:
            Valeur aléatoire stable basée sur col, row (deterministic)
        """
        return ((col * 73856093) ^ (row * 19349663) ^ 0x9E3779B9) & 0xFFFFFFFF

    def draw_background(self):
        """Dessine tout l'arrière-plan (ciel/espace, sol, étoiles, pad).
        
        C'est LA fonction centrale du rendu visuel. Elle gère:
        1. Dégradé ciel bleu → noir (transition vers l'espace)
        2. Afficher le sol graphique (Sol.png en tiling)
        3. Dessiner les couches d'étoiles parallaxées
        4. Afficher comètes et étoiles filantes
        5. Dessiner le pad de lancement avec glow
        """
        # Appliquer le tremblement d'écran (screen shake) aux coordonnées caméra
        shake_cam_x, shake_cam_y = self.screen_shake.apply(self.camera_x, self.camera_y)
        
        # TRANSITION DU CIEL (Bleu → Noir basée sur altitude du joueur)
        player_y = self.player.position.y
        
        # Configuration des couleurs de transition
        if self.level_type == 'debris':
            sky_blue = (135, 206, 235)  # Ciel bleu classique (jour)
            atmosphere_start = 0  # Transition commence au sol
        else:
            sky_blue = (100, 160, 240)  # Bleu doux (déjà en altitude)
            atmosphere_start = -1000
        
        space_black = (15, 15, 35)  # Noir de l'espace profond
        
        # Calculer le ratio de transition (0.0 = bleu, 1.0 = noir)
        transition_range = self.atmosphere_altitude - atmosphere_start
        if transition_range == 0:
            transition = 0.0 if player_y > self.atmosphere_altitude else 1.0
        else:
            # Interpolation linéaire entre les deux altitudes
            transition = max(0.0, min(1.0, (player_y - atmosphere_start) / transition_range))
        
        # Stocker la transition pour les autres systèmes (étoiles, etc)
        self.space_transition = transition
        
        # Interpole entre les 2 couleurs
        bg_color = (
            int(sky_blue[0] + (space_black[0] - sky_blue[0]) * transition),
            int(sky_blue[1] + (space_black[1] - sky_blue[1]) * transition),
            int(sky_blue[2] + (space_black[2] - sky_blue[2]) * transition),
        )
        self.display_surface.fill(bg_color)  # Remplir tout l'écran avec cette couleur
        
        # AFFICHER LE SOL (graphique)
        if self.ground_image and self.player.position.y > self.atmosphere_altitude:
            ground_width, ground_height = self.ground_image.get_size()
            # Position du sol au ground_y, tiling horizontal avec parallaxe de caméra
            screen_ground_y = int(self.ground_y - shake_cam_y)
            
            # Boucle de tiling: répéter le sol horizontalement
            x_offset = int(shake_cam_x) % ground_width
            screen_x = -x_offset
            while screen_x < SCREEN_WIDTH:
                screen_rect = self.ground_image.get_rect(topleft=(screen_x, screen_ground_y))
                self.display_surface.blit(self.ground_image, screen_rect)
                screen_x += ground_width
        
        # ÉTOILES parallaxées (4 couches avec vitesses différentes)
        if transition > 0.2:  # Commencer à montrer les étoiles à 20% de transition
            for layer in self.star_layers:
                self._draw_star_layer(layer, shake_cam_x, shake_cam_y, transition)
        
        # COMÈTES spectaculaires (seulement en espace)
        self.comet_manager.draw(self.display_surface, shake_cam_x, shake_cam_y)
        
        # ÉTOILES FILANTES (effet cosmétique)
        self.shooting_stars.draw(self.display_surface, shake_cam_x, shake_cam_y)

        # PAD DE LANCEMENT avec effet de glow cyan
        pad_x = int(-90 - shake_cam_x)
        pad_y = int(self.ground_y + 50 - shake_cam_y)
        
        # Glow du pad (seulement au sol, pas dans l'espace)
        if transition < 0.5:
            glow_surf = pygame.Surface((220, 30), pygame.SRCALPHA)
            # Plusieurs cercles concentriques pour l'effet de rayonnement
            for i in range(3):
                alpha = 30 - i * 10
                pygame.draw.rect(glow_surf, (*SOFT_CYAN[:3], alpha), 
                               (10 - i * 5, 5 - i * 2, 200 + i * 10, 20 + i * 4), 
                               border_radius=8)
            self.display_surface.blit(glow_surf, (pad_x - 10, pad_y - 5), 
                                     special_flags=pygame.BLEND_ADD)
        
        # Dessiner le pad (rectangle blanc)
        launch_pad = pygame.Rect(pad_x, pad_y, 180, 10)
        pygame.draw.rect(self.display_surface, SOFT_CYAN, launch_pad, border_radius=4)
    
    def _draw_star_layer(self, layer, cam_x, cam_y, transition):
        """Dessine une couche d'étoiles avec effet de parallaxe"""
        cell_size = 160
        parallax_x = cam_x * layer['speed']
        parallax_y = cam_y * layer['speed']
        
        start_col = math.floor(parallax_x / cell_size) - 1
        end_col = math.floor((parallax_x + SCREEN_WIDTH) / cell_size) + 1
        start_row = math.floor(parallax_y / cell_size) - 1
        end_row = math.floor((parallax_y + SCREEN_HEIGHT) / cell_size) + 1

        for col in range(start_col, end_col + 1):
            for row in range(start_row, end_row + 1):
                hash_value = self.star_hash(col, row)
                if hash_value % 100 >= layer['density']:
                    continue

                x_offset = (hash_value >> 8) % cell_size
                y_offset = (hash_value >> 16) % cell_size
                world_x = col * cell_size + x_offset
                world_y = row * cell_size + y_offset
                screen_x = int(world_x - parallax_x)
                screen_y = int(world_y - parallax_y)

                # Taille et luminosité basées sur le hash
                size = layer['size_range'][0] + (hash_value % 3) * (layer['size_range'][1] - layer['size_range'][0]) // 2
                
                # Scintillement subtil
                twinkle = 0.7 + 0.3 * math.sin((pygame.time.get_ticks() / 1000) * (hash_value % 5 + 1) + hash_value)
                brightness = int(layer['brightness'] * transition * twinkle)
                color = (brightness, brightness, min(255, brightness + 20))
                
                pygame.draw.circle(self.display_surface, color, (screen_x, screen_y), size)

    # C'est la fonction qui dessine tous les sprites à l'écran, elle est appelée à chaque frame depuis run()
    def draw_sprites(self):
        shake_cam_x, shake_cam_y = self.screen_shake.apply(self.camera_x, self.camera_y)
        
        # Dessiner d'abord les obstacles avec un léger glow pour les déchets
        for obstacle in self.obstacles:
            screen_pos = (obstacle.position.x - shake_cam_x, obstacle.position.y - shake_cam_y)
            screen_rect = obstacle.image.get_rect(center=screen_pos)
            
            # Glow pour les déchets collectables
            if obstacle.obstacle_type == "dechet":
                glow_size = max(obstacle.image.get_width(), obstacle.image.get_height()) + 10
                glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                glow_color = (255, 255, 100, 40)  # Jaune transparent
                pygame.draw.circle(glow_surf, glow_color, (glow_size // 2, glow_size // 2), glow_size // 2)
                self.display_surface.blit(glow_surf, 
                                         (screen_pos[0] - glow_size // 2, screen_pos[1] - glow_size // 2),
                                         special_flags=pygame.BLEND_ADD)
            
            self.display_surface.blit(obstacle.image, screen_rect)
        
        # Dessiner le joueur avec effet de glow
        player = self.player
        player_screen_pos = (player.position.x - shake_cam_x, player.position.y - shake_cam_y)
        

        
        # Dessiner la fusée
        player_rect = player.image.get_rect(center=player_screen_pos)
        self.display_surface.blit(player.image, player_rect)
        
        # Projection de trajectoire (quand la fusée est lancée)
        if player.launched:
            self._draw_trajectory_prediction(shake_cam_x, shake_cam_y)
        
        # Dessiner les particules au-dessus
        self.particle_emitter.draw(self.display_surface, shake_cam_x, shake_cam_y)
    
    def _draw_trajectory_prediction(self, camera_x, camera_y):
        """Dessine une projection de la trajectoire future de la fusée"""
        # Paramètres de simulation
        sim_x = float(self.player.position.x)
        sim_y = float(self.player.position.y)
        sim_vx = float(self.player.velocity.x)
        sim_vy = float(self.player.velocity.y)
        sim_angle = self.player.angle
        
        # Paramètres physiques (copiés du player)
        gravity = self.player.gravity
        thrust = self.player.thrust_power
        drag = self.player.linear_drag
        
        # Vérifier si boost actif
        keys = pygame.key.get_pressed()
        boost_mult = 3.0 if keys[pygame.K_z] else 1.0
        
        points = []
        dt_sim = 0.05  # Pas de simulation
        
        for i in range(60):  # Simuler ~3 secondes
            # Calculer la direction de poussée
            rad = math.radians(sim_angle)
            forward_x = -math.sin(rad)
            forward_y = -math.cos(rad)
            
            # Accélération
            acc_x = forward_x * thrust * boost_mult
            acc_y = gravity + forward_y * thrust * boost_mult
            
            # Mise à jour vélocité
            sim_vx += acc_x * dt_sim
            sim_vy += acc_y * dt_sim
            sim_vx *= (1.0 - drag * dt_sim)
            sim_vy *= (1.0 - drag * dt_sim)
            
            # Mise à jour position
            sim_x += sim_vx * dt_sim
            sim_y += sim_vy * dt_sim
            
            # Convertir en coordonnées écran
            screen_x = int(sim_x - camera_x)
            screen_y = int(sim_y - camera_y)
            
            # Arrêter si hors écran
            if screen_y > SCREEN_HEIGHT + 100 or screen_y < -500:
                break
            
            points.append((screen_x, screen_y))
        
        # Dessiner les points de trajectoire avec dégradé
        for i, (px, py) in enumerate(points):
            if i % 2 != 0:  # Un point sur deux pour effet pointillé
                continue
            
            # Dégradé de transparence
            alpha = int(180 * (1 - i / len(points))) if points else 0
            size = max(1, 4 - i // 15)
            
            if alpha > 10 and 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                dot_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                color = (255, 255, 255, alpha)
                pygame.draw.circle(dot_surf, color, (size, size), size)
                self.display_surface.blit(dot_surf, (px - size, py - size))

    #C'est la fonction qui dessine le score et les instructions à l'écran, elle est appelée à chaque frame depuis run()
    def draw_hud(self, dt):
        """Affiche TOUS les éléments d'interface utilisateur (HUD).
        
        Inclut:
        - Score (animé)
        - Meilleur score
        - Vitesse de la fusée
        - Indicateur d'altitude (barre de progression)
        - Indicateur de Boost actif
        - Contrôles (fade après 8 sec)
        - Titre du niveau (animation in/out)
        """
        # ANIMATION DU SCORE (compte progressivement vers la vraie valeur)
        if self.displayed_score < self.score:
            self.displayed_score = min(self.score, self.displayed_score + self.score_animation_speed * dt)
        elif self.displayed_score > self.score:
            self.displayed_score = self.score
        
        display_score = int(self.displayed_score)
        
        # Fond semi-transparent pour le HUD (plus lisible)
        hud_bg = pygame.Surface((350, 120), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 100))
        pygame.draw.rect(hud_bg, (255, 255, 255, 50), hud_bg.get_rect(), 2, border_radius=10)
        self.display_surface.blit(hud_bg, (10, 10))
        
        # Score avec effet de couleur quand il change
        score_color = SOFT_YELLOW if self.displayed_score == self.score else (100, 255, 100)
        score_text = self.font.render(f"Score : {display_score}", True, score_color)
        hs_text = self.font.render(f"Meilleur : {self.high_score}", True, (200, 200, 200))
        
        self.display_surface.blit(score_text, (25, 22))
        self.display_surface.blit(hs_text, (25, 48))
        
        # Vitesse avec effet visuel
        speed_kmh = self.get_speed_kmh()
        speed_color = SOFT_YELLOW
        if speed_kmh > 500:
            speed_color = (255, 150, 50)  # Orange pour vitesse élevée
        if speed_kmh > 800:
            speed_color = (255, 100, 100)  # Rouge pour très haute vitesse
        
        speed_text = self.font.render(f"Vitesse : {speed_kmh:.0f} km/h", True, speed_color)
        self.display_surface.blit(speed_text, (25, 74))
        
        # Indicateur d'altitude / progression (barre verticale à droite)
        if self.end_y is not None:
            self._draw_altitude_indicator()
        
        # Indicateur de boost
        keys = pygame.key.get_pressed()
        if keys[pygame.K_z] and self.player.launched:
            boost_text = self.font.render("⚡ BOOST ⚡", True, (100, 200, 255))
            boost_rect = boost_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
            
            # Fond pulsant
            pulse = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() / 100)
            glow_surf = pygame.Surface((boost_rect.width + 40, boost_rect.height + 20), pygame.SRCALPHA)
            glow_color = (100, 200, 255, int(80 * pulse))
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=10)
            self.display_surface.blit(glow_surf, (boost_rect.x - 20, boost_rect.y - 10))
            self.display_surface.blit(boost_text, boost_rect)
        
        # Contrôles (plus discret en bas)
        if self.level_time < 8.0:  # Afficher les contrôles seulement au début
            alpha = int(255 * max(0, 1 - self.level_time / 8.0))
            controls_surf = pygame.Surface((500, 30), pygame.SRCALPHA)
            small_font = pygame.font.Font(None, 26)
            controls_text = small_font.render("ESPACE: Décoller  |  ←/→: Diriger  |  Z: Boost", True, (200, 200, 200, alpha))
            controls_surf.blit(controls_text, (0, 0))
            self.display_surface.blit(controls_surf, (SCREEN_WIDTH // 2 - 230, SCREEN_HEIGHT - 40))

        # Animation du titre de niveau
        if self.level_time < 4.0:
            self._draw_level_title()
    
    def _draw_altitude_indicator(self):
        """Dessine un indicateur de progression verticale élégant"""
        bar_height = 200
        bar_width = 12
        bar_x = SCREEN_WIDTH - 35
        bar_y = SCREEN_HEIGHT // 2 - bar_height // 2
        
        # Calcul de la progression
        start_y = self.ground_y
        progress = max(0, min(1, (start_y - self.player.position.y) / (start_y - self.end_y)))
        
        # Fond de la barre
        bg_rect = pygame.Rect(bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4)
        pygame.draw.rect(self.display_surface, (30, 30, 50), bg_rect, border_radius=6)
        pygame.draw.rect(self.display_surface, (80, 80, 100), bg_rect, 2, border_radius=6)
        
        # Barre de progression avec gradient
        fill_height = int(bar_height * progress)
        if fill_height > 0:
            for i in range(fill_height):
                ratio = i / bar_height
                color = (
                    int(100 + 155 * ratio),  # Rouge -> Orange
                    int(200 - 100 * ratio),  # Vert -> Jaune
                    int(100 - 50 * ratio)    # Bleu -> Orange
                )
                y_pos = bar_y + bar_height - i
                pygame.draw.line(self.display_surface, color, 
                               (bar_x, y_pos), (bar_x + bar_width, y_pos))
        
        # Icône de fusée sur l'indicateur
        rocket_y = bar_y + bar_height - int(bar_height * progress)
        pygame.draw.polygon(self.display_surface, (255, 255, 255), [
            (bar_x + bar_width + 8, rocket_y),
            (bar_x + bar_width + 18, rocket_y + 6),
            (bar_x + bar_width + 18, rocket_y - 6)
        ])
        
        # Label
        small_font = pygame.font.Font(None, 22)
        pct_text = small_font.render(f"{int(progress * 100)}%", True, (200, 200, 200))
        self.display_surface.blit(pct_text, (bar_x - 5, bar_y + bar_height + 8))
    
    def _draw_level_title(self):
        """Dessine le titre du niveau avec animation et effets"""
        if self.level_time < 0.8:
            # Arrive du haut (0 à 0.8s)
            y_pos = -100 + (self.level_time / 0.8) * 200
            alpha = int(255 * (self.level_time / 0.8))
        elif self.level_time < 3.2:
            # Reste au centre (0.8s à 3.2s)
            y_pos = 100
            alpha = 255
        else:
            # Repart vers le haut (3.2s à 4.0s)
            y_pos = 100 - ((self.level_time - 3.2) / 0.8) * 200
            alpha = int(255 * (1 - (self.level_time - 3.2) / 0.8))
        
        # Créer les surfaces avec alpha
        title_surf = self.title_font.render(self.title_text, True, (255, 255, 255))
        shadow_surf = self.title_font.render(self.title_text, True, (0, 0, 0))
        
        # Glow derrière le titre
        glow_width = title_surf.get_width() + 60
        glow_height = title_surf.get_height() + 40
        glow_surf = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
        
        for i in range(3):
            glow_alpha = max(0, (alpha // 4) - i * 15)
            pygame.draw.rect(glow_surf, (100, 150, 255, glow_alpha),
                           (i * 10, i * 8, glow_width - i * 20, glow_height - i * 16),
                           border_radius=15)
        
        glow_x = SCREEN_WIDTH // 2 - glow_width // 2
        glow_y = y_pos - 20
        self.display_surface.blit(glow_surf, (glow_x, glow_y), special_flags=pygame.BLEND_ADD)
        
        # Ombre et titre
        title_x = SCREEN_WIDTH // 2 - title_surf.get_width() // 2
        
        if alpha < 255:
            # Appliquer l'alpha si nécessaire
            shadow_surf.set_alpha(alpha)
            title_surf.set_alpha(alpha)
        
        self.display_surface.blit(shadow_surf, (title_x + 3, y_pos + 3))
        self.display_surface.blit(title_surf, (title_x, y_pos))

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
        """Crée un nouvel obstacle de manière aléatoire.
        
        STRATÉGIE DE SPAWN:
        - Les obstacles apparaissent MAJORITÉ par le haut (65%) car la fusée monte
        - Minorité sur les côtés (20%) pour varier la direction
        - Petit peu par le bas (15%)
        
        Deux types d'obstacles:
        - Débris (40% en mode mixed, 100% en mode debris)
        - Déchets (60% à collecter pour points)
        
        Pas de spawn en atmosphère (Y > atmosphere_altitude) pour économiser ressources.
        """
        all_imgs = self.obstacle_images.get("debris", []) + self.obstacle_images.get("dechet", [])
        if not all_imgs: 
            return  # Pas d'images chargées
        
        # Pas de débris tant qu'on est dans l'atmosphère
        if self.player.position.y > self.atmosphere_altitude:
            return
        
        # Choix du type d'obstacle selon le niveau
        if self.level_type == 'debris':
            is_debris = True  # Niveau 1: tous des débris
        else:
            is_debris = random.random() < 0.4  # Niveau 2: 40% débris, 60% déchets
            
        # Récupérer les images du bon type
        choices = self.obstacle_images.get("debris", []) if is_debris else self.obstacle_images.get("dechet", [])
        if not choices: 
            choices = all_imgs  # Fallback si type vide
        
        item_name, image = random.choice(choices)
        
        # Données de spawn (centré sur la caméra)
        cam_center_x = self.camera_x + SCREEN_WIDTH * 0.5
        cam_center_y = self.camera_y + SCREEN_HEIGHT * 0.5
        spawn_radius_x = SCREEN_WIDTH * 1.2
        spawn_radius_y = SCREEN_HEIGHT * 1.2
        
        # STRATÉGIE: apparition majoritairement au-dessus car la fusée monte
        rand_val = random.random()
        if rand_val < 0.65:
            # HAUT (65%): où la fusée va aller
            x = self.camera_x + random.uniform(-200, SCREEN_WIDTH + 200)
            y = self.camera_y - random.uniform(100, 1000)
        elif rand_val < 0.85:
            # CÔTÉS (20% de 85-65): pour varier la direction
            base_x = self.camera_x - random.uniform(100, 400) if random.random() < 0.5 else self.camera_x + SCREEN_WIDTH + random.uniform(100, 400)
            x = base_x
            y = self.camera_y + random.uniform(-500, SCREEN_HEIGHT + 200)
        else:
            # BAS (15% de 100-85): derrière la fusée
            x = self.camera_x + random.uniform(-200, SCREEN_WIDTH + 200)
            y = self.camera_y + SCREEN_HEIGHT + random.uniform(100, 600)
            
        # Créer l'obstacle (DebrisItem ou DechetItem)
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
        """Détecte les collisions joueur-obstacles et gère les effets.
        
        DEUX CAS:
        1. Débris: Explosion Game Over totale
        2. Déchet: Collecte et score +10
        
        Utilise la distance circulaire pour détection (cercle vs cercle).
        
        Args:
            dt: Delta time
            game_instance: Référence au game pour changer d'état
        """
        if not self.obstacles:
            return

        if not self.is_player_in_flight():
            self.collision_cooldown = 0.0
            return

        # Cooldown pour éviter détections multiples trop rapides
        self.collision_cooldown = max(0.0, self.collision_cooldown - dt)
        player_radius = max(14, min(self.player.image.get_width(), self.player.image.get_height()) * 0.28)

        for obstacle in self.obstacles:
            # Vecteur distance entre joueur et obstacle
            delta = self.player.position - obstacle.position
            hit_dist = player_radius + obstacle.collision_radius

            # Détection collision (distance circulaire)
            if delta.length_squared() <= hit_dist * hit_dist:
                if obstacle.obstacle_type == "debris":
                    # ===== DÉBRIS: C'EST EXPLOSIF ======
                    # Explosion spectaculaire!
                    self.particle_emitter.emit_explosion(
                        self.player.position.x, 
                        self.player.position.y, 
                        count=60
                    )
                    self.screen_shake.trigger(intensity=25, duration=0.5)
                    
                    # Changer l'image de la fusée en explosion
                    import utils
                    img = utils.load_texture("explode.png")
                    w, h = self.player.image.get_size()
                    self.player.image = pygame.transform.smoothscale(img, (w, h))
                    
                    # Jouer le son de crash
                    if hasattr(self, 'crash_sound') and self.crash_sound:
                        self.crash_sound.play()
                        
                    # Transitionner vers le bon écran
                    if len(game_instance.collected_trash) > 0:
                        # Niveau 2: tri des déchets collectés
                        game_instance.change_state("sorting_level")
                    else:
                        # Pas de déchets: Game Over
                        game_instance.change_state("game_over")
                    break  # Stop tout, sortir de la boucle
                    
                elif obstacle.obstacle_type == "dechet":
                    # ===== DÉCHET: COLLECTE + SCORE ======
                    # Effet visuel d'étincelles jaunes
                    self.particle_emitter.emit_sparkle(
                        obstacle.position.x,
                        obstacle.position.y,
                        color=(255, 255, 100),
                        count=20
                    )
                    
                    # Ajouter le déchet collecté à la liste (pour niveau de tri)
                    game_instance.collected_trash.append((getattr(obstacle, "item_name", "Inconnu"), obstacle.image.copy()))
                    
                    # Ajouter les points
                    game_instance.score += 10
                    
                    # Supprimer l'obstacle
                    obstacle.kill()
                    # Ne pas break: continuer à checker les autres obstacles!

    # C'est la fonction qui met à jour le niveau, elle est appelée à chaque frame depuis run() dans game.py
    def run(self, dt, game_instance=None):
        """Fonction PRINCIPALE mise à jour du niveau - appelée CHAQUE FRAME.
        
        C'est le cœur du système. Elle gère:
        1. Mise à jour physique (sprites, obstacles, caméra)
        2. Systèmes de particules et effets
        3. Collisions joueur-obstacles
        4. Rendu complet de la scène
        
        Appel cascade:
        update() → update_camera() → update_obstacles() → draw_*()
        
        Args:
            dt: Delta time en secondes
            game_instance: Référence à l'instance du jeu principal
            
        Returns:
            "completed" si le joueur atteint l'altitude end_y
        """
        self.level_time += dt  # Compte le temps pour les animations
        
        # ===== MISE À JOUR PHYSIQUE =====
        self.visible_sprites.update(dt)  # Update tous les sprites (joueur + obstacles)
        self.update_camera()  # Suivre le joueur
        self.update_obstacles(dt)  # Spawn/supprimer les obstacles
        
        # ===== SYSTÈMES DE PARTICULES =====
        self.particle_emitter.update(dt)  # Met à jour les particules (flammes, étincelles, etc)
        self.screen_shake.update(dt)  # Mettre à jour le tremblement d'écran
        
        # Effets spatiaux (seulement en espace)
        in_space = getattr(self, 'space_transition', 0) > 0.5
        self.shooting_stars.update(dt, self.camera_x, self.camera_y, in_space)
        self.comet_manager.update(dt, self.camera_x, self.camera_y, in_space)
        
        # Lignes de vitesse (effet de mouvement fluide quand on va vite)
        self.speed_lines.update(
            dt, 
            self.player.velocity.x, 
            self.player.velocity.y,
            self.player.position.x,
            self.player.position.y
        )
        
        # ===== ÉMISSION DE PARTICULES DE PROPULSION =====
        if self.player.launched:
            keys = pygame.key.get_pressed()
            boost = keys[pygame.K_z]  # Le joueur appuie-t-il sur Boost?
            
            # Calculer la position d'émission (arrière de la fusée)
            rad = math.radians(self.player.angle)
            emit_x = self.player.position.x + math.sin(rad) * 50
            emit_y = self.player.position.y + math.cos(rad) * 50
            
            # Émettre les flammes de propulsion
            self.particle_emitter.emit_thrust(
                emit_x, emit_y,
                self.player.angle,
                intensity=1.2 if boost else 0.8,  # Plus intense en boost
                boost=boost  # Changer la couleur des flammes
            )
        
        # ===== COLLISIONS =====
        if game_instance:
            self.handle_obstacle_collisions(dt, game_instance)
            
        # ===== SYNCHRONISATION SCORE =====
        if game_instance:
            self.score = game_instance.score
            self.high_score = game_instance.high_score
            
            # Quand on quitte l'atmosphère, diminuer le son de décollage progressivement
            if self.player.position.y <= self.atmosphere_altitude:
                if hasattr(game_instance, 'takeoff_sound') and game_instance.takeoff_sound:
                    if not getattr(self, 'takeoff_faded', False):
                        game_instance.takeoff_sound.fadeout(2000)  # 2-sec fade
                        self.takeoff_faded = True

        # ===== RENDU COMPLET =====
        self.draw_background()      # Ciel, sol, étoiles, pad
        self.draw_sprites()         # Joueur, obstacles, glow
        
        # Lignes de vitesse au premier plan
        shake_cam_x, shake_cam_y = self.screen_shake.apply(self.camera_x, self.camera_y)
        self.speed_lines.draw(self.display_surface, shake_cam_x, shake_cam_y)
        
        self.draw_hud(dt)           # Score, vitesse, contrôles
        
        # ===== CONDITION DE FIN =====
        if self.end_y is not None and self.player.position.y < self.end_y:
            return "completed"  # Niveau fini!