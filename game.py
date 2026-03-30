import pygame
import os
from settings import BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, SOFT_YELLOW
from level import Level
from sorting_level import SortingLevel
from utils import load_texture

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.levels = [
            Level(self.screen, level_type='debris', end_y=-5000),
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
        elif new_state == 'sorting_level':
            self.sorting_scene = SortingLevel(self.screen, self.collected_trash[:])
        elif new_state == 'menu':
            self.save_high_score()

    @property
    def current_level(self):
        return self.levels[self.current_level_index]

    def draw_menu(self):
        logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(self.logo, logo_rect)

        text_surf = self.font.render('Appuie sur ESPACE pour Jouer', True, SOFT_YELLOW)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 180))
        self.screen.blit(text_surf, text_rect)

        hs_surf = self.font.render(f'High Score: {self.high_score}', True, (255, 255, 255))
        self.screen.blit(hs_surf, (10, 10))

    def draw_game_over(self):
        go_surf = self.font.render(f'GAME OVER - Score : {self.score} - Espace pour Menu', True, (255, 50, 50))
        self.screen.blit(go_surf, (SCREEN_WIDTH//2 - go_surf.get_width()//2, SCREEN_HEIGHT//2))

    def handle_menu_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.score = 0
            self.collected_trash.clear()
            self.levels = [
                Level(self.screen, level_type='debris', end_y=-5000),
                Level(self.screen, level_type='mixed')
            ]
            self.current_level_index = 0
            self.change_state('playing')

    def handle_game_over_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.change_state('menu')

    def run(self, dt):
        self.screen.fill(BG_COLOR)

        if self.state == 'menu':
            self.handle_menu_input()
            self.draw_menu()
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
