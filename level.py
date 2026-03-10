from pathlib import Path
import pygame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH, SOFT_YELLOW, OFF_WHITE, SOFT_CYAN
from player import Player

class Level:
    def __init__(self, surface):
        self.display_surface = surface
        self.world_width = SCREEN_WIDTH
        # Équipe : 5200 c'est la hauteur du niveau pour nos tests. On ajustera ça quand on fera le vrai level design.
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
        # Équipe : Le 0.65 sert à décentrer la caméra pour voir plus loin vers le haut (là où on va).
        target = self.player.position.y - SCREEN_HEIGHT * 0.65
        max_camera = self.world_height - SCREEN_HEIGHT
        self.camera_y = max(0, min(max_camera, target))

    def draw_background(self):
        # Équipe : Grosse opti ici, on ne calcule et on ne dessine que les étoiles qui sont visibles à l'écran pour économiser le CPU.
        start_row = int(self.camera_y // 180)
        end_row = int((self.camera_y + SCREEN_HEIGHT) // 180) + 2

        for row in range(start_row, end_row):
            world_y_1 = row * 180 + 40
            world_y_2 = row * 180 + 100
            x1 = 80 + (row * 7) % (self.world_width - 160)
            x2 = 80 + (row * 13) % (self.world_width - 160)

            screen_y_1 = int(world_y_1 - self.camera_y)
            screen_y_2 = int(world_y_2 - self.camera_y)

            if -5 <= screen_y_1 <= SCREEN_HEIGHT + 5:
                pygame.draw.circle(self.display_surface, OFF_WHITE, (int(x1), screen_y_1), 2)
            if -5 <= screen_y_2 <= SCREEN_HEIGHT + 5:
                pygame.draw.circle(self.display_surface, OFF_WHITE, (int(x2), screen_y_2), 2)

        launch_pad = pygame.Rect(int(SCREEN_WIDTH * 0.5 - 90), int(self.ground_y + 50 - self.camera_y), 180, 10)
        pygame.draw.rect(self.display_surface, SOFT_CYAN, launch_pad, border_radius=4)

    def draw_sprites(self):
        for sprite in self.visible_sprites:
            screen_pos = (sprite.position.x, sprite.position.y - self.camera_y)
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