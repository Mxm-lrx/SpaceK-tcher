import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TRASH_CATEGORIES
from utils import load_texture

SUCCESS_MESSAGES = {
    "Verte": "Bravo ! Le verre se recycle à l'infini dans la poubelle verte.",
    "Jaune": "Super ! Les emballages (plastique, métal, carton) vont dans la poubelle jaune.",
    "Bleue": "Bien joué ! Les autres déchets vont dans la poubelle grise/bleue."
}

FAILURE_MESSAGES = {
    "bouteilleverre": "Erreur : le verre est recyclable à l'infini. Il doit aller dans la poubelle VERTE !",
    "canette": "Erreur : les canettes en métal se recyclent très bien, c'est poubelle JAUNE !",
    "yaourt": "Erreur : le pot de yaourt se recycle de mieux en mieux mais par défaut, ici c'est la poubelle BLEUE !",
    "banane": "Erreur : la peau de banane est organique. Sans compost, elle va dans la poubelle BLEUE !"
}


SUCCESS_MESSAGES = {
    "Verte": "Bravo ! Le verre se recycle à l'infini dans la poubelle verte.",
    "Jaune": "Super ! Les emballages (plastique, métal, carton) vont dans la poubelle jaune.",
    "Bleue": "Bien joué ! Les autres déchets vont dans la poubelle grise/bleue."
}

FAILURE_MESSAGES = {
    "bouteilleverre": "Erreur : le verre est recyclable à l'infini. Il doit aller dans la poubelle VERTE !",
    "canette": "Erreur : les canettes en métal se recyclent très bien, c'est poubelle JAUNE !",
    "yaourt": "Erreur : le pot de yaourt se recycle de mieux en mieux mais par défaut, ici c'est la poubelle BLEUE !",
    "banane": "Erreur : la peau de banane est organique. Sans compost, elle va dans la poubelle BLEUE !"
}


class Bin(pygame.sprite.Sprite):
    def __init__(self, color_name, rect_color, position, groups):
        super().__init__(groups)
        self.color_name = color_name
        self.base_color = rect_color
        
        # Créer une poubelle plus stylisée
        width, height = 120, 160
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Corps de la poubelle avec gradient
        for i in range(height - 20):
            ratio = i / (height - 20)
            color = tuple(max(0, int(c * (0.7 + 0.3 * ratio))) for c in rect_color[:3])
            pygame.draw.line(self.image, color, (10, 20 + i), (width - 10, 20 + i))
        
        # Couvercle
        pygame.draw.ellipse(self.image, tuple(min(255, c + 30) for c in rect_color[:3]), 
                          (5, 10, width - 10, 25))
        pygame.draw.ellipse(self.image, (50, 50, 50), (5, 10, width - 10, 25), 2)
        
        # Contour
        pygame.draw.rect(self.image, (50, 50, 50), (10, 20, width - 20, height - 25), 3, border_radius=5)
        
        # Symbole de recyclage stylisé
        symbol_colors = {
            "Verte": "♻",
            "Jaune": "📦",
            "Bleue": "🗑"
        }
        font = pygame.font.Font(None, 48)
        symbol = font.render(symbol_colors.get(color_name, "?"), True, (255, 255, 255))
        symbol_rect = symbol.get_rect(center=(width // 2, height // 2 + 10))
        self.image.blit(symbol, symbol_rect)
        
        # Label
        label_font = pygame.font.Font(None, 28)
        label = label_font.render(color_name, True, (255, 255, 255))
        label_rect = label.get_rect(center=(width // 2, height - 15))
        
        # Fond du label
        label_bg = pygame.Surface((label.get_width() + 10, label.get_height() + 4), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 150))
        self.image.blit(label_bg, (label_rect.x - 5, label_rect.y - 2))
        self.image.blit(label, label_rect)

        self.rect = self.image.get_rect(midbottom=position)
        self.hover = False
    
    def set_hover(self, is_hover):
        """Met en surbrillance si le déchet est au-dessus"""
        self.hover = is_hover

class TrashThrow(pygame.sprite.Sprite):
    def __init__(self, item_name, image, position, groups):
        super().__init__(groups)
        self.item_name = item_name
        
        # Redimensionner l'image pour qu'elle s'ajuste correctement
        w, h = image.get_size()
        scale = min(60.0 / max(1, w), 60.0 / max(1, h)) 
        self.image = pygame.transform.smoothscale(image, (int(w * scale), int(h * scale)))
        
        # Nous avons besoin d'une petite étiquette ou juste d'une image, utilisons simplement l'image
        self.rect = self.image.get_rect(center=position)

        self.velocity = pygame.Vector2(0, 0)
        self.gravity = 700
        self.is_thrown = False

    def update(self, dt):
        if self.is_thrown:
            self.velocity.y += self.gravity * dt
            self.rect.x += self.velocity.x * dt
            self.rect.y += self.velocity.y * dt

class SortingLevel:
    def __init__(self, surface, trash_list):
        self.display_surface = surface
        self.trash_list = trash_list  # Liste de tuples : (nom_objet, image_surface)
        self.font = pygame.font.Font(None, 48)

        self.level_time = 0.0
        self.title_text = "Niveau 3 : Le Grand Centre de Tri"
        self.title_font = pygame.font.Font(None, 64)

        self.visible_sprites = pygame.sprite.Group()
        self.bins = pygame.sprite.Group()

        Bin("Verte", (100, 255, 100), (SCREEN_WIDTH * 0.25, SCREEN_HEIGHT - 30), [self.visible_sprites, self.bins])
        Bin("Jaune", (255, 255, 100), (SCREEN_WIDTH * 0.50, SCREEN_HEIGHT - 30), [self.visible_sprites, self.bins])
        Bin("Bleue", (100, 100, 255), (SCREEN_WIDTH * 0.75, SCREEN_HEIGHT - 30), [self.visible_sprites, self.bins])

        self.current_trash = None
        self.aiming = False
        self.start_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
        
        self.feedback_timer = 0
        self.feedback_msg = ""
        self.feedback_color = (255, 255, 255)
        
        # Particules pour les effets
        from particle_system import ParticleEmitter
        self.particles = ParticleEmitter(max_particles=300)
        
        # Étoiles de fond
        self.bg_stars = []
        import random
        for _ in range(80):
            self.bg_stars.append({
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(1, 2),
                'twinkle': random.uniform(0, math.tau)
            })
        
        self.spawn_next_trash()

    def spawn_next_trash(self):
        if self.trash_list:
            item_data = self.trash_list.pop(0)
            if isinstance(item_data, tuple) and len(item_data) == 2:
                item_name, item_img = item_data
            else:
                item_name = str(item_data)
                item_img = pygame.Surface((40,40))
                item_img.fill((200,200,200))
            self.current_trash = TrashThrow(item_name, item_img, self.start_pos, [self.visible_sprites])
        else:
            self.current_trash = None

    def get_expected_bin(self, item_name):
        for bin_color, items in TRASH_CATEGORIES.items():
            for item in items:
                if item.lower() in item_name.lower():
                    return bin_color
        return "Bleue" 

    def get_failure_message(self, item_name):
        return FAILURE_MESSAGES.get(item_name.lower(), "Erreur : ce déchet ne va pas dans cette poubelle !")

    def run(self, dt, game_instance):
        self.level_time += dt
        self.particles.update(dt)
        
        # Fond avec gradient spatial
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            color = (int(30 + 20 * ratio), int(30 + 15 * ratio), int(50 + 20 * ratio))
            pygame.draw.line(self.display_surface, color, (0, y), (SCREEN_WIDTH, y))
        
        # Étoiles de fond
        for star in self.bg_stars:
            twinkle = 0.5 + 0.5 * math.sin(self.level_time * 2 + star['twinkle'])
            brightness = int(100 + 100 * twinkle)
            pygame.draw.circle(self.display_surface, (brightness, brightness, brightness + 20),
                             (int(star['x']), int(star['y'])), int(star['size']))

        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            
            # Message de feedback stylisé
            feedback_font = pygame.font.Font(None, 42)
            msg_surf = feedback_font.render(self.feedback_msg, True, self.feedback_color)
            
            # Fond du message
            msg_bg = pygame.Surface((msg_surf.get_width() + 40, msg_surf.get_height() + 20), pygame.SRCALPHA)
            bg_color = (0, 100, 0, 180) if self.feedback_color[1] > 200 else (100, 0, 0, 180)
            msg_bg.fill(bg_color)
            pygame.draw.rect(msg_bg, self.feedback_color, msg_bg.get_rect(), 3, border_radius=10)
            
            msg_x = SCREEN_WIDTH // 2 - msg_bg.get_width() // 2
            msg_y = SCREEN_HEIGHT // 2 - 120
            self.display_surface.blit(msg_bg, (msg_x, msg_y))
            self.display_surface.blit(msg_surf, (msg_x + 20, msg_y + 10))
            
            if self.feedback_timer <= 0:
                self.current_trash.kill()
                self.spawn_next_trash()
            
            self.visible_sprites.draw(self.display_surface)
            self.particles.draw(self.display_surface)
            self._draw_title()
            return

        if self.current_trash is None:
            if not getattr(self, 'win_played', False):
                self.win_played = True
                win_sounds = [ws for ws in getattr(game_instance, 'victory_sounds', []) if ws]
                if win_sounds:
                    import random
                    random.choice(win_sounds).play()
                
                # Effet de victoire
                for _ in range(5):
                    import random
                    self.particles.emit_sparkle(
                        random.uniform(100, SCREEN_WIDTH - 100),
                        random.uniform(100, SCREEN_HEIGHT - 200),
                        color=(255, 215, 0),
                        count=30
                    )

            # Écran de fin stylisé
            victory_font = pygame.font.Font(None, 72)
            txt = victory_font.render("Tri terminé !", True, (100, 255, 100))
            txt_shadow = victory_font.render("Tri terminé !", True, (0, 50, 0))
            
            self.display_surface.blit(txt_shadow, (SCREEN_WIDTH//2 - txt.get_width()//2 + 3, SCREEN_HEIGHT//2 - 50 + 3))
            self.display_surface.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//2 - 50))
            
            score_txt = self.font.render(f"Score final : {game_instance.score}", True, (255, 255, 255))
            self.display_surface.blit(score_txt, (SCREEN_WIDTH//2 - score_txt.get_width()//2, SCREEN_HEIGHT//2 + 20))
            
            # Instruction pulsante
            pulse = 0.5 + 0.5 * math.sin(self.level_time * 3)
            inst_color = (int(150 + 100 * pulse), int(150 + 100 * pulse), int(150 + 100 * pulse))
            inst_txt = pygame.font.Font(None, 36).render("Appuyez sur ESPACE pour continuer", True, inst_color)
            self.display_surface.blit(inst_txt, (SCREEN_WIDTH//2 - inst_txt.get_width()//2, SCREEN_HEIGHT//2 + 80))
            
            self.particles.draw(self.display_surface)
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                game_instance.change_state("menu")
            return

        # HUD amélioré
        hud_bg = pygame.Surface((400, 50), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 120))
        pygame.draw.rect(hud_bg, (255, 255, 255, 100), hud_bg.get_rect(), 2, border_radius=8)
        self.display_surface.blit(hud_bg, (SCREEN_WIDTH//2 - 200, 10))
        
        hud_txt = self.font.render(f"À trier : {self.current_trash.item_name}", True, (255, 255, 255))
        self.display_surface.blit(hud_txt, (SCREEN_WIDTH//2 - hud_txt.get_width()//2, 20))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if not self.current_trash.is_thrown:
            if mouse_pressed:
                self.aiming = True
                # Trajectoire prédictive améliorée
                self._draw_trajectory_prediction(mouse_pos)
            elif self.aiming:
                self.aiming = False
                dx = self.current_trash.rect.centerx - mouse_pos[0]
                dy = self.current_trash.rect.centery - mouse_pos[1]
                # Mise à l'échelle de la vélocité initiale
                self.current_trash.velocity = pygame.Vector2(dx * 5, dy * 5)
                self.current_trash.is_thrown = True
        else:
            hit_bins = pygame.sprite.spritecollide(self.current_trash, self.bins, False)
            if hit_bins:
                expected = self.get_expected_bin(self.current_trash.item_name)
                if hit_bins[0].color_name == expected:
                    game_instance.score += 50
                    self.feedback_msg = SUCCESS_MESSAGES.get(expected, "Bravo !")
                    self.feedback_color = (100, 255, 100)
                    # Effet de succès
                    self.particles.emit_sparkle(
                        self.current_trash.rect.centerx,
                        self.current_trash.rect.centery,
                        color=(100, 255, 100),
                        count=25
                    )
                else:
                    game_instance.score = max(0, game_instance.score - 10)
                    self.feedback_msg = self.get_failure_message(self.current_trash.item_name)
                    self.feedback_color = (255, 100, 100)
                    # Effet d'échec
                    self.particles.emit_sparkle(
                        self.current_trash.rect.centerx,
                        self.current_trash.rect.centery,
                        color=(255, 100, 100),
                        count=15
                    )
                
                self.current_trash.velocity = pygame.Vector2(0, 0)
                self.current_trash.gravity = 0
                self.feedback_timer = 3.0
            elif self.current_trash.rect.y > SCREEN_HEIGHT or self.current_trash.rect.x < -100 or self.current_trash.rect.x > SCREEN_WIDTH + 100:
                self.current_trash.kill()
                self.spawn_next_trash()

        self.visible_sprites.update(dt)
        self.visible_sprites.draw(self.display_surface)
        self.particles.draw(self.display_surface)
        
        self._draw_title()
    
    def _draw_trajectory_prediction(self, mouse_pos):
        """Dessine une trajectoire prédictive du lancer"""
        start_x = self.current_trash.rect.centerx
        start_y = self.current_trash.rect.centery
        
        dx = start_x - mouse_pos[0]
        dy = start_y - mouse_pos[1]
        vx = dx * 5
        vy = dy * 5
        gravity = 700
        
        # Dessiner la ligne de visée
        pygame.draw.line(self.display_surface, (255, 100, 100, 150), 
                        (start_x, start_y), mouse_pos, 2)
        
        # Simuler la trajectoire
        points = []
        sim_x, sim_y = float(start_x), float(start_y)
        sim_vx, sim_vy = vx, vy
        
        for i in range(40):
            dt = 0.03
            sim_vy += gravity * dt
            sim_x += sim_vx * dt
            sim_y += sim_vy * dt
            
            if sim_y > SCREEN_HEIGHT or sim_x < 0 or sim_x > SCREEN_WIDTH:
                break
            
            points.append((int(sim_x), int(sim_y)))
        
        # Dessiner les points de la trajectoire avec dégradé
        for i, point in enumerate(points):
            alpha = int(255 * (1 - i / len(points))) if points else 255
            size = max(1, 4 - i // 10)
            color = (255, 255, 255)
            
            if i % 3 == 0:  # Dessiner un point sur 3 pour un effet pointillé
                pygame.draw.circle(self.display_surface, color, point, size)
    
    def _draw_title(self):
        """Dessine le titre du niveau avec animation"""
        if self.level_time >= 4.0:
            return
            
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

        title_surf = self.title_font.render(self.title_text, True, (255, 255, 255))
        shadow_surf = self.title_font.render(self.title_text, True, (0, 0, 0))
        
        # Glow
        glow_width = title_surf.get_width() + 60
        glow_height = title_surf.get_height() + 40
        glow_surf = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
        glow_alpha = max(0, alpha // 4)
        pygame.draw.rect(glow_surf, (100, 200, 100, glow_alpha),
                       (0, 0, glow_width, glow_height), border_radius=15)
        
        glow_x = SCREEN_WIDTH // 2 - glow_width // 2
        self.display_surface.blit(glow_surf, (glow_x, y_pos - 20), special_flags=pygame.BLEND_ADD)
        
        title_x = SCREEN_WIDTH // 2 - title_surf.get_width() // 2
        
        if alpha < 255:
            shadow_surf.set_alpha(alpha)
            title_surf.set_alpha(alpha)
        
        self.display_surface.blit(shadow_surf, (title_x + 3, y_pos + 3))
        self.display_surface.blit(title_surf, (title_x, y_pos))

