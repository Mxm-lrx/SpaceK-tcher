from settings import BG_COLOR
from level import Level

class Game:
    def __init__(self, screen):
        self.screen = screen
        # Équipe : C'est ici qu'on listera tous nos niveaux plus tard (Level2, Level3...). Pour l'instant on n'en a qu'un seul de prêt.
        self.levels = [Level(self.screen)]
        self.current_level_index = 0

    @property
    def current_level(self):
        return self.levels[self.current_level_index]

    def run(self, dt):
        self.screen.fill(BG_COLOR)
        self.current_level.run(dt)