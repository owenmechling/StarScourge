# powerups.py
# Basic powerup system scaffold for StarScourge

class PowerupProfiles:
    """Container for all powerup profile data, similar to weapons.profiles."""
    def __init__(self):
        self.PIERCING = {
            "name": "piercing",
            "description": "Bullets and rockets pierce through enemies.",
            "duration": 600,  # frames (10 seconds at 60 FPS)
        }
        # Add more powerup profiles here as needed

class Powerup:
    def __init__(self, profile):
        self.name = profile["name"]
        self.description = profile.get("description", "")
        self.duration = profile.get("duration", 600)
        self.active = False

    def activate(self, player):
        self.active = True
        # Apply effect to player (to be implemented)

    def deactivate(self, player):
        self.active = False
        # Remove effect from player (to be implemented)

    def update(self, player):
        if self.active:
            self.duration -= 1
            if self.duration <= 0:
                self.deactivate(player)

# Usage example (not run here):
# profiles = PowerupProfiles()
# piercing_powerup = Powerup(profiles.PIERCING)
