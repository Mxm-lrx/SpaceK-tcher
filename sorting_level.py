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
        self.image = pygame.Surface((100, 150))
        self.image.fill(rect_color)

        font = pygame.font.Font(None, 36)
        text = font.render(color_name[:4], True, (0, 0, 0))
        self.image.blit(text, (10, 10))

        self.rect = self.image.get_rect(midbottom=position)

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

        self.visible_sprites = pygame.sprite.Group()
        self.bins = pygame.sprite.Group()

        Bin("Verte", (100, 255, 100), (SCREEN_WIDTH * 0.25, SCREEN_HEIGHT - 50), [self.visible_sprites, self.bins])
        Bin("Jaune", (255, 255, 100), (SCREEN_WIDTH * 0.50, SCREEN_HEIGHT - 50), [self.visible_sprites, self.bins])
        Bin("Bleue", (100, 100, 255), (SCREEN_WIDTH * 0.75, SCREEN_HEIGHT - 50), [self.visible_sprites, self.bins])

        self.current_trash = None
        self.aiming = False
        self.start_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
        
        self.feedback_timer = 0
        self.feedback_msg = ""
        self.feedback_color = (255, 255, 255)
        
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
        self.display_surface.fill((40, 40, 40))

        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            msg_surf = pygame.font.Font(None, 36).render(self.feedback_msg, True, self.feedback_color)
            self.display_surface.blit(msg_surf, (SCREEN_WIDTH//2 - msg_surf.get_width()//2, SCREEN_HEIGHT//2 - 100))
            if self.feedback_timer <= 0:
                self.current_trash.kill()
                self.spawn_next_trash()
            
            self.visible_sprites.draw(self.display_surface)
            return

        if self.current_trash is None:
            txt = self.font.render("Tri termine ! Espace pour Menu.", True, (255, 255, 255))
            self.display_surface.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//2))
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                game_instance.change_state("menu")
            return

        hud_txt = self.font.render(f"Dechet a trier : {self.current_trash.item_name}", True, (255, 255, 255))
        self.display_surface.blit(hud_txt, (20, 20))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if not self.current_trash.is_thrown:
            if mouse_pressed:
                self.aiming = True
                pygame.draw.line(self.display_surface, (255, 100, 100), self.current_trash.rect.center, mouse_pos, 3)
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
                else:
                    game_instance.score = max(0, game_instance.score - 10)
                    self.feedback_msg = self.get_failure_message(self.current_trash.item_name)
                    self.feedback_color = (255, 100, 100)
                
                self.current_trash.velocity = pygame.Vector2(0, 0)
                self.current_trash.gravity = 0
                self.feedback_timer = 3.0
            elif self.current_trash.rect.y > SCREEN_HEIGHT or self.current_trash.rect.x < -100 or self.current_trash.rect.x > SCREEN_WIDTH + 100:
                self.current_trash.kill()
                self.spawn_next_trash()

        self.visible_sprites.update(dt)
        self.visible_sprites.draw(self.display_surface)

