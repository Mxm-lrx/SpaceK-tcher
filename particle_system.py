"""
Système de particules avancé pour SpaceK'tcher
Gère les trainées de propulsion, étoiles filantes, effets de collecte et explosions
"""
import pygame
import math
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Particle:
    """Particule individuelle avec physique et rendu"""
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'size', 'color', 
                 'alpha', 'gravity', 'shrink', 'fade')
    
    def __init__(self, x, y, vx, vy, life, size, color, gravity=0, shrink=True, fade=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.alpha = 255
        self.gravity = gravity
        self.shrink = shrink
        self.fade = fade
    
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        
        # Calcul du ratio de vie restante
        life_ratio = max(0, self.life / self.max_life)
        
        if self.fade:
            self.alpha = int(255 * life_ratio)
        if self.shrink:
            self.size = max(1, self.size * (0.5 + 0.5 * life_ratio))
        
        return self.life > 0
    
    def draw(self, surface, camera_x=0, camera_y=0):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Vérifier si visible
        if not (-self.size < screen_x < SCREEN_WIDTH + self.size and 
                -self.size < screen_y < SCREEN_HEIGHT + self.size):
            return
        
        if self.alpha < 255:
            # Surface avec transparence pour l'effet de fade
            size_int = max(1, int(self.size * 2))
            particle_surf = pygame.Surface((size_int, size_int), pygame.SRCALPHA)
            color_with_alpha = (*self.color[:3], self.alpha)
            pygame.draw.circle(particle_surf, color_with_alpha, 
                             (size_int // 2, size_int // 2), max(1, int(self.size)))
            surface.blit(particle_surf, (screen_x - size_int // 2, screen_y - size_int // 2))
        else:
            pygame.draw.circle(surface, self.color, (screen_x, screen_y), max(1, int(self.size)))


class GlowParticle(Particle):
    """Particule avec effet de lueur (glow)"""
    __slots__ = ('glow_size', 'glow_color')
    
    def __init__(self, x, y, vx, vy, life, size, color, glow_color=None, gravity=0):
        super().__init__(x, y, vx, vy, life, size, color, gravity, shrink=True, fade=True)
        self.glow_size = size * 3
        self.glow_color = glow_color or tuple(min(255, c + 50) for c in color[:3])
    
    def draw(self, surface, camera_x=0, camera_y=0):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        if not (-self.glow_size < screen_x < SCREEN_WIDTH + self.glow_size and 
                -self.glow_size < screen_y < SCREEN_HEIGHT + self.glow_size):
            return
        
        # Dessiner le glow (plus grand, plus transparent)
        glow_alpha = max(0, self.alpha // 3)
        glow_int = max(2, int(self.glow_size * 2))
        glow_surf = pygame.Surface((glow_int, glow_int), pygame.SRCALPHA)
        
        # Dessiner plusieurs cercles concentriques pour l'effet de glow
        for i in range(3, 0, -1):
            radius = int(self.glow_size * i / 3)
            alpha = glow_alpha // i
            color_with_alpha = (*self.glow_color[:3], alpha)
            pygame.draw.circle(glow_surf, color_with_alpha, 
                             (glow_int // 2, glow_int // 2), radius)
        
        surface.blit(glow_surf, (screen_x - glow_int // 2, screen_y - glow_int // 2), 
                    special_flags=pygame.BLEND_ADD)
        
        # Dessiner le cœur de la particule
        super().draw(surface, camera_x, camera_y)


class ParticleEmitter:
    """Émetteur de particules avec différents patterns"""
    
    def __init__(self, max_particles=500):
        self.particles = []
        self.max_particles = max_particles
    
    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self, surface, camera_x=0, camera_y=0):
        for particle in self.particles:
            particle.draw(surface, camera_x, camera_y)
    
    def emit_thrust(self, x, y, angle, intensity=1.0, boost=False):
        """Émet des particules de propulsion de fusée"""
        if len(self.particles) >= self.max_particles:
            return
        
        # Convertir l'angle en radians et calculer la direction opposée
        rad = math.radians(angle)
        base_vx = math.sin(rad) * 150
        base_vy = math.cos(rad) * 150
        
        num_particles = 3 if not boost else 6
        
        for _ in range(num_particles):
            # Variation aléatoire
            spread = 25 if not boost else 35
            vx = base_vx + random.uniform(-spread, spread)
            vy = base_vy + random.uniform(-spread, spread)
            
            # Couleurs de feu : orange → jaune → blanc selon l'intensité
            if boost:
                colors = [(100, 180, 255), (150, 200, 255), (200, 220, 255)]  # Bleu pour boost
            else:
                colors = [(255, 100, 50), (255, 150, 50), (255, 200, 100)]  # Orange/jaune
            
            color = random.choice(colors)
            size = random.uniform(3, 6) * intensity
            life = random.uniform(0.15, 0.35)
            
            offset_x = random.uniform(-8, 8)
            offset_y = random.uniform(0, 15)  # Légèrement derrière la fusée
            
            particle = GlowParticle(
                x + offset_x, y + offset_y,
                vx, vy, life, size, color,
                gravity=50
            )
            self.particles.append(particle)
    
    def emit_sparkle(self, x, y, color=(255, 255, 100), count=15):
        """Émet des étincelles lors de la collecte d'objets"""
        if len(self.particles) + count > self.max_particles:
            count = self.max_particles - len(self.particles)
        
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            # Variation de couleur
            r = max(0, min(255, color[0] + random.randint(-30, 30)))
            g = max(0, min(255, color[1] + random.randint(-30, 30)))
            b = max(0, min(255, color[2] + random.randint(-30, 30)))
            
            size = random.uniform(2, 5)
            life = random.uniform(0.3, 0.7)
            
            particle = GlowParticle(
                x + random.uniform(-10, 10),
                y + random.uniform(-10, 10),
                vx, vy, life, size, (r, g, b),
                gravity=100
            )
            self.particles.append(particle)
    
    def emit_explosion(self, x, y, count=40):
        """Émet une explosion spectaculaire"""
        if len(self.particles) + count > self.max_particles:
            count = max(10, self.max_particles - len(self.particles))
        
        colors = [
            (255, 100, 50),   # Orange
            (255, 200, 50),   # Jaune
            (255, 50, 50),    # Rouge
            (255, 150, 100),  # Orange clair
            (200, 200, 200),  # Gris (fumée)
        ]
        
        for i in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(100, 350)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            color = random.choice(colors)
            size = random.uniform(4, 12)
            life = random.uniform(0.4, 1.2)
            
            particle = GlowParticle(
                x + random.uniform(-20, 20),
                y + random.uniform(-20, 20),
                vx, vy, life, size, color,
                gravity=80
            )
            self.particles.append(particle)
        
        # Ajouter des débris plus gros
        for _ in range(count // 4):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            particle = Particle(
                x, y, vx, vy,
                life=random.uniform(0.8, 1.5),
                size=random.uniform(6, 15),
                color=(100, 100, 100),
                gravity=200,
                shrink=False,
                fade=True
            )
            self.particles.append(particle)
    
    def emit_trail(self, x, y, vx, vy, color=(200, 200, 255)):
        """Émet une trainée légère (pour les étoiles filantes ou objets rapides)"""
        if len(self.particles) >= self.max_particles:
            return
        
        particle = Particle(
            x + random.uniform(-3, 3),
            y + random.uniform(-3, 3),
            vx * 0.3 + random.uniform(-10, 10),
            vy * 0.3 + random.uniform(-10, 10),
            life=random.uniform(0.2, 0.5),
            size=random.uniform(2, 4),
            color=color,
            gravity=0
        )
        self.particles.append(particle)
    
    def clear(self):
        """Supprime toutes les particules"""
        self.particles.clear()


class ShootingStar:
    """Étoile filante avec trainée lumineuse"""
    
    def __init__(self, camera_x, camera_y):
        # Spawn à l'extérieur de l'écran
        side = random.choice(['top', 'left', 'right'])
        if side == 'top':
            self.x = camera_x + random.uniform(-200, SCREEN_WIDTH + 200)
            self.y = camera_y - 100
        elif side == 'left':
            self.x = camera_x - 100
            self.y = camera_y + random.uniform(-200, SCREEN_HEIGHT + 200)
        else:
            self.x = camera_x + SCREEN_WIDTH + 100
            self.y = camera_y + random.uniform(-200, SCREEN_HEIGHT + 200)
        
        # Direction vers le bas-opposé
        angle = random.uniform(math.pi * 0.2, math.pi * 0.4)
        if side == 'right':
            angle = math.pi - angle
        
        speed = random.uniform(400, 800)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.life = random.uniform(1.0, 2.5)
        self.max_life = self.life
        self.size = random.uniform(2, 4)
        self.trail = []
        self.max_trail = 15
        self.color = random.choice([
            (255, 255, 255),
            (200, 220, 255),
            (255, 240, 200),
        ])
    
    def update(self, dt):
        # Sauvegarder la position pour la trainée
        self.trail.append((self.x, self.y, self.size))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
        
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        
        return self.life > 0
    
    def draw(self, surface, camera_x, camera_y):
        # Dessiner la trainée
        for i, (tx, ty, ts) in enumerate(self.trail):
            screen_x = int(tx - camera_x)
            screen_y = int(ty - camera_y)
            
            if 0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT:
                alpha = int(255 * (i / self.max_trail) * (self.life / self.max_life))
                size = max(1, int(ts * (i / self.max_trail)))
                
                if alpha > 10:
                    trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    color_with_alpha = (*self.color, alpha)
                    pygame.draw.circle(trail_surf, color_with_alpha, (size, size), size)
                    surface.blit(trail_surf, (screen_x - size, screen_y - size), 
                               special_flags=pygame.BLEND_ADD)
        
        # Dessiner l'étoile principale
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        if 0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT:
            # Glow
            glow_size = int(self.size * 4)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            for r in range(glow_size, 0, -2):
                alpha = int(150 * (r / glow_size))
                pygame.draw.circle(glow_surf, (*self.color, alpha), 
                                 (glow_size, glow_size), r)
            surface.blit(glow_surf, (screen_x - glow_size, screen_y - glow_size), 
                        special_flags=pygame.BLEND_ADD)


class ShootingStarManager:
    """Gestionnaire d'étoiles filantes"""
    
    def __init__(self, spawn_rate=0.3):
        self.stars = []
        self.spawn_rate = spawn_rate  # étoiles par seconde en moyenne
        self.spawn_timer = 0
        self.max_stars = 5
    
    def update(self, dt, camera_x, camera_y, in_space=True):
        if not in_space:
            self.stars.clear()
            return
        
        # Spawn de nouvelles étoiles
        self.spawn_timer += dt
        spawn_interval = 1.0 / self.spawn_rate
        
        while self.spawn_timer >= spawn_interval and len(self.stars) < self.max_stars:
            self.spawn_timer -= spawn_interval
            if random.random() < 0.6:  # 60% de chance de spawn
                self.stars.append(ShootingStar(camera_x, camera_y))
        
        # Update des étoiles
        self.stars = [star for star in self.stars if star.update(dt)]
    
    def draw(self, surface, camera_x, camera_y):
        for star in self.stars:
            star.draw(surface, camera_x, camera_y)


class ScreenShake:
    """Gestionnaire de tremblement d'écran"""
    
    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.offset_x = 0
        self.offset_y = 0
    
    def trigger(self, intensity=15, duration=0.3):
        """Déclenche un tremblement"""
        self.intensity = intensity
        self.duration = duration
    
    def update(self, dt):
        if self.duration > 0:
            self.duration -= dt
            # Diminution progressive de l'intensité
            current_intensity = self.intensity * (self.duration / 0.3)
            self.offset_x = random.uniform(-current_intensity, current_intensity)
            self.offset_y = random.uniform(-current_intensity, current_intensity)
        else:
            self.offset_x = 0
            self.offset_y = 0
    
    def apply(self, camera_x, camera_y):
        """Retourne les coordonnées de caméra modifiées"""
        return camera_x + self.offset_x, camera_y + self.offset_y


class Nebula:
    """Nébuleuse décorative en arrière-plan"""
    
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.surface = self._generate_surface()
    
    def _generate_surface(self):
        """Génère une surface de nébuleuse avec effet de gradient circulaire"""
        surf_size = int(self.size * 2)
        surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        
        center = surf_size // 2
        
        # Dessiner plusieurs cercles concentriques pour l'effet de gradient
        for r in range(int(self.size), 0, -max(1, int(self.size // 20))):
            alpha = int(40 * (1 - (r / self.size)))
            color_with_alpha = (*self.color[:3], alpha)
            pygame.draw.circle(surface, color_with_alpha, (center, center), r)
        
        return surface
    
    def draw(self, surface, camera_x, camera_y, parallax_factor=0.1):
        """Dessine la nébuleuse avec un effet de parallaxe"""
        screen_x = int(self.x - camera_x * parallax_factor)
        screen_y = int(self.y - camera_y * parallax_factor)
        
        # Wrap around pour que les nébuleuses restent visibles
        screen_x = screen_x % (SCREEN_WIDTH + self.size * 2) - self.size
        screen_y = screen_y % (SCREEN_HEIGHT + self.size * 2) - self.size
        
        surface.blit(self.surface, (screen_x, screen_y), special_flags=pygame.BLEND_ADD)


class NebulaManager:
    """Gestionnaire de nébuleuses - Version simplifiée, les planètes sont gérées séparément"""
    
    def __init__(self):
        self.nebulae = []
        self._generate_nebulae()
    
    def _generate_nebulae(self):
        """Génère des nébuleuses procédurales subtiles"""
        colors = [
            (60, 30, 100),   # Violet sombre
            (30, 60, 100),   # Bleu sombre
            (100, 30, 60),   # Rose sombre
            (30, 80, 80),    # Cyan sombre
        ]
        
        for _ in range(5):
            x = random.uniform(-500, SCREEN_WIDTH + 500)
            y = random.uniform(-500, SCREEN_HEIGHT + 500)
            size = random.uniform(200, 500)
            color = random.choice(colors)
            self.nebulae.append(Nebula(x, y, size, color))
    
    def draw(self, surface, camera_x, camera_y, space_transition=1.0):
        """Dessine les nébuleuses avec intensité basée sur la transition vers l'espace"""
        if space_transition < 0.3:
            return
        
        for nebula in self.nebulae:
            nebula.draw(surface, camera_x, camera_y)


class Planet:
    """Planète réaliste avec ombrage, atmosphère et détails"""
    
    def __init__(self, base_x, base_y, radius, planet_type="rocky"):
        self.base_x = base_x
        self.base_y = base_y
        self.radius = radius
        self.planet_type = planet_type
        self.rotation = random.uniform(0, math.tau)
        self.rotation_speed = random.uniform(0.01, 0.05)
        self.parallax_factor = 0.05 + (radius / 500) * 0.15  # Plus grandes = plus loin = moins de parallaxe
        
        # Couleurs selon le type
        self.colors = self._get_planet_colors()
        
        # Générer la texture de la planète
        self.surface = self._generate_planet_surface()
        
        # Lunes optionnelles
        self.moons = []
        if random.random() < 0.4 and radius > 60:
            num_moons = random.randint(1, 3)
            for i in range(num_moons):
                moon_dist = radius * random.uniform(1.5, 2.5)
                moon_size = random.randint(5, max(6, int(radius * 0.2)))
                moon_speed = random.uniform(0.2, 0.8)
                moon_phase = random.uniform(0, math.tau)
                self.moons.append({
                    'dist': moon_dist,
                    'size': moon_size,
                    'speed': moon_speed,
                    'phase': moon_phase,
                    'color': (180, 180, 190)
                })
        
        # Anneaux optionnels (pour les grandes planètes)
        self.has_rings = random.random() < 0.25 and radius > 80
        if self.has_rings:
            self.ring_color = random.choice([
                (200, 180, 150),  # Beige
                (180, 200, 220),  # Bleu clair
                (220, 200, 180),  # Sable
            ])
            self.ring_tilt = random.uniform(0.2, 0.5)
    
    def _get_planet_colors(self):
        """Retourne une palette de couleurs selon le type de planète"""
        palettes = {
            "rocky": [
                [(139, 90, 43), (160, 120, 80), (100, 70, 40)],     # Marron/rouille
                [(128, 128, 128), (169, 169, 169), (105, 105, 105)], # Gris lunaire
                [(205, 133, 63), (210, 150, 80), (180, 110, 50)],   # Orange/Mars
            ],
            "gas_giant": [
                [(255, 200, 150), (255, 180, 120), (200, 140, 100)], # Jupiter-like
                [(230, 220, 180), (200, 190, 150), (180, 170, 130)], # Saturne
                [(150, 200, 230), (130, 180, 210), (100, 150, 190)], # Neptune-like
            ],
            "ice": [
                [(200, 230, 255), (180, 210, 240), (150, 190, 220)], # Glace bleue
                [(240, 250, 255), (220, 235, 245), (200, 220, 235)], # Blanc glacé
            ],
            "earth_like": [
                [(100, 150, 200), (80, 130, 100), (150, 140, 100)],  # Terre
            ],
            "lava": [
                [(200, 80, 50), (255, 120, 50), (150, 50, 30)],      # Lave
            ]
        }
        
        palette_list = palettes.get(self.planet_type, palettes["rocky"])
        return random.choice(palette_list)
    
    def _generate_planet_surface(self):
        """Génère la surface de la planète avec ombrage réaliste"""
        size = int(self.radius * 2.5)  # Marge pour l'atmosphère
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Dessiner l'atmosphère glow
        if self.planet_type in ["gas_giant", "earth_like"]:
            for r in range(int(self.radius * 1.2), int(self.radius), -2):
                alpha = int(30 * (r - self.radius) / (self.radius * 0.2))
                atmo_color = tuple(min(255, c + 50) for c in self.colors[0])
                pygame.draw.circle(surface, (*atmo_color, max(0, alpha)), (center, center), r)
        
        # Corps principal de la planète
        base_color = self.colors[0]
        pygame.draw.circle(surface, base_color, (center, center), int(self.radius))
        
        # Détails de surface (cratères, bandes, etc.)
        self._add_surface_details(surface, center)
        
        # Ombrage réaliste (lumière venant du coin supérieur gauche)
        self._add_shading(surface, center)
        
        # Highlight (reflet)
        self._add_highlight(surface, center)
        
        return surface
    
    def _add_surface_details(self, surface, center):
        """Ajoute des détails selon le type de planète"""
        if self.planet_type == "rocky":
            # Cratères
            num_craters = random.randint(3, 8)
            for _ in range(num_craters):
                angle = random.uniform(0, math.tau)
                dist = random.uniform(0, self.radius * 0.7)
                cx = center + int(math.cos(angle) * dist)
                cy = center + int(math.sin(angle) * dist)
                crater_r = random.randint(3, max(4, int(self.radius * 0.15)))
                
                # Ombre du cratère
                pygame.draw.circle(surface, self.colors[2], (cx + 1, cy + 1), crater_r)
                pygame.draw.circle(surface, self.colors[1], (cx, cy), crater_r - 1)
        
        elif self.planet_type == "gas_giant":
            # Bandes horizontales
            num_bands = random.randint(4, 8)
            for i in range(num_bands):
                y_offset = int((i / num_bands - 0.5) * self.radius * 1.6)
                band_color = self.colors[i % len(self.colors)]
                band_height = int(self.radius * 0.15)
                
                # Créer un rectangle arrondi pour la bande
                for dy in range(-band_height // 2, band_height // 2):
                    y = center + y_offset + dy
                    # Calculer la largeur à cette hauteur (cercle)
                    if abs(y - center) < self.radius:
                        width = int(math.sqrt(self.radius**2 - (y - center)**2))
                        alpha = 100 - abs(dy) * 10
                        if alpha > 0:
                            pygame.draw.line(surface, (*band_color, alpha),
                                           (center - width, y), (center + width, y))
            
            # Grande tache (style Jupiter)
            if random.random() < 0.5:
                spot_x = center + int(self.radius * random.uniform(-0.3, 0.3))
                spot_y = center + int(self.radius * random.uniform(-0.2, 0.2))
                spot_rx = int(self.radius * random.uniform(0.15, 0.25))
                spot_ry = int(spot_rx * 0.6)
                spot_color = random.choice([(200, 100, 80), (180, 150, 120), (255, 200, 150)])
                pygame.draw.ellipse(surface, spot_color,
                                  (spot_x - spot_rx, spot_y - spot_ry, spot_rx * 2, spot_ry * 2))
        
        elif self.planet_type == "earth_like":
            # Continents simplifiés
            num_continents = random.randint(2, 4)
            for _ in range(num_continents):
                angle = random.uniform(0, math.tau)
                dist = random.uniform(0, self.radius * 0.6)
                cx = center + int(math.cos(angle) * dist)
                cy = center + int(math.sin(angle) * dist)
                
                # Forme irrégulière pour le continent
                points = []
                num_points = random.randint(5, 8)
                base_size = random.randint(int(self.radius * 0.2), int(self.radius * 0.4))
                for i in range(num_points):
                    a = (i / num_points) * math.tau
                    r = base_size * random.uniform(0.6, 1.0)
                    points.append((cx + int(math.cos(a) * r), cy + int(math.sin(a) * r)))
                
                if len(points) >= 3:
                    pygame.draw.polygon(surface, self.colors[1], points)
    
    def _add_shading(self, surface, center):
        """Ajoute un ombrage réaliste"""
        # Créer un gradient d'ombre
        for r in range(int(self.radius), 0, -1):
            # Position relative au centre
            shade_offset = int(self.radius * 0.3)
            
            # Calculer l'intensité de l'ombre
            # Plus sombre vers le bas-droite
            progress = r / self.radius
            alpha = int(80 * (1 - progress))
            
            pygame.draw.circle(surface, (0, 0, 0, alpha),
                             (center + shade_offset, center + shade_offset), r)
    
    def _add_highlight(self, surface, center):
        """Ajoute un reflet lumineux"""
        highlight_x = center - int(self.radius * 0.4)
        highlight_y = center - int(self.radius * 0.4)
        highlight_r = int(self.radius * 0.25)
        
        for r in range(highlight_r, 0, -1):
            alpha = int(60 * (r / highlight_r))
            pygame.draw.circle(surface, (255, 255, 255, alpha),
                             (highlight_x, highlight_y), r)
    
    def update(self, dt):
        """Met à jour la rotation et les lunes"""
        self.rotation += self.rotation_speed * dt
        for moon in self.moons:
            moon['phase'] += moon['speed'] * dt
    
    def draw(self, surface, camera_x, camera_y, time):
        """Dessine la planète avec parallaxe"""
        # Position avec parallaxe (les planètes sont loin, bougent moins)
        screen_x = int(self.base_x - camera_x * self.parallax_factor)
        screen_y = int(self.base_y - camera_y * self.parallax_factor)
        
        # Wrap around pour que les planètes restent visibles
        wrap_margin = self.radius * 3
        screen_x = ((screen_x + wrap_margin) % (SCREEN_WIDTH + wrap_margin * 2)) - wrap_margin
        screen_y = ((screen_y + wrap_margin) % (SCREEN_HEIGHT + wrap_margin * 2)) - wrap_margin
        
        # Dessiner les anneaux (partie arrière)
        if self.has_rings:
            self._draw_rings(surface, screen_x, screen_y, behind=True)
        
        # Dessiner les lunes derrière
        for moon in self.moons:
            if math.sin(moon['phase']) < 0:
                self._draw_moon(surface, screen_x, screen_y, moon, time)
        
        # Dessiner la planète
        planet_rect = self.surface.get_rect(center=(screen_x, screen_y))
        surface.blit(self.surface, planet_rect)
        
        # Dessiner les anneaux (partie avant)
        if self.has_rings:
            self._draw_rings(surface, screen_x, screen_y, behind=False)
        
        # Dessiner les lunes devant
        for moon in self.moons:
            if math.sin(moon['phase']) >= 0:
                self._draw_moon(surface, screen_x, screen_y, moon, time)
    
    def _draw_rings(self, surface, x, y, behind=True):
        """Dessine les anneaux de la planète"""
        ring_inner = int(self.radius * 1.3)
        ring_outer = int(self.radius * 2.0)
        
        for r in range(ring_inner, ring_outer, 2):
            # Variation d'opacité pour l'effet de bandes
            alpha = 80 + int(40 * math.sin(r * 0.3))
            if behind:
                # Partie arrière (plus sombre)
                alpha = alpha // 2
            
            # Dessiner l'ellipse inclinée
            ring_width = r * 2
            ring_height = int(r * 2 * self.ring_tilt)
            
            ring_rect = pygame.Rect(x - r, y - ring_height // 2, ring_width, ring_height)
            
            ring_surf = pygame.Surface((ring_width, ring_height), pygame.SRCALPHA)
            pygame.draw.ellipse(ring_surf, (*self.ring_color, alpha), 
                              (0, 0, ring_width, ring_height), 1)
            
            if behind:
                # Ne dessiner que la moitié supérieure
                surface.blit(ring_surf, ring_rect.topleft, 
                           area=pygame.Rect(0, 0, ring_width, ring_height // 2))
            else:
                # Ne dessiner que la moitié inférieure
                surface.blit(ring_surf, (ring_rect.x, ring_rect.y + ring_height // 2),
                           area=pygame.Rect(0, ring_height // 2, ring_width, ring_height // 2))
    
    def _draw_moon(self, surface, planet_x, planet_y, moon, time):
        """Dessine une lune en orbite"""
        moon_x = planet_x + int(math.cos(moon['phase']) * moon['dist'])
        moon_y = planet_y + int(math.sin(moon['phase']) * moon['dist'] * 0.3)  # Orbite inclinée
        
        # Lune avec ombrage simple
        pygame.draw.circle(surface, moon['color'], (moon_x, moon_y), moon['size'])
        # Ombre
        pygame.draw.circle(surface, (50, 50, 60), 
                          (moon_x + moon['size'] // 3, moon_y + moon['size'] // 3), 
                          moon['size'] - 1)
        # Reflet
        pygame.draw.circle(surface, (220, 220, 230),
                          (moon_x - moon['size'] // 3, moon_y - moon['size'] // 3),
                          moon['size'] // 3)


class PlanetManager:
    """Gestionnaire de planètes"""
    
    def __init__(self):
        self.planets = []
        self._generate_planets()
    
    def _generate_planets(self):
        """Génère une collection de planètes variées"""
        planet_configs = [
            # (type, min_radius, max_radius, count)
            ("rocky", 30, 70, 4),
            ("gas_giant", 80, 150, 2),
            ("ice", 40, 80, 2),
            ("earth_like", 50, 90, 1),
            ("lava", 35, 60, 1),
        ]
        
        for planet_type, min_r, max_r, count in planet_configs:
            for _ in range(count):
                x = random.uniform(-1000, SCREEN_WIDTH + 1000)
                y = random.uniform(-2000, SCREEN_HEIGHT + 2000)
                radius = random.randint(min_r, max_r)
                self.planets.append(Planet(x, y, radius, planet_type))
        
        # Trier par taille (plus grandes en arrière)
        self.planets.sort(key=lambda p: p.radius, reverse=True)
    
    def update(self, dt):
        """Met à jour toutes les planètes"""
        for planet in self.planets:
            planet.update(dt)
    
    def draw(self, surface, camera_x, camera_y, space_transition=1.0):
        """Dessine toutes les planètes"""
        if space_transition < 0.4:
            return
        
        time = pygame.time.get_ticks() / 1000
        for planet in self.planets:
            planet.draw(surface, camera_x, camera_y, time)


class SpeedLines:
    """Lignes de vitesse pour l'effet de mouvement rapide"""
    
    def __init__(self):
        self.lines = []
        self.max_lines = 50
    
    def update(self, dt, velocity_x, velocity_y, player_x, player_y):
        """Met à jour les lignes de vitesse"""
        speed = math.sqrt(velocity_x**2 + velocity_y**2)
        
        # Seuil de vitesse pour afficher les lignes
        if speed < 200:
            self.lines.clear()
            return
        
        # Calculer la direction opposée au mouvement
        if speed > 0:
            dir_x = -velocity_x / speed
            dir_y = -velocity_y / speed
        else:
            return
        
        # Générer de nouvelles lignes
        spawn_rate = min(1.0, (speed - 200) / 300)
        if random.random() < spawn_rate:
            # Position autour du joueur
            angle = random.uniform(0, math.tau)
            dist = random.uniform(100, 300)
            x = player_x + math.cos(angle) * dist
            y = player_y + math.sin(angle) * dist
            
            length = random.uniform(20, 60) * (speed / 300)
            life = random.uniform(0.1, 0.3)
            
            self.lines.append({
                'x': x, 'y': y,
                'dx': dir_x, 'dy': dir_y,
                'length': length,
                'life': life,
                'max_life': life,
                'speed': speed * random.uniform(0.8, 1.2)
            })
        
        # Mettre à jour les lignes existantes
        for line in self.lines[:]:
            line['x'] += line['dx'] * line['speed'] * dt
            line['y'] += line['dy'] * line['speed'] * dt
            line['life'] -= dt
            
            if line['life'] <= 0:
                self.lines.remove(line)
    
    def draw(self, surface, camera_x, camera_y):
        """Dessine les lignes de vitesse"""
        for line in self.lines:
            alpha = int(255 * (line['life'] / line['max_life']))
            
            start_x = int(line['x'] - camera_x)
            start_y = int(line['y'] - camera_y)
            end_x = int(start_x + line['dx'] * line['length'])
            end_y = int(start_y + line['dy'] * line['length'])
            
            # Vérifier si visible
            if not (-50 < start_x < SCREEN_WIDTH + 50 and -50 < start_y < SCREEN_HEIGHT + 50):
                continue
            
            # Dessiner avec gradient
            line_surf = pygame.Surface((abs(end_x - start_x) + 10, abs(end_y - start_y) + 10), pygame.SRCALPHA)
            color = (255, 255, 255, alpha)
            
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), 2)


class Comet:
    """Comète avec queue lumineuse"""
    
    def __init__(self, camera_x, camera_y):
        # Spawn depuis le haut ou les côtés
        side = random.choice(['top', 'left', 'right'])
        if side == 'top':
            self.x = camera_x + random.uniform(-500, SCREEN_WIDTH + 500)
            self.y = camera_y - 500
        elif side == 'left':
            self.x = camera_x - 500
            self.y = camera_y + random.uniform(-500, SCREEN_HEIGHT + 500)
        else:
            self.x = camera_x + SCREEN_WIDTH + 500
            self.y = camera_y + random.uniform(-500, SCREEN_HEIGHT + 500)
        
        # Direction
        target_x = camera_x + SCREEN_WIDTH / 2 + random.uniform(-500, 500)
        target_y = camera_y + SCREEN_HEIGHT + 500
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        self.speed = random.uniform(300, 600)
        self.vx = (dx / dist) * self.speed
        self.vy = (dy / dist) * self.speed
        
        self.size = random.randint(8, 20)
        self.life = random.uniform(3, 6)
        self.trail = []
        self.max_trail = 40
        
        # Couleur (bleu-vert typique des comètes)
        self.color = random.choice([
            (150, 255, 200),  # Vert-cyan
            (200, 230, 255),  # Bleu clair
            (255, 240, 200),  # Jaune pâle
        ])
    
    def update(self, dt):
        # Sauvegarder position pour la queue
        self.trail.append((self.x, self.y, self.size))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
        
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        
        return self.life > 0
    
    def draw(self, surface, camera_x, camera_y):
        # Queue de la comète
        for i, (tx, ty, ts) in enumerate(self.trail):
            screen_x = int(tx - camera_x)
            screen_y = int(ty - camera_y)
            
            if 0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT:
                progress = i / self.max_trail
                alpha = int(150 * progress)
                size = max(1, int(ts * progress * 0.5))
                
                if alpha > 5:
                    glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                    for r in range(size * 2, 0, -2):
                        a = int(alpha * (r / (size * 2)))
                        pygame.draw.circle(glow_surf, (*self.color, a), 
                                         (size * 2, size * 2), r)
                    surface.blit(glow_surf, (screen_x - size * 2, screen_y - size * 2),
                               special_flags=pygame.BLEND_ADD)
        
        # Tête de la comète
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        if 0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT:
            # Glow
            glow_size = self.size * 4
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            for r in range(glow_size, 0, -3):
                alpha = int(200 * (r / glow_size))
                pygame.draw.circle(glow_surf, (*self.color, alpha),
                                 (glow_size, glow_size), r)
            surface.blit(glow_surf, (screen_x - glow_size, screen_y - glow_size),
                        special_flags=pygame.BLEND_ADD)
            
            # Cœur brillant
            pygame.draw.circle(surface, (255, 255, 255), (screen_x, screen_y), self.size // 2)


class CometManager:
    """Gestionnaire de comètes"""
    
    def __init__(self, spawn_rate=0.05):
        self.comets = []
        self.spawn_rate = spawn_rate
        self.spawn_timer = 0
        self.max_comets = 2
    
    def update(self, dt, camera_x, camera_y, in_space=True):
        if not in_space:
            self.comets.clear()
            return
        
        # Spawn
        self.spawn_timer += dt
        if self.spawn_timer >= 1.0 / self.spawn_rate and len(self.comets) < self.max_comets:
            self.spawn_timer = 0
            if random.random() < 0.15:  # 15% de chance
                self.comets.append(Comet(camera_x, camera_y))
        
        # Update
        self.comets = [c for c in self.comets if c.update(dt)]
    
    def draw(self, surface, camera_x, camera_y):
        for comet in self.comets:
            comet.draw(surface, camera_x, camera_y)


class CosmicDust:
    """Poussière cosmique ambiante"""
    
    def __init__(self):
        self.particles = []
        self.max_particles = 100
    
    def update(self, dt, camera_x, camera_y, in_space=True):
        if not in_space:
            self.particles.clear()
            return
        
        # Maintenir le nombre de particules
        while len(self.particles) < self.max_particles:
            self.particles.append({
                'x': camera_x + random.uniform(-100, SCREEN_WIDTH + 100),
                'y': camera_y + random.uniform(-100, SCREEN_HEIGHT + 100),
                'size': random.uniform(0.5, 2),
                'alpha': random.randint(30, 80),
                'drift_x': random.uniform(-10, 10),
                'drift_y': random.uniform(-10, 10),
                'twinkle_speed': random.uniform(1, 3),
                'twinkle_phase': random.uniform(0, math.tau)
            })
        
        # Mettre à jour
        for p in self.particles[:]:
            p['x'] += p['drift_x'] * dt
            p['y'] += p['drift_y'] * dt
            p['twinkle_phase'] += p['twinkle_speed'] * dt
            
            # Retirer si hors écran
            if (p['x'] < camera_x - 200 or p['x'] > camera_x + SCREEN_WIDTH + 200 or
                p['y'] < camera_y - 200 or p['y'] > camera_y + SCREEN_HEIGHT + 200):
                self.particles.remove(p)
    
    def draw(self, surface, camera_x, camera_y):
        for p in self.particles:
            screen_x = int(p['x'] - camera_x)
            screen_y = int(p['y'] - camera_y)
            
            if 0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT:
                twinkle = 0.5 + 0.5 * math.sin(p['twinkle_phase'])
                alpha = int(p['alpha'] * twinkle)
                
                dust_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                pygame.draw.circle(dust_surf, (200, 200, 220, alpha), (2, 2), int(p['size']))
                surface.blit(dust_surf, (screen_x - 2, screen_y - 2))


class SunFlare:
    """Soleil avec effet de lens flare"""
    
    def __init__(self):
        self.x = SCREEN_WIDTH * 0.85
        self.y = -200  # Au-dessus de l'écran initial
        self.radius = 80
        self.parallax = 0.02  # Très loin
        
        # Générer la surface du soleil
        self.surface = self._generate_sun()
        
        # Rayons de lens flare
        self.flare_colors = [
            (255, 200, 100, 100),
            (255, 150, 50, 80),
            (200, 100, 50, 60),
            (150, 200, 255, 40),
        ]
    
    def _generate_sun(self):
        """Génère la texture du soleil"""
        size = self.radius * 6
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Corona extérieure
        for r in range(int(self.radius * 2.5), int(self.radius), -5):
            alpha = int(60 * (1 - (r - self.radius) / (self.radius * 1.5)))
            pygame.draw.circle(surface, (255, 200, 100, max(0, alpha)), (center, center), r)
        
        # Corps du soleil
        for r in range(int(self.radius), 0, -2):
            progress = r / self.radius
            color = (
                255,
                int(200 + 55 * (1 - progress)),
                int(100 + 155 * (1 - progress)),
                255
            )
            pygame.draw.circle(surface, color, (center, center), r)
        
        return surface
    
    def draw(self, surface, camera_x, camera_y, space_transition):
        if space_transition < 0.5:
            return
        
        # Position avec parallaxe
        screen_x = int(self.x - camera_x * self.parallax)
        screen_y = int(self.y - camera_y * self.parallax)
        
        # Wrap pour rester visible
        screen_x = screen_x % (SCREEN_WIDTH + 200) - 100
        
        # Dessiner le soleil
        sun_rect = self.surface.get_rect(center=(screen_x, screen_y))
        surface.blit(self.surface, sun_rect, special_flags=pygame.BLEND_ADD)
        
        # Lens flare (cercles le long de la ligne vers le centre)
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        dx = center_x - screen_x
        dy = center_y - screen_y
        
        for i, color in enumerate(self.flare_colors):
            progress = (i + 1) * 0.25
            flare_x = int(screen_x + dx * progress)
            flare_y = int(screen_y + dy * progress)
            flare_r = int(20 + i * 15)
            
            flare_surf = pygame.Surface((flare_r * 2, flare_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(flare_surf, color, (flare_r, flare_r), flare_r)
            surface.blit(flare_surf, (flare_x - flare_r, flare_y - flare_r),
                        special_flags=pygame.BLEND_ADD)
