import sys

with open('level.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Corrige les limites d'apparition pour qu'elles soient complètement hors de vue et corrige l'ajout des déchets pour sauvegarder le tuple

# Correction des limites d'apparition
old_spawn = '''        cam_center_x = self.camera_x + SCREEN_WIDTH * 0.5
        cam_center_y = self.camera_y + SCREEN_HEIGHT * 0.5
        spawn_radius_x = SCREEN_WIDTH * 0.9
        spawn_radius_y = SCREEN_HEIGHT * 0.9

        x, y = cam_center_x, cam_center_y
        for _ in range(8):
            x = random.uniform(cam_center_x - spawn_radius_x, cam_center_x + spawn_radius_x)
            y = random.uniform(cam_center_y - spawn_radius_y, cam_center_y + spawn_radius_y)
            if pygame.Vector2(x, y).distance_to(self.player.position) > 180: break'''

new_spawn = '''        cam_center_x = self.camera_x + SCREEN_WIDTH * 0.5
        cam_center_y = self.camera_y + SCREEN_HEIGHT * 0.5
        spawn_radius_x = SCREEN_WIDTH * 1.2
        spawn_radius_y = SCREEN_HEIGHT * 1.2
        
        # Force l'apparition en dehors des limites de l'écran
        if random.random() < 0.5:
            # Apparition à gauche ou à droite
            x = self.camera_x + (SCREEN_WIDTH + max(100, random.random()*400)) * random.choice([1, -1])
            y = self.camera_y + random.uniform(-200, SCREEN_HEIGHT + 200)
        else:
            # Apparition en haut ou en bas
            x = self.camera_x + random.uniform(-200, SCREEN_WIDTH + 200)
            y = self.camera_y + (SCREEN_HEIGHT + max(100, random.random()*400)) * random.choice([1, -1])'''

code = code.replace(old_spawn, new_spawn)


# Correction de l'ajout des déchets collectés
old_append = 'game_instance.collected_trash.append(getattr(obstacle, "item_name", "Inconnu"))'
new_append = 'game_instance.collected_trash.append((getattr(obstacle, "item_name", "Inconnu"), obstacle.image.copy()))'
code = code.replace(old_append, new_append)


# Ajuste l'échelle spécifiquement pour les Débris et Déchets, remplaçant les tailles de base
old_cls_def = '''class DebrisItem(FloatingObstacle):
    obstacle_type = "debris"

class DechetItem(FloatingObstacle):
    obstacle_type = "dechet"'''

new_cls_def = '''class DebrisItem(FloatingObstacle):
    obstacle_type = "debris"
    def __init__(self, position, image, groups):
        super().__init__(position, image, groups)
        w, h = image.get_size()
        scale = min(80.0 / max(1, w), 80.0 / max(1, h)) 
        self.image = pygame.transform.smoothscale(image, (max(12, int(w * scale)), max(12, int(h * scale))))
        self.collision_radius = max(10, min(self.image.get_width(), self.image.get_height()) * 0.33)

class DechetItem(FloatingObstacle):
    obstacle_type = "dechet"
    def __init__(self, position, image, groups):
        super().__init__(position, image, groups)
        w, h = image.get_size()
        scale = min(40.0 / max(1, w), 40.0 / max(1, h)) 
        self.image = pygame.transform.smoothscale(image, (max(12, int(w * scale)), max(12, int(h * scale))))
        self.collision_radius = max(10, min(self.image.get_width(), self.image.get_height()) * 0.33)'''

code = code.replace(old_cls_def, new_cls_def)

with open('level.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("level.py adjusted")
