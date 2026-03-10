from pathlib import Path
import pygame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH, SOFT_YELLOW, OFF_WHITE, SOFT_CYAN
from player import Player


class Level:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()

        self.world_width = SCREEN_WIDTH
        self.world_height = 5200
        self.ground_y = self.world_height - 90

        self.visible_sprites = pygame.sprite.Group()
        self.player = Player(
            (self.world_width * 0.5, self.ground_y),
            [self.visible_sprites],
            self.world_width,
            self.world_height,
            self.ground_y
        )

        self.font = pygame.font.Font(None, 32)
        self.camera_y = self.world_height - SCREEN_HEIGHT
        # Équipe : score en placeholder, la vraie logique ira dans run() ou un manager dédié.
        self.score = 0
        self.score_file = Path(__file__).with_name('score.txt')
        self.high_score = self.load_high_score()
        self.star_positions = self.generate_stars()

    def load_high_score(self):
        # Équipe : on garde un format ultra simple (juste un entier dans score.txt).
        if not self.score_file.exists():
            self.score_file.write_text('0', encoding='utf-8')
            return 0

        content = self.score_file.read_text(encoding='utf-8').strip()
        if content.isdigit():
            return int(content)

        self.score_file.write_text('0', encoding='utf-8')
        return 0

    def generate_stars(self):
        stars = []
        for row in range(0, self.world_height, 180):
            x1 = 80 + (row * 7) % (self.world_width - 160)
            x2 = 80 + (row * 13) % (self.world_width - 160)
            stars.append((x1, row + 40))
            stars.append((x2, row + 100))
        return stars

    def update_camera(self):
        # Équipe : ajustez 0.65 si vous voulez cadrer plus haut ou plus bas.
        target = self.player.position.y - SCREEN_HEIGHT * 0.65
        max_camera = self.world_height - SCREEN_HEIGHT
        self.camera_y = max(0, min(max_camera, target))

    def draw_background(self):
        for x, world_y in self.star_positions:
            screen_y = int(world_y - self.camera_y)
            if -5 <= screen_y <= SCREEN_HEIGHT + 5:
                pygame.draw.circle(self.display_surface, OFF_WHITE, (int(x), screen_y), 2)

        launch_pad = pygame.Rect(int(SCREEN_WIDTH * 0.5 - 90), int(self.ground_y + 50 - self.camera_y), 180, 10)
        pygame.draw.rect(self.display_surface, SOFT_CYAN, launch_pad, border_radius=4)

    def draw_sprites(self):
        for sprite in self.visible_sprites:
            screen_pos = (sprite.position.x, sprite.position.y - self.camera_y)
            screen_rect = sprite.image.get_rect(center=screen_pos)
            self.display_surface.blit(sprite.image, screen_rect)

    def draw_hud(self):
        score_info = f"Score : {self.score}   Meilleur score : {self.high_score}"
        controls_info = "Appuie sur ESPACE pour décoller | Gauche/Droite pour diriger"

        score_text = self.font.render(score_info, True, SOFT_YELLOW)
        controls_text = self.font.render(controls_info, True, SOFT_YELLOW)

        self.display_surface.blit(score_text, (20, 18))
        self.display_surface.blit(controls_text, (20, 48))

    def run(self, dt):
        # Équipe: injectez ici obstacles/orbes quand vous ferez la phase 1 complète.
        self.visible_sprites.update(dt)
        self.update_camera()
        self.draw_background()
        self.draw_sprites()
        self.draw_hud()