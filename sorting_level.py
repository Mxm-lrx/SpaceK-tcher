"""
========================================================================
                    NIVEAU 3: LE JEU DE TRI - SpaceK'tcher
========================================================================

Ce module implémente le dernier niveau du jeu: un mini-jeu éducatif
où le joueur doit TRIER LES DÉCHETS collectés dans le niveau précédent.

CONCEPT:
1. Le joueur lance chaque déchet à la souris vers les bonnes poubelles
2. 3 catégories de recyclage: VERTE (verre), JAUNE (emballages), BLEUE (autres)
3. Chaque bonne réponse = +50 points
4. Chaque mauvaise réponse = -10 points
5. À la fin: écran de victoire avec score final

MÉCANIQUE DE JEU:
- Souris enfoncée = "viser" (affiche trajectoire)
- Souris relâchée = lancer le déchet
- Collision avec la bonne poubelle = succès + étincelles vertes
- Collision avec mauvaise poubelle = échec + étincelles rouges + message

DIDACTIQUE:
Cette partie enseigne le tri sélectif et la gestion des déchets.
Les messages d'erreur expliquer pourquoi chaque catégorie existe.
========================================================================
"""
import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TRASH_CATEGORIES
from utils import load_texture

# DICTIONNAIRES DE MESSAGES: Feedback pédagogique pour le joueur

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
    """Représente une poubelle de tri stylisée.
    
    Une poubelle a une couleur correspondant à une catégorie:
    - Verte: Verre (100% recyclable)
    - Jaune: Emballages (plastique, métal, carton)
    - Bleue: Autres déchets (résiduels)
    
    Le sprite est dessiné procéduralement avec:
    - Un gradient de couleur pour le corps (effet 3D)
    - Un couvercle avec relief
    - Un symbole Unicode (♻, 📦, 🗑)
    - Un label de couleur en bas
    """
    
    def __init__(self, color_name, rect_color, position, groups):
        """Initialise une poubelle.
        
        Args:
            color_name: "Verte", "Jaune" ou "Bleue"
            rect_color: Tuple RGB de la couleur (ex: (100, 255, 100))
            position: Tuple (x, y) position à l'écran
            groups: Liste des groupes pygame pour le rendu
        """
        super().__init__(groups)
        self.color_name = color_name
        self.base_color = rect_color
        
        # CRÉATION DU SPRITE: dessiner la poubelle
        width, height = 120, 160
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # CORPS: gradient de couleur pour l'effet 3D (plutôt lumineux en haut, plus sombre en bas)
        for i in range(height - 20):
            ratio = i / (height - 20)  # 0 (haut) à 1 (bas)
            # Appliquer un dégradé: plus sombre vers le bas
            color = tuple(max(0, int(c * (0.7 + 0.3 * ratio))) for c in rect_color[:3])
            pygame.draw.line(self.image, color, (10, 20 + i), (width - 10, 20 + i))
        
        # COUVERCLE: ellipse arrondie avec relief
        pygame.draw.ellipse(self.image, tuple(min(255, c + 30) for c in rect_color[:3]), 
                          (5, 10, width - 10, 25))  # Plus clair (plus illuminé)
        pygame.draw.ellipse(self.image, (50, 50, 50), (5, 10, width - 10, 25), 2)  # Contour sombre
        
        # CONTOUR: rectangle sombre autour du corps
        pygame.draw.rect(self.image, (50, 50, 50), (10, 20, width - 20, height - 25), 3, border_radius=5)
        
        # SYMBOLE DE RECYCLAGE: icône Unicode pour identifier visuellement
        symbol_colors = {
            "Verte": "♻",    # Symbole de recyclage
            "Jaune": "📦",    # Boîte/emballage
            "Bleue": "🗑"     # Poubelle générique
        }
        font = pygame.font.Font(None, 48)
        symbol = font.render(symbol_colors.get(color_name, "?"), True, (255, 255, 255))
        symbol_rect = symbol.get_rect(center=(width // 2, height // 2 + 10))
        self.image.blit(symbol, symbol_rect)
        
        # LABEL: nom de la poubelle en bas
        label_font = pygame.font.Font(None, 28)
        label = label_font.render(color_name, True, (255, 255, 255))
        label_rect = label.get_rect(center=(width // 2, height - 15))
        
        # Fond semi-transparent derrière le label (lisibilité)
        label_bg = pygame.Surface((label.get_width() + 10, label.get_height() + 4), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 150))
        self.image.blit(label_bg, (label_rect.x - 5, label_rect.y - 2))
        self.image.blit(label, label_rect)

        self.rect = self.image.get_rect(midbottom=position)
        self.hover = False
    
    def set_hover(self, is_hover):
        """Active/désactive l'effet de surbrillance (quand le déchet est au-dessus).
        
        Args:
            is_hover: True si la poubelle est surbrillancée
        """
        self.hover = is_hover

class TrashThrow(pygame.sprite.Sprite):
    """Représente un déchet qu'on peut lancer vers les poubelles.
    
    La physique simule un projectile:
    - Mouvement parabolique (X horizontal, Y vertical avec gravité)
    - Accélération due à la gravité (9.81 m/s² simulé à 700 pixels/s²)
    - Collision avec les poubelles détectée automatiquement
    
    États:
    - is_thrown = False: déchet au repos, en attente d'être lancé
    - is_thrown = True: déchet en vol (physique active)
    """
    
    def __init__(self, item_name, image, position, groups):
        """Initialise un déchet à lancer.
        
        Args:
            item_name: Nom du déchet (ex: "bouteilleverre", "canette")
            image: Image pygame du déchet
            position: Tuple (x, y) position initiale
            groups: Listes des groupes pygame pour le rendu
        """
        super().__init__(groups)
        self.item_name = item_name
        
        # REDIMENSIONNEMENT: adapter l'image à max 60x60 pixels
        w, h = image.get_size()
        scale = min(60.0 / max(1, w), 60.0 / max(1, h)) 
        self.image = pygame.transform.smoothscale(image, (int(w * scale), int(h * scale)))
        
        self.rect = self.image.get_rect(center=position)

        # PHYSIQUE
        self.velocity = pygame.Vector2(0, 0)  # (vx, vy) en pixels/seconde
        self.gravity = 700  # Accélération vers le bas (pixels/s²)
        self.is_thrown = False  # Le déchet est-il lancé?

    def update(self, dt):
        """Met à jour la position du déchet si lancé.
        
        Applique la physique classique:
        - Accélération Y due à la gravité
        - Mise à jour de position: p += v*dt
        
        Args:
            dt: Delta time en secondes
        """
        if self.is_thrown:
            # Appliquer la gravité (accélération de la vélocité)
            self.velocity.y += self.gravity * dt
            
            # Mettre à jour la position
            self.rect.x += self.velocity.x * dt
            self.rect.y += self.velocity.y * dt

class SortingLevel:
    """Gestionnaire du niveau 3: Le centre de tri interactif.
    
    C'est le dernier niveau du jeu. Le joueur doit:
    1. Lancer des déchets collectés vers les bonnes poubelles
    2. Apprendre les catégories de tri
    3. Accumuler des points pour les bonnes réponses
    
    FLUX:
    1. __init__(): créer les 3 poubelles et charger les déchets
    2. run(dt): boucle principale - gestion input, physique, collisions
    3. Retour au menu quand tous les déchets sont triés
    """
    
    def __init__(self, surface, trash_list):
        """Initialise le niveau de tri.
        
        Args:
            surface: Surface pygame où dessiner
            trash_list: Liste de tuples (nom_déchet, image_pygame) collectés dans les niveaux précédents
        """
        self.display_surface = surface
        self.trash_list = trash_list  # Queue de déchets à trier
        self.font = pygame.font.Font(None, 48)

        # ANIMATIONS
        self.level_time = 0.0  # Temps de jeu
        self.title_text = "Niveau 3 : Le Grand Centre de Tri"
        self.title_font = pygame.font.Font(None, 64)

        # SPRITES
        self.visible_sprites = pygame.sprite.Group()
        self.bins = pygame.sprite.Group()

        # CRÉER LES 3 POUBELLES (espacées horizontalement)
        # Chacune avec 1/3 de la largeur d'écran
        Bin("Verte", (100, 255, 100), (SCREEN_WIDTH * 0.25, SCREEN_HEIGHT - 30), [self.visible_sprites, self.bins])
        Bin("Jaune", (255, 255, 100), (SCREEN_WIDTH * 0.50, SCREEN_HEIGHT - 30), [self.visible_sprites, self.bins])
        Bin("Bleue", (100, 100, 255), (SCREEN_WIDTH * 0.75, SCREEN_HEIGHT - 30), [self.visible_sprites, self.bins])

        # DÉCHET CURRENT
        self.current_trash = None
        self.aiming = False  # Joueur vise-t-il?
        self.start_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)  # Position de spawn des déchets
        
        # FEEDBACK (messages de succès/échec)
        self.feedback_timer = 0      # Durée du message à afficher
        self.feedback_msg = ""        # Texte du message
        self.feedback_color = (255, 255, 255)  # Couleur (vert=succès, rouge=échec)
        
        # SYSTÈMES D'EFFETS
        # Particules pour les étincelles de succès/échec
        from particle_system import ParticleEmitter
        self.particles = ParticleEmitter(max_particles=300)
        
        # FOND D'ÉTOILES (décor spatial)
        self.bg_stars = []
        import random
        for _ in range(80):
            self.bg_stars.append({
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(1, 2),
                'twinkle': random.uniform(0, math.tau)  # Phase pour scintillement
            })
        
        # Mettre le premier déchet en attente
        self.spawn_next_trash()

    def spawn_next_trash(self):
        """Créer le prochain déchet à trier.
        
        Prend le prochain item de self.trash_list, crée un sprite TrashThrow
        qui le rend actif sur l'écran. Le joueur commence la phase de VISÉE.
        
        Si la liste est vide -> self.current_trash=None (cf. run() pour détection de victoire)
        """
        if self.trash_list:
            # Retirer de la file un tuple (nom, surface_pygame)
            item_data = self.trash_list.pop(0)
            # Le tuple peut avoir 2 éléments ou être un objet direct
            if isinstance(item_data, tuple) and len(item_data) == 2:
                item_name, item_img = item_data
            else:
                # Fallback si format invalide
                item_name = str(item_data)
                item_img = pygame.Surface((40,40))
                item_img.fill((200,200,200))
            # Créer un projectile à la position fixe (haut-centre)
            self.current_trash = TrashThrow(item_name, item_img, self.start_pos, [self.visible_sprites])
        else:
            # No more trash = victoire!
            self.current_trash = None

    def get_expected_bin(self, item_name):
        """Déterminer la bonne poubelle pour un déchet.
        
        Utilise le dictionnaire TRASH_CATEGORIES pour matcher le nom du déchet
        aux 3 catégories:
        - "Verte" : VERRE (bouteilles, pots)
        - "Jaune" : EMBALLAGES (carton, plastique, métal)
        - "Bleue" : AUTRES (par défaut)
        
        En France, ce système de tri 3-couleurs est standard. En cas d'item inconnu,
        retourne "Bleue" (bac généraliste).
        
        Args:
            item_name: Nom du déchet (chaîne)
            
        Returns:
            Couleur du bac: "Verte", "Jaune", ou "Bleue"
        """
        # Parcourir les catégories et chercher un match (case-insensitive)
        for bin_color, items in TRASH_CATEGORIES.items():
            for item in items:
                if item.lower() in item_name.lower():
                    return bin_color
        # Fallback: si rien ne match, bac généraliste
        return "Bleue"

    def get_failure_message(self, item_name):
        """Récupérer le message d'erreur pédagogique pour un mauvais tri.
        
        Chaque déchet a un message expliquant où le tri était FAUX et pourquoi.
        Cela permet à l'enfant d'APPRENDRE en jouant.
        
        Si le déchet n'a pas de message spécifique, message générique.
        
        Args:
            item_name: Nom du déchet trié incorrectement
            
        Returns:
            Texte du message pédagogique
        """
        return FAILURE_MESSAGES.get(item_name.lower(), "Erreur : ce déchet ne va pas dans cette poubelle !")

    def run(self, dt, game_instance):
        """CŒUR DU NIVEAU 3 - Boucle principale du centre de tri.
        
        PHASES:
        1. VISÉE (feedback_timer==0, trash pas lancé):
           - Afficher la trajectoire prédictive sous la souris
           - À clique souris relâché: calculer vélocité et lancer
           
        2. VOL (trash lancé):
           - Appliquer la physique (gravité, collision)
           - Vérifier si déchet atteint une poubelle
           
        3. FEEDBACK (feedback_timer > 0):
           - Afficher le résultat (succès/échec) pendant 3 secondes
           - Actualiser le score (+50 succès, -10 échec)
           - Créer des effets visuels (étincelles)
           
        4. VICTOIRE (trash_list vide):
           - Afficher "Tri terminé!"
           - Attendre ESPACE pour retour au menu
        
        FEEDBACK ÉDUCATIF:
        - Bon tri: +50 points, message vert expliquant pourquoi
        - Mauvais tri: -10 points, message rouge expliquant où va le vrai tri
        - C'est un système d'apprentissage par essai-erreur!
        
        Args:
            dt: Delta time (secondes depuis la dernière frame)
            game_instance: Référence au jeu principal (pour score, sounds, states)
        """
        self.level_time += dt
        self.particles.update(dt)
        
        # === ARRIÈRE-PLAN: DÉGRADÉ SPATIAL ===
        # Gradient du ciel bleu vers l'espace noir
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            # Plus bas = plus sombre et plus bleu-violet
            color = (int(30 + 20 * ratio), int(30 + 15 * ratio), int(50 + 20 * ratio))
            pygame.draw.line(self.display_surface, color, (0, y), (SCREEN_WIDTH, y))
        
        # === ÉTOILES SCINTILLANTES ===
        # Chaque étoile brille avec une fréquence différente (personnalisée par sa phase 'twinkle')
        for star in self.bg_stars:
            # Onde sinusoïdale pour faire scintiller
            twinkle = 0.5 + 0.5 * math.sin(self.level_time * 2 + star['twinkle'])
            brightness = int(100 + 100 * twinkle)
            pygame.draw.circle(self.display_surface, (brightness, brightness, brightness + 20),
                             (int(star['x']), int(star['y'])), int(star['size']))

        # === PHASE 3: FEEDBACK (Affichage du résultat du dernier lancer) ===
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            
            # Message de feedback stylisé avec fond coloré
            feedback_font = pygame.font.Font(None, 42)
            msg_surf = feedback_font.render(self.feedback_msg, True, self.feedback_color)
            
            # Créer un fond transparent avec bordure
            msg_bg = pygame.Surface((msg_surf.get_width() + 40, msg_surf.get_height() + 20), pygame.SRCALPHA)
            # Couleur du fond: vert foncé si succès, rouge foncé si échec
            bg_color = (0, 100, 0, 180) if self.feedback_color[1] > 200 else (100, 0, 0, 180)
            msg_bg.fill(bg_color)
            pygame.draw.rect(msg_bg, self.feedback_color, msg_bg.get_rect(), 3, border_radius=10)
            
            # Centrer le message à l'écran
            msg_x = SCREEN_WIDTH // 2 - msg_bg.get_width() // 2
            msg_y = SCREEN_HEIGHT // 2 - 120
            self.display_surface.blit(msg_bg, (msg_x, msg_y))
            self.display_surface.blit(msg_surf, (msg_x + 20, msg_y + 10))
            
            # Quand le feedback est fini, préparer le prochain déchet
            if self.feedback_timer <= 0:
                self.current_trash.kill()
                self.spawn_next_trash()
            
            # Afficher les sprites et effets
            self.visible_sprites.draw(self.display_surface)
            self.particles.draw(self.display_surface)
            self._draw_title()
            return

        # === PHASE 4: VICTOIRE (Plus de déchets à trier) ===
        if self.current_trash is None:
            # Jouer le son de victoire une seule fois
            if not getattr(self, 'win_played', False):
                self.win_played = True
                win_sounds = [ws for ws in getattr(game_instance, 'victory_sounds', []) if ws]
                if win_sounds:
                    import random
                    random.choice(win_sounds).play()
                
                # Créer des étincelles d'or en cascade pour l'effet "Bravo!"
                for _ in range(5):
                    import random
                    self.particles.emit_sparkle(
                        random.uniform(100, SCREEN_WIDTH - 100),
                        random.uniform(100, SCREEN_HEIGHT - 200),
                        color=(255, 215, 0),
                        count=30
                    )

            # === ÉCRAN DE FIN STYLISÉ ===
            # Titre avec ombre pour donner du relief
            victory_font = pygame.font.Font(None, 72)
            txt = victory_font.render("Tri terminé !", True, (100, 255, 100))
            txt_shadow = victory_font.render("Tri terminé !", True, (0, 50, 0))
            
            # Ombre décalée (3 pixels à droite et en bas)
            self.display_surface.blit(txt_shadow, (SCREEN_WIDTH//2 - txt.get_width()//2 + 3, SCREEN_HEIGHT//2 - 50 + 3))
            self.display_surface.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//2 - 50))
            
            # Afficher le score final
            score_txt = self.font.render(f"Score final : {game_instance.score}", True, (255, 255, 255))
            self.display_surface.blit(score_txt, (SCREEN_WIDTH//2 - score_txt.get_width()//2, SCREEN_HEIGHT//2 + 20))
            
            # Instruction pulsante "Appuyez sur ESPACE"
            pulse = 0.5 + 0.5 * math.sin(self.level_time * 3)
            inst_color = (int(150 + 100 * pulse), int(150 + 100 * pulse), int(150 + 100 * pulse))
            inst_txt = pygame.font.Font(None, 36).render("Appuyez sur ESPACE pour continuer", True, inst_color)
            self.display_surface.blit(inst_txt, (SCREEN_WIDTH//2 - inst_txt.get_width()//2, SCREEN_HEIGHT//2 + 80))
            
            self.particles.draw(self.display_surface)
            
            # Attendre ESPACE puis retourner au menu
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                game_instance.change_state("menu")
            return

        # === PHASE 1/2: JEU EN COURS ===
        # HUD en haut montrant le déchet actuel
        hud_bg = pygame.Surface((400, 50), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 120))
        pygame.draw.rect(hud_bg, (255, 255, 255, 100), hud_bg.get_rect(), 2, border_radius=8)
        self.display_surface.blit(hud_bg, (SCREEN_WIDTH//2 - 200, 10))
        
        hud_txt = self.font.render(f"À trier : {self.current_trash.item_name}", True, (255, 255, 255))
        self.display_surface.blit(hud_txt, (SCREEN_WIDTH//2 - hud_txt.get_width()//2, 20))

        # === PHASE 1: VISÉE (Le joueur n'a pas encore lancé) ===
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if not self.current_trash.is_thrown:
            if mouse_pressed:
                self.aiming = True
                # Afficher la trajectoire prédictive quand souris appuyée
                self._draw_trajectory_prediction(mouse_pos)
            elif self.aiming:
                # Souris relâchée = LANCER!
                self.aiming = False
                # Calculer la vélocité en fonction de la distance souris-objet
                dx = self.current_trash.rect.centerx - mouse_pos[0]
                dy = self.current_trash.rect.centery - mouse_pos[1]
                # Scaling: 5x pour que le lancer soit assez rapide et contrôlable
                self.current_trash.velocity = pygame.Vector2(dx * 5, dy * 5)
                self.current_trash.is_thrown = True
        else:
            # === PHASE 2: VOL (Le déchet est en l'air) ===
            # Vérifier si le déchet a touché une poubelle
            hit_bins = pygame.sprite.spritecollide(self.current_trash, self.bins, False)
            if hit_bins:
                # Collision avec poubelle - vérifier si c'est la bonne!
                expected = self.get_expected_bin(self.current_trash.item_name)
                if hit_bins[0].color_name == expected:
                    # === SUCCÈS! ===
                    game_instance.score += 50
                    self.feedback_msg = SUCCESS_MESSAGES.get(expected, "Bravo !")
                    self.feedback_color = (100, 255, 100)  # Vert
                    # Effet visuel de succès: étincelles vertes
                    self.particles.emit_sparkle(
                        self.current_trash.rect.centerx,
                        self.current_trash.rect.centery,
                        color=(100, 255, 100),
                        count=25
                    )
                else:
                    # === ÉCHEC (Mauvaise poubelle) ===
                    game_instance.score = max(0, game_instance.score - 10)
                    # Récupérer le message d'apprentissage
                    self.feedback_msg = self.get_failure_message(self.current_trash.item_name)
                    self.feedback_color = (255, 100, 100)  # Rouge
                    # Effet visuel d'échec: étincelles rouges
                    self.particles.emit_sparkle(
                        self.current_trash.rect.centerx,
                        self.current_trash.rect.centery,
                        color=(255, 100, 100),
                        count=15
                    )
                
                # Arrêter le déchet et attendre le feedback
                self.current_trash.velocity = pygame.Vector2(0, 0)
                self.current_trash.gravity = 0
                self.feedback_timer = 3.0  # Afficher le résultat pendant 3 secondes
            elif self.current_trash.rect.y > SCREEN_HEIGHT or self.current_trash.rect.x < -100 or self.current_trash.rect.x > SCREEN_WIDTH + 100:
                # Le déchet est tombé hors de l'écran sans toucher - le recycler silencieusement
                self.current_trash.kill()
                self.spawn_next_trash()

        # === AFFICHAGE ===
        self.visible_sprites.update(dt)
        self.visible_sprites.draw(self.display_surface)
        self.particles.draw(self.display_surface)
        
        self._draw_title()
    
    def _draw_trajectory_prediction(self, mouse_pos):
        """Dessine l'arc de trajectoire prédictive (système d'aiming).
        
        FONCTIONNEMENT:
        1. Calculer la vélocité initiale en fonction de la distance souris-objet
        2. Simuler la trajectoire en appliquant la gravité frame par frame
        3. Afficher le chemin en semi-transparent
        
        UTILITÉ PÉDAGOGIQUE:
        - Permet au joueur de PRÉVOIR le lancer (feedback immédiat)
        - Fait comprendre la physique de la gravité (arc parabolique)
        - Rend le jeu plus précis et satisfaisant
        
        VISUELS:
        - Ligne rouge du déchet vers la souris
        - Points blancs en dégradé montrant l'arc
        """
        start_x = self.current_trash.rect.centerx
        start_y = self.current_trash.rect.centery
        
        # Calculer la vélocité initiale
        dx = start_x - mouse_pos[0]
        dy = start_y - mouse_pos[1]
        vx = dx * 5
        vy = dy * 5
        gravity = 700
        
        # === LIGNE DE VISÉE (du déchet vers la souris) ===
        pygame.draw.line(self.display_surface, (255, 100, 100, 150), 
                        (start_x, start_y), mouse_pos, 2)
        
        # === SIMULER LA TRAJECTOIRE ===
        # Recréer la physique du jeu pour afficher le chemin réel
        points = []
        sim_x, sim_y = float(start_x), float(start_y)
        sim_vx, sim_vy = vx, vy
        
        # Itérer 40 fois avec dt=0.03s pour obtenir 1.2 secondes de simulation
        for i in range(40):
            dt = 0.03
            sim_vy += gravity * dt  # Appliquer la gravité
            sim_x += sim_vx * dt    # Mettre à jour X
            sim_y += sim_vy * dt    # Mettre à jour Y
            
            # Sortir si hors écran
            if sim_y > SCREEN_HEIGHT or sim_x < 0 or sim_x > SCREEN_WIDTH:
                break
            
            points.append((int(sim_x), int(sim_y)))
        
        # === DESSINER LES POINTS DE TRAJECTOIRE ===
        # Dégradé: les points lointains sont plus transparents
        for i, point in enumerate(points):
            alpha = int(255 * (1 - i / len(points))) if points else 255
            size = max(1, 4 - i // 10)  # Les points diminuent de taille
            color = (255, 255, 255)
            
            # Dessiner un point sur 3 pour un effet pointillé (pas une ligne continue)
            if i % 3 == 0:
                pygame.draw.circle(self.display_surface, color, point, size)
    
    def _draw_title(self):
        """Anime le titre du niveau (Niveau 3: Le Grand Centre de Tri).
        
        ANIMATION 3 PHASES:
        1. ENTRÉE (0 à 0.8s): Descend du haut, apparition progressive
        2. RÉSIDENCE (0.8s à 3.2s): Reste au centre, visible complètement
        3. SORTIE (3.2s à 4.0s): Remonte vers le haut, disparition progressive
        
        VISUELS:
        - Texte blanc avec ombre noire (relief)
        - Halo vert semi-transparent (glow effect)
        - Alpha progressive pour l'apparition/disparition
        
        BUT PÉDAGOGIQUE:
        - Présenter clairement l'objectif du niveau (le tri)
        - Créer une atmosphère accueillante et ludique
        - Donner du temps au joueur pour comprendre avant de commencer
        """
        # Si l'animation est finie, ne rien afficher
        if self.level_time >= 4.0:
            return
        
        # === CALCULER LA POSITION ET L'OPACITÉ ===
        if self.level_time < 0.8:
            # PHASE 1: ENTRÉE (0 à 0.8s)
            # Interpolation linéaire: -100 → +100 en 0.8 secondes
            y_pos = -100 + (self.level_time / 0.8) * 200
            alpha = int(255 * (self.level_time / 0.8))
        elif self.level_time < 3.2:
            # PHASE 2: RÉSIDENCE (0.8s à 3.2s)
            # Rester parfaitement visible au centre
            y_pos = 100
            alpha = 255
        else:
            # PHASE 3: SORTIE (3.2s à 4.0s)
            # Interpolation inverse: +100 → -100 en 0.8 secondes
            y_pos = 100 - ((self.level_time - 3.2) / 0.8) * 200
            alpha = int(255 * (1 - (self.level_time - 3.2) / 0.8))

        # === CRÉER LES SURFACES DE TEXTE ===
        title_surf = self.title_font.render(self.title_text, True, (255, 255, 255))
        shadow_surf = self.title_font.render(self.title_text, True, (0, 0, 0))
        
        # === CRÉER L'EFFET DE GLOW (halo) ===
        # Surface plus grande que le texte avec bordure arrondie
        glow_width = title_surf.get_width() + 60
        glow_height = title_surf.get_height() + 40
        glow_surf = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
        # L'intensité du glow suit le même alpha que le texte
        glow_alpha = max(0, alpha // 4)
        pygame.draw.rect(glow_surf, (100, 200, 100, glow_alpha),
                       (0, 0, glow_width, glow_height), border_radius=15)
        
        # === AFFICHER LE GLOW (additive blending pour éclairage) ===
        glow_x = SCREEN_WIDTH // 2 - glow_width // 2
        self.display_surface.blit(glow_surf, (glow_x, y_pos - 20), special_flags=pygame.BLEND_ADD)
        
        # === APPLIQUER L'ALPHA AU TEXTE ===
        title_x = SCREEN_WIDTH // 2 - title_surf.get_width() // 2
        
        if alpha < 255:
            # Seulement pendant l'entrée et la sortie (pas au centre)
            shadow_surf.set_alpha(alpha)
            title_surf.set_alpha(alpha)
        
        # === AFFICHER LE TEXTE (ombre puis texte) ===
        # Ombre décalée (3 pixels à droite et en bas)
        self.display_surface.blit(shadow_surf, (title_x + 3, y_pos + 3))
        # Texte blanc par-dessus
        self.display_surface.blit(title_surf, (title_x, y_pos))

