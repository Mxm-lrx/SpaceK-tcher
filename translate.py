import os

replacements = {
    "# Scale image to fit decently inside hands/screen": "# Redimensionner l'image pour qu'elle s'ajuste correctement dans les mains/à l'écran",
    "# We need a small label or just image, let's just use image": "# Nous avons besoin d'une petite étiquette ou juste d'une image, utilisons simplement l'image",
    "# List of tuples: (item_name, surface_image)": "# Liste de tuples : (nom_objet, image_surface)",
    "# Scale initial velocity": "# Mise à l'échelle de la vélocité initiale",
    "# Spawn au-dessus (Top)": "# Apparition au-dessus (Haut)",
    "# Spawn sur les cotes (Left / Right)": "# Apparition sur les côtés (Gauche / Droite)",
    "# Spawn en-dessous (Bottom)": "# Apparition en-dessous (Bas)",
    "# Clean obstacles that are too far away (notablly too far below since rocket goes up)": "# Nettoie les obstacles trop éloignés (notamment trop bas puisque la fusée monte)",
    "# update HUD with game_instance score": "# Met à jour le HUD avec le score",
    "# spawn majoritairement au-dessus car la fusée monte (65%)": "# Apparition majoritairement au-dessus car la fusée monte (65%)",
    "# Fix spawn bounds to be completely out of camera view and fix collected_trash append to save tuple with image": "# Corrige les limites d'apparition pour qu'elles soient complètement hors de vue et corrige l'ajout des déchets pour sauvegarder le tuple",
    "# Spawn bounds fix": "# Correction des limites d'apparition",
    "# force spawn outside of screen bounds": "# Force l'apparition en dehors des limites de l'écran",
    "# Spawn left or right": "# Apparition à gauche ou à droite",
    "# Spawn top or bottom": "# Apparition en haut ou en bas",
    "# collected trash append fix": "# Correction de l'ajout des déchets collectés",
    "# Adjust scaling for Debris and Dechet specifically, overriding base FloatingObstacle sizes": "# Ajuste l'échelle spécifiquement pour les Débris et Déchets, remplaçant les tailles de base",
    "# Scale image to fit decently inside hands/screen": "# Redimensionner l'image pour qu'elle s'ajuste correctement"
}

for root, dirs, files in os.walk('.'):
    for fn in files:
        if fn.endswith('.py') and fn != 'translate.py':
            fp = os.path.join(root, fn)
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
            original_content = content
            for en, fr in replacements.items():
                content = content.replace(en, fr)
            if content != original_content:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Updated {fp}')
print("Done")