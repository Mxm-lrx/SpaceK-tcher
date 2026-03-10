from pathlib import Path
import math
import pygame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH, SOFT_YELLOW, OFF_WHITE, SOFT_CYAN
from player import Player

class Level:
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

    def update_camera(self):
        self.camera_x = self.player.position.x - SCREEN_WIDTH * 0.5
        self.camera_y = self.player.position.y - SCREEN_HEIGHT * 0.65

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

    def draw_sprites(self):
        for sprite in self.visible_sprites:
            screen_pos = (sprite.position.x - self.camera_x, sprite.position.y - self.camera_y)
            screen_rect = sprite.image.get_rect(center=screen_pos)
            self.display_surface.blit(sprite.image, screen_rect)

    def draw_hud(self):
        score_text = self.font.render(f"Score : {self.score}   Meilleur score : {self.high_score}", True, SOFT_YELLOW)
        controls_text = self.font.render("Appuie sur ESPACE pour décoller | Gauche/Droite pour diriger", True, SOFT_YELLOW)
        self.display_surface.blit(score_text, (20, 18))
        self.display_surface.blit(controls_text, (20, 48))

    def run(self, dt):
        self.visible_sprites.update(dt)
        self.update_camera()
        self.draw_background()
        self.draw_sprites()
        self.draw_hud()