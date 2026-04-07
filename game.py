import pygame
import os
from settings import BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, SOFT_YELLOW, OFF_WHITE
from level import Level
from sorting_level import SortingLevel
from utils import load_texture, load_sound, play_music
import random

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.levels = [
            Level(self.screen, level_type='debris', end_y=-8000),
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
        self.state = new_state
        if new_state == 'game_over':
            self.save_high_score()
            pygame.mixer.music.stop()
        elif new_state == 'sorting_level':
            self.sorting_scene = SortingLevel(self.screen, self.collected_trash[:])
            play_music('Project_27 SK NV3.wav')
        elif new_state == 'menu':
            self.save_high_score()
            play_music('Project_27 SK MENU.wav')

    @property
    def current_level(self):
        return self.levels[self.current_level_index]

    def draw_menu(self):
        logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(self.logo, logo_rect)

        # On dessine le bouton JOUER
        button_rect = pygame.Rect(0, 0, 250, 70)
        button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Si la souris est sur le bouton, on le met en surbrillance
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, SOFT_YELLOW, button_rect, border_radius=15)
            text_color = BG_COLOR
        else:
            pygame.draw.rect(self.screen, OFF_WHITE, button_rect, border_radius=15)
            text_color = BG_COLOR

        pygame.draw.rect(self.screen, SOFT_YELLOW, button_rect, width=3, border_radius=15)

        text_surf = self.font.render('JOUER', True, text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

        # Affichage informatif "ou appuyer sur Espace" en plus petit
        small_font = pygame.font.Font(None, 32)
        info_surf = small_font.render('Ou appuyez sur ESPACE', True, (200, 200, 200))
        info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 230))
        self.screen.blit(info_surf, info_rect)

        hs_surf = small_font.render(f'High Score: {self.high_score}', True, (255, 255, 255))
        self.screen.blit(hs_surf, (10, 10))

    def draw_game_over(self):
        go_surf = self.font.render(f'GAME OVER - Score : {self.score} - Espace pour Menu', True, (255, 50, 50))
        self.screen.blit(go_surf, (SCREEN_WIDTH//2 - go_surf.get_width()//2, SCREEN_HEIGHT//2))

    def handle_menu_input(self):
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
                Level(self.screen, level_type='debris', end_y=-8000),
                Level(self.screen, level_type='mixed')
            ]
            self.current_level_index = 0
            self.change_state('playing')

    def handle_game_over_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.change_state('menu')

    def run(self, dt):
        # Ne pas remplir l'écran ici - le niveau gère maintenant le dégradé du ciel
        # self.screen.fill(BG_COLOR)

        if self.state == 'menu':
            self.screen.fill(BG_COLOR)
            self.handle_menu_input()
            self.draw_menu()
        elif self.state == 'playing':
            level_status = self.current_level.run(dt, self)
            if level_status == "completed":
                # Joue un son de victoire aléatoire
                win_sounds = [ws for ws in self.victory_sounds if ws]
                if win_sounds:
                    random.choice(win_sounds).play()

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
            self.draw_game_over()
            self.handle_game_over_input()
        elif self.state == 'sorting_level':
            if self.sorting_scene:
                self.sorting_scene.run(dt, self)
