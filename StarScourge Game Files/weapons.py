import pygame
import projectile
from projectile import Projectile, Beam
import utils
import math 
import random

WEAPON_TYPES = {
    "projectile": "projectile",
    "beam": "beam"
}

class profiles:
    def __init__(self, assets):
        self.EXPLOSION = {
            "name": "explosion",
            # Will be set dynamically on use
            "image": None,
            "damage": 0,
            "scale": 1,
            "speed": 0,
            "hit_radius": 0,
            "angle": 0,
            "angle_variance": 15,
            "life_timer": 30,
            "sub_proj": None
        }

        self.HOMING_MISSILE = {
            "name": "missile",
            "image": assets["rocket"],
            "sound": assets["rocketLaunch"],
            "damage": 25,
            "scale": 1,
            "speed": 3,
            "hit_radius": 32,
            "angle": 0,
            "angle_variance": 15,
            "life_timer": 200,
            "sub_proj": self.EXPLOSION,
            "piercing": False  # No piercing by default
        }
        self.SHOCKWAVE = {
            "name": "shockwave",
            "image": assets["shockwave"],
            "base_image": assets["shockwave"],
            "sound": assets["shockwaveSound"],
            "damage": 100,
            "scale": 1,
            "scaling": 1.1,
            "speed": 0,
            "hit_radius": 64,
            "angle": 0,
            "life_timer": 200,
            "sub_proj": None,
            "piercing": True  # Always piercing
        }
        self.BULLET = {
            "name": "bullet",
            "image": assets["bullet"],
            "sound": assets["basicAttack"],
            "damage": 5,
            "scale": 1,
            "speed": 5,
            "hit_radius": 32,
            "angle": 0,
            "angle_variance": 15,
            "life_timer": 200,
            "sub_proj": None,
            "piercing": False  # No piercing by default
        }
        self.LASER = {
            "name": "laser",
            "windup_image": "",
            "windup_time": 60,
            "base_image": assets["laserBase"],
            "beam_image": assets["laserBeam"],
            "beam_lifetime": 300,
            "beam_cooldown": 60,
            "sound": assets["laserSound"],
            "damage": 20,
            "scale": 1,
            "hit_radius": 32,
            "max_radius": 100,
            "angle": 0,
            "sub_proj": None
        }

class homing_missile:
    def __init__(self, profiles, ammo=10000, cooldown=5):
        self.type = WEAPON_TYPES["projectile"]
        self.ammo = ammo
        self.last_fire_time = 0
        self.profile = profiles.HOMING_MISSILE
        self.cooldown = cooldown

    def trigger(self, x, y, angle, projectiles, game_state=None):
        if self.ammo > 0 and self.cooldown < 1: 
            explosion = Projectile(x-self.profile["image"].get_width()// 2, y, angle, self.profile["sub_proj"])
            #projectiles.append(Projectile(x-self.profile["image"].get_width()// 2, y, angle, self.profile, update_fuction=self.projectile_update_function))
            #projectiles.append(Projectile(x-self.profile["image"].get_width()// 2, y, angle+5, self.profile, update_fuction=self.projectile_update_function))
            projectiles.append(Projectile(x-self.profile["image"].get_width()// 2, y, angle-5, self.profile, update_fuction=self.projectile_update_function))
            if game_state is not None:
                self.profile["sound"].set_volume(game_state.sfx_volume)
            self.profile["sound"].play()
            self.ammo -= 1
            self.cooldown = 10

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def projectile_update_function(self, projectile, targets):
        # Decrease the life timer
        projectile.life_timer -= 1
        if projectile.life_timer <= 0:
            return  # Skip further updates if time is up

        # Acquire a target if we don't have one
        if projectile.target is None and targets:
            projectile.target = min(targets, key=lambda e: (projectile.x - (e.x + e.image.get_width()/2))**2 + (projectile.y - (e.y + e.image.get_height()/2))**2)
        
        if projectile.target:
            # Compute the desired angle towards the target enemy's center
            target_center_x = projectile.target.x + projectile.target.image.get_width() / 2
            target_center_y = projectile.target.y + projectile.target.image.get_height() / 2
            dx = target_center_x - projectile.x
            dy = target_center_y - projectile.y
            desired_angle = math.degrees(math.atan2(dy, dx))
            # Calculate the smallest angle difference
            angle_diff = (desired_angle - projectile.angle + 180) % 360 - 180
            # Limit the change by the turn rate
            if angle_diff > projectile.turn_rate:
                angle_diff = projectile.turn_rate
            elif angle_diff < -projectile.turn_rate:
                angle_diff = -projectile.turn_rate
            # Update the rocket's angle with some random variation for a wobbly effect
            projectile.angle += angle_diff + random.uniform(-1, 1)
        # Optional alternative: Prevent downward movement (if vy > 0, set it to 0)
        rad = math.radians(projectile.angle)
        vx = projectile.speed * math.cos(rad)
        vy = projectile.speed * math.sin(rad)
        projectile.x += vx
        projectile.y += vy

    def screen_effect(self, screen):
        return

    def draw(self, screen):
        for projectile in self.projectiles:
            projectile.draw(screen)
    
    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))

    def hud_text(self):
        return f": {self.ammo}"

class shockwave:
    def __init__(self, profiles, cooldown=60):
        self.type = WEAPON_TYPES["projectile"]
        self.cooldown = cooldown
        self.last_shot = 0  # Allow immediate firing on game start
        self.profile = profiles.SHOCKWAVE.copy()
        self.radius = 0
        # Dramatic shockwave: bigger, longer, slower
        self.profile["scale"] = 2.0  # Start at double size
        self.profile["scaling"] = 1.07  # Expand even slower
        self.profile["life_timer"] = 80  # Last longer
        self.max_radius = 250  # Hitbox expands to 250px

    def trigger(self, player, angle, projectiles, game_state=None):
        if self.last_shot < 1:
            # Center top of player image
            x = player.x + player.image.get_width() // 2 - self.profile["image"].get_width() // 2
            y = player.y + player.image.get_height() // 2 - self.profile["image"].get_height() // 2
            if game_state is not None:
                self.profile["sound"].set_volume(game_state.sfx_volume)
            self.profile["sound"].play()
            # Create the shockwave projectile with initial scale so it starts at player size
            shockwave_proj = Projectile(x, y, angle, self.profile, update_fuction=self.projectile_update_function)
            shockwave_proj.scale = self.profile["scale"]
            projectiles.append(shockwave_proj)
            self.last_shot = self.cooldown

    def update(self):
        if self.last_shot > 0:
            self.last_shot -= 1

    def projectile_update_function(self, projectile, targets=None):
        # Make the shockwave expand to a larger radius, then expire
        if not hasattr(projectile, "radius"):
            projectile.radius = (projectile.image.get_width() * projectile.scale) / 2
        max_radius = getattr(self, "max_radius", 250)
        if projectile.radius < max_radius:
            # Expand the shockwave smoothly
            projectile.scale *= self.profile["scaling"]
            projectile.radius = (projectile.image.get_width() * projectile.scale) / 2
        else:
            projectile.life_timer = 0  # Expire the projectile
        projectile.life_timer -= 1

    def hud_text(self):
        # Show the actual cooldown remaining, or READY
        if self.last_shot > 0:
            return f" Cooldown: {int(self.last_shot)}"
        else:
            return ": READY"

    def screen_effect(self, screen):
        return

class machine_gun:
    def __init__(self, profiles, ammo=10000, cooldown=5):
        self.type = WEAPON_TYPES["projectile"]
        self.ammo = ammo
        self.profile = profiles.BULLET
        self.cooldown = cooldown
        self.last_shot = cooldown

    def trigger(self, x, y, angle, projectiles, game_state=None):
        if self.ammo > 0 and self.last_shot < 1: 
            if game_state is not None:
                self.profile["sound"].set_volume(game_state.sfx_volume)
            self.profile["sound"].play()
            projectiles.append(Projectile(x-self.profile["image"].get_width()// 2, y, angle, self.profile, update_fuction=self.projectile_update_function))
            self.ammo -= 1
            self.last_shot = self.cooldown

    def update(self):
        if self.last_shot > 0:
            self.last_shot -= 1

    def projectile_update_function(self, projectile, targets=None):
        projectile.x += projectile.vx
        projectile.y += projectile.vy
        projectile.life_timer -= 1

    def screen_effect(self, screen):
        return

    def hud_text(self):
        return f": {self.ammo}"

class laser:
    def __init__(self, profiles):
        self.profile = profiles.LASER
        self.type = WEAPON_TYPES["beam"]
        self.cooldown = 60

    def trigger(self, source, angle, beams, game_state=None):
        if self.cooldown < 1: 
            if game_state is not None:
                self.profile["sound"].set_volume(game_state.sfx_volume)
            beams.append(Beam(source, angle, self.profile, draw_function=self.beam_draw_function))
            self.profile["sound"].play()
            self.cooldown = self.profile["windup_time"]+self.profile["beam_lifetime"]+self.profile["beam_cooldown"]

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
      
    def beam_draw_function(self, beam, screen, source):
        if beam.windup_time > 0:
            # Draw the windup effect
            progress = 1 - (beam.windup_time / beam.windup_const)
            radius = int(beam.profile["max_radius"] * progress)
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (0, 255, 255, 100), (radius, radius), radius)
            screen.blit(surf, (beam.x - radius, beam.y - radius))
        elif beam.beam_lifetime > 0:
            # vibration effect based on time; tweak amplitude/frequency
            time_now = pygame.time.get_ticks()
            vibration = int(2 * math.sin(time_now * 0.09 + beam.stack_index))

            x = source.x + 32 + vibration # shoot the beam from the center of the ship, which is 64x64 as are all
            vertical_offset = beam.stack_index * 6 # Calculate vertical offset for stacking
            
            # Draw the base image at the player's top, applying the vertical offset.
            base_rect = beam.base_image.get_rect(midbottom=(x, source.y - vertical_offset))
            screen.blit(beam.base_image, base_rect)
            # Draw the beam segments upward from the p layer's y position.
            start_y = source.y - 128
            end_y = -128  # adjust if needed to reach the top of the screen
            beam_height = beam.beam_image.get_height()
            for y in range(start_y, end_y, -beam_height):
                beam_rect = beam.beam_image.get_rect(midtop=(x, y))
                screen.blit(beam.beam_image, beam_rect)
       
    def screen_effect(self, screen):
        #flash_timer = 5
        return

    def hud_text(self):
        if self.cooldown > 0:
            return f"Cooldown: {int(self.cooldown)}"
        else:
            return "READY"


