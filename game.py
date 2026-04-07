import pygame
import os
import math
from settings import BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, SOFT_YELLOW, OFF_WHITE
from level import Level
from sorting_level import SortingLevel
from utils import load_texture, load_sound, play_music
from particle_system import ParticleEmitter
import random

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.levels = [
            Level(self.screen, level_type='debris', end_y=-16000),
            Level(self.screen, level_type='mixed')
        ]
        self.current_level_index = 0

        self.state = 'menu'
        self.score = 0
        self.collected_trash = []
        self.high_score = self.load_high_score()

        self.font = pygame.font.Font(None, 48)
        self.logo = load_texture('MissingTexture.jpg', scale_to=(350, 350))
        self.sorting_scene = None

        # Sons
        self.takeoff_sound = load_sound('Décollage Fusée.wav')
        self.victory_sounds = [load_sound('bruit victoire.wav'), load_sound('bruit victoire 2.wav')]

        # Système de particules pour le menu
        self.menu_particles = ParticleEmitter(max_particles=200)
        self.menu_time = 0.0
        
        # Animation du logo
        self.logo_scale = 1.0
        self.logo_angle = 0.0
        
        # Étoiles de fond du menu
        self.menu_stars = []
        for _ in range(100):
            self.menu_stars.append({
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(1, 3),
                'speed': random.uniform(0.2, 1.0),
                'twinkle_phase': random.uniform(0, math.tau)
            })
        
        # Transition fade
        self.fade_alpha = 255
        self.fading_in = True
        self.fading_out = False
        self.fade_target_state = None

        play_music('Project_27 SK MENU.wav')

    def load_high_score(self):
        if os.path.exists('score.txt'):
            with open('score.txt', 'r') as f:
                try:
                    return int(f.read())
                except ValueError:
                    return 0
        return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open('score.txt', 'w') as f:
                f.write(str(self.high_score))

    def change_state(self, new_state):
        # Transition avec fade
        self.fading_out = True
        self.fade_target_state = new_state
    
    def _apply_state_change(self, new_state):
        """Applique le changement d'état après le fade out"""
        self.state = new_state
        if new_state == 'game_over':
            self.save_high_score()
            pygame.mixer.music.stop()
        elif new_state == 'sorting_level':
            self.sorting_scene = SortingLevel(self.screen, self.collected_trash[:])
            play_music('Project_27 SK NV3.wav')
        elif new_state == 'menu':
            self.save_high_score()
            self.menu_time = 0.0
            play_music('Project_27 SK MENU.wav')

    @property
    def current_level(self):
        return self.levels[self.current_level_index]

    def draw_menu(self, dt):
        self.menu_time += dt
        
        # Fond avec gradient
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            color = (
                int(15 + 10 * ratio),
                int(15 + 10 * ratio),
                int(35 + 15 * ratio)
            )
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Dessiner les étoiles avec scintillement
        for star in self.menu_stars:
            star['y'] += star['speed'] * dt * 20
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.uniform(0, SCREEN_WIDTH)
            
            twinkle = 0.5 + 0.5 * math.sin(self.menu_time * 3 + star['twinkle_phase'])
            brightness = int(150 + 105 * twinkle)
            color = (brightness, brightness, min(255, brightness + 20))
            pygame.draw.circle(self.screen, color, (int(star['x']), int(star['y'])), int(star['size']))
        
        # Particules flottantes
        if random.random() < 0.1:
            self.menu_particles.emit_sparkle(
                random.uniform(0, SCREEN_WIDTH),
                random.uniform(0, SCREEN_HEIGHT),
                color=(100, 150, 255),
                count=1
            )
        self.menu_particles.update(dt)
        self.menu_particles.draw(self.screen)
        
        # Animation du logo (pulsation + légère rotation)
        self.logo_scale = 1.0 + 0.03 * math.sin(self.menu_time * 2)
        self.logo_angle = 2 * math.sin(self.menu_time * 0.5)
        
        scaled_logo = pygame.transform.rotozoom(self.logo, self.logo_angle, self.logo_scale)
        logo_rect = scaled_logo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        
        # Glow derrière le logo
        glow_size = max(scaled_logo.get_width(), scaled_logo.get_height()) + 80
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_intensity = 0.5 + 0.3 * math.sin(self.menu_time * 1.5)
        for r in range(glow_size // 2, 10, -10):
            alpha = int(40 * glow_intensity * (r / (glow_size // 2)))
            pygame.draw.circle(glow_surf, (100, 150, 255, alpha), (glow_size // 2, glow_size // 2), r)
        self.screen.blit(glow_surf, (logo_rect.centerx - glow_size // 2, logo_rect.centery - glow_size // 2), 
                        special_flags=pygame.BLEND_ADD)
        
        self.screen.blit(scaled_logo, logo_rect)

        # Bouton JOUER amélioré
        button_rect = pygame.Rect(0, 0, 250, 70)
        button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150)
        
        mouse_pos = pygame.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        # Effet de glow sur le bouton
        if is_hover:
            glow_btn = pygame.Surface((button_rect.width + 40, button_rect.height + 40), pygame.SRCALPHA)
            pulse = 0.6 + 0.4 * math.sin(self.menu_time * 5)
            for i in range(3):
                alpha = int(60 * pulse) - i * 15
                pygame.draw.rect(glow_btn, (255, 230, 100, max(0, alpha)), 
                               (i * 5, i * 5, button_rect.width + 40 - i * 10, button_rect.height + 40 - i * 10),
                               border_radius=20)
            self.screen.blit(glow_btn, (button_rect.x - 20, button_rect.y - 20), special_flags=pygame.BLEND_ADD)
        
        # Fond du bouton
        btn_color = SOFT_YELLOW if is_hover else OFF_WHITE
        pygame.draw.rect(self.screen, btn_color, button_rect, border_radius=15)
        pygame.draw.rect(self.screen, SOFT_YELLOW, button_rect, width=3, border_radius=15)

        text_color = BG_COLOR
        text_surf = self.font.render('JOUER', True, text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

        # Texte info avec animation
        small_font = pygame.font.Font(None, 32)
        info_alpha = int(150 + 50 * math.sin(self.menu_time * 2))
        info_surf = small_font.render('Ou appuyez sur ESPACE', True, (200, 200, 200))
        info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 230))
        self.screen.blit(info_surf, info_rect)

        # High score avec style
        hs_bg = pygame.Surface((200, 40), pygame.SRCALPHA)
        hs_bg.fill((0, 0, 0, 100))
        self.screen.blit(hs_bg, (5, 5))
        hs_surf = small_font.render(f'🏆 High Score: {self.high_score}', True, (255, 215, 0))
        self.screen.blit(hs_surf, (15, 12))

    def draw_game_over(self, dt):
        # Fond semi-transparent avec effet
        self.screen.fill((20, 10, 10))
        
        # Effet de vignette
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for r in range(min(SCREEN_WIDTH, SCREEN_HEIGHT) // 2, 0, -20):
            alpha = int(100 * (1 - r / (min(SCREEN_WIDTH, SCREEN_HEIGHT) // 2)))
            pygame.draw.circle(vignette, (0, 0, 0, alpha), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), r + 200)
        self.screen.blit(vignette, (0, 0))
        
        # Texte GAME OVER avec effet de tremblement
        game_over_font = pygame.font.Font(None, 96)
        shake = random.uniform(-2, 2) if random.random() < 0.1 else 0
        go_surf = game_over_font.render('GAME OVER', True, (255, 50, 50))
        go_shadow = game_over_font.render('GAME OVER', True, (80, 0, 0))
        
        go_x = SCREEN_WIDTH // 2 - go_surf.get_width() // 2 + shake
        go_y = SCREEN_HEIGHT // 2 - 80
        
        self.screen.blit(go_shadow, (go_x + 4, go_y + 4))
        self.screen.blit(go_surf, (go_x, go_y))
        
        # Score
        score_surf = self.font.render(f'Score Final : {self.score}', True, (255, 255, 255))
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(score_surf, score_rect)
        
        # Instruction
        small_font = pygame.font.Font(None, 36)
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300)
        inst_color = (int(200 * pulse + 55), int(200 * pulse + 55), int(200 * pulse + 55))
        inst_surf = small_font.render('Appuyez sur ESPACE pour revenir au menu', True, inst_color)
        inst_rect = inst_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(inst_surf, inst_rect)

    def handle_menu_input(self):
        if self.fading_out:
            return
            
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        button_rect = pygame.Rect(0, 0, 250, 70)
        button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150)

        if keys[pygame.K_SPACE] or (mouse_pressed[0] and button_rect.collidepoint(mouse_pos)):
            if self.takeoff_sound:
                self.takeoff_sound.play()
            play_music('Project_27 SK NV1.wav')
            
            self.score = 0
            self.collected_trash.clear()
            self.levels = [
                Level(self.screen, level_type='debris', end_y=-16000),
                Level(self.screen, level_type='mixed')
            ]
            self.current_level_index = 0
            
            # Démarrer le fade out puis changer d'état
            self.fading_out = True
            self.fade_target_state = 'playing'

    def handle_game_over_input(self):
        if self.fading_out:
            return
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Retour au menu avec ESPACE ou clic souris
        if keys[pygame.K_SPACE] or mouse_pressed[0]:
            self.change_state('menu')
    
    def _update_fade(self, dt):
        """Gère les transitions fade in/out"""
        fade_speed = 400  # Alpha par seconde
        
        if self.fading_in:
            self.fade_alpha -= fade_speed * dt
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fading_in = False
        
        if self.fading_out:
            self.fade_alpha += fade_speed * dt
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.fading_out = False
                self.fading_in = True
                if self.fade_target_state:
                    self._apply_state_change(self.fade_target_state)
                    self.fade_target_state = None
    
    def _draw_fade(self):
        """Dessine l'overlay de fade"""
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(int(self.fade_alpha))
            self.screen.blit(fade_surf, (0, 0))

    def run(self, dt):
        # Mise à jour des transitions
        self._update_fade(dt)
        
        if self.state == 'menu':
            self.handle_menu_input()
            self.draw_menu(dt)
        elif self.state == 'playing':
            level_status = self.current_level.run(dt, self)
            if level_status == "completed":
                # Keep track of old player state
                old_player = self.current_level.player
                pos = (old_player.position.x, old_player.position.y)
                vel = (old_player.velocity.x, old_player.velocity.y)
                
                self.current_level_index += 1
                if self.current_level_index >= len(self.levels):
                    # Finished all levels
                    if len(self.collected_trash) > 0:
                        self.change_state("sorting_level")
                    else:
                        self.change_state("game_over")
                else:
                    if self.current_level_index == 1:
                        play_music('Project_27 SK NV2.wav')
                    
                    # Initialize the next level right now manually to pass player state
                    next_level = self.levels[self.current_level_index]
                    # We actually need to re-initialize it to pass the params, or just update its player.
                    # It's cleaner to re-instantiate it here:
                    level_type = next_level.level_type
                    end_y = next_level.end_y
                    self.levels[self.current_level_index] = Level(self.screen, level_type=level_type, end_y=end_y, player_start_pos=pos, player_velocity=vel)

        elif self.state == 'game_over':
            self.draw_game_over(dt)
            self.handle_game_over_input()
        elif self.state == 'sorting_level':
            if self.sorting_scene:
                self.sorting_scene.run(dt, self)
        
        # Appliquer le fade par-dessus tout
        self._draw_fade()
