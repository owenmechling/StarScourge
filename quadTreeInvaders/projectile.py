from quadtree import Quadtree, Boundary, Point
from utils import SCREEN_WIDTH, SCREEN_HEIGHT
import utils
import random
import math

class Projectile:
    def __init__(self, x, y, angle, profile, sub_proj=None, update_fuction=None, friendly=True):
        self.x, self.y = x, y
        self.name = profile["name"]
        self.image = profile["image"]
        self.speed = profile["speed"]
        self.hit_radius = profile["hit_radius"]
        self.damage = profile["damage"]
        self.angle = angle
        rad = math.radians(angle)
        self.vx = self.speed * math.cos(rad)
        self.vy = self.speed * math.sin(rad)
        # self.turn_rate = turn_rate
        self.update_function = update_fuction 
        self.life_timer = profile["life_timer"]
        self.scale = profile["scale"]
        self.profile = profile
        self.sub_proj = sub_proj
        self.friendly = friendly
        self.target = None
        self.turn_rate = 0

    def update(self, targets=None):
        if self.update_function:
            self.update_function(self, targets)
        else:
            self.x += self.vx
            self.y += self.vy
            self.life_timer -= 1

    def draw(self, screen):
        screen.blit(self.image, (self.x*self.scale, self.y*self.scale))

    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))

    def expired(self):
        return self.life_timer <= 0

class Beam:
    def __init__(self, source, angle, profile, stack_index=0, sub_effect=None, update_fuction=None, draw_function=None, friendly=True):
        self.source = source
        self.angle = angle
        self.stack_index = stack_index
        self.name = profile["name"]
        self.windup_image = profile["windup_image"]
        self.windup_time = profile["windup_time"]
        self.windup_const = profile["windup_time"]
        self.beam_lifetime = profile["beam_lifetime"]
        self.base_image = profile["base_image"]
        self.beam_image = profile["beam_image"]
        self.hit_radius = profile["hit_radius"]
        self.damage = profile["damage"]
        rad = math.radians(angle)
        # self.turn_rate = turn_rate
        self.update_function = update_fuction 
        self.draw_function = draw_function
        self.profile = profile
        self.sub_effect = sub_effect
        self.friendly = friendly

    def update(self, targets=None):
        if self.update_function:
            self.update_function(self, targets)
        else:
            self.x = self.source.x + self.source.width // 2
            self.y = self.source.y
            if self.windup_time > 0:
                self.windup_time -= 1
            elif self.beam_lifetime > 0:
                self.beam_lifetime -= 1

    def draw(self, beam, screen, source):
        if self.draw_function:
            self.draw_function(beam, screen, source)
        else:
            if self.windup_time > 0:
                # Draw the windup effect
                progress = 1 - (self.windup_time / self.windup_const)
                radius = int(self.profile["max_radius"] * progress)
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (0, 255, 255, 100), (radius, radius), radius)
                screen.blit(surf, (self.x - radius, self.y - radius))
            elif self.beam_lifetime > 0:
                # vibration effect based on time; tweak amplitude/frequency
                time_now = pygame.time.get_ticks()
                vibration = int(2 * math.sin(time_now * 0.09 + self.stack_index))
                x = self.x + vibration
                # Calculate vertical offset for stacking
                vertical_offset = self.stack_index * 6
                # Draw the base image at the player's top, applying the vertical offset.
                base_rect = self.base_image.get_rect(midbottom=(x, self.y - vertical_offset))
                screen.blit(self.base_image, base_rect)
                # Draw the beam segments upward from the player's y position.
                start_y = self.x - 128
                end_y = -128  # adjust if needed to reach the top of the screen
                beam_height = self.beam_image.get_height()
                for y in range(start_y, end_y, -beam_height):
                    beam_rect = self.beam_image.get_rect(midtop=(x, y))
                    screen.blit(self.beam_image, beam_rect)

    def get_rect(self):
        x = self.player.x + self.player.width // 2
        width = self.beam_image.get_width()
        return pygame.Rect(x - width // 2, 0, width, 600)

    def expired(self):
        return self.beam_lifetime <= 0

def projectiles_frame_update(projectiles, targets=None):
    for projectile in projectiles:
        projectile.update(targets)
        if projectile.expired():
            projectiles.remove(projectile)
            if projectile.sub_proj:
                sub_proj.x = projectile.x
                sub_proj.y = projectile.y
                sub_proj.angle = projectile.angle
                projectiles.append(sub_proj)

def beams_frame_update(beams, targets=None):
    for beam in beams:
        beam.update(targets)
        if beam.expired():
            beams.remove(beam)
            # if beam.sub_proj:
            #     sub_proj.x = beam.x
            #     sub_proj.y = beam.y
            #     sub_proj.angle = beam.angle
            #     beams.append(sub_proj)