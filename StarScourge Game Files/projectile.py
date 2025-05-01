from quadtree import Quadtree, Boundary, Point
from utils import SCREEN_WIDTH, SCREEN_HEIGHT
import utils
import random
import math
import pygame

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
        self.fade = 255  # For explosion fade-out

    def update(self, targets=None):
        if self.update_function:
            self.update_function(self, targets)
        else:
            self.x += self.vx
            self.y += self.vy
            self.life_timer -= 1
        if self.name == "explosion":
            # Fade out explosion alpha as it expires
            if self.life_timer > 0:
                self.fade = int(255 * (self.life_timer / self.profile["life_timer"]))
            else:
                self.fade = 0

    def draw(self, screen):
        if self.image is None:
            return  # Don't attempt to draw if image is not set
        if self.name == "shockwave":
            # Center the shockwave as it grows
            scaled_size = int(self.image.get_width() * self.scale), int(self.image.get_height() * self.scale)
            scaled_img = pygame.transform.scale(self.image, scaled_size)
            center_x = self.x + self.image.get_width() // 2
            center_y = self.y + self.image.get_height() // 2
            draw_x = center_x - scaled_img.get_width() // 2
            draw_y = center_y - scaled_img.get_height() // 2
            # Draw the image (optional, for texture)
            screen.blit(scaled_img, (draw_x, draw_y))
            # Draw a visible expanding circle overlay for the shockwave
            radius = int((self.image.get_width() * self.scale) / 2)
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (0, 200, 255, 90), (radius, radius), radius)
            pygame.draw.circle(surf, (255, 255, 255, 120), (radius, radius), max(1, radius - 8), 4)
            screen.blit(surf, (center_x - radius, center_y - radius))
        elif self.name == "explosion":
            # Fade out explosion
            img = self.image.copy()
            img.set_alpha(self.fade)
            screen.blit(img, (self.x, self.y))
        else:
            screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        if self.name == "shockwave":
            scaled_size = int(self.image.get_width() * self.scale), int(self.image.get_height() * self.scale)
            center_x = self.x + self.image.get_width() // 2
            center_y = self.y + self.image.get_height() // 2
            draw_x = center_x - scaled_size[0] // 2
            draw_y = center_y - scaled_size[1] // 2
            return pygame.Rect(draw_x, draw_y, scaled_size[0], scaled_size[1])
        else:
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
        x = self.source.x + self.source.width // 2
        width = self.beam_image.get_width()
        # Start at y = -100, height = SCREEN_HEIGHT + 200 (to cover the whole screen and 100px above)
        return pygame.Rect(x - width // 2, 0, width, SCREEN_HEIGHT + 200)

    def get_segment_rects(self):
        # Returns a list of rects for each beam segment as drawn
        rects = []
        time_now = pygame.time.get_ticks()
        vibration = int(2 * math.sin(time_now * 0.09 + self.stack_index))
        x = self.source.x + self.source.width // 2 + vibration
        vertical_offset = self.stack_index * 6
        base_y = self.source.y - vertical_offset
        width = self.beam_image.get_width()
        height = self.beam_image.get_height()
        # Draw segments upward from the player's y position
        start_y = base_y - 128
        end_y = -128  # adjust if needed to reach the top of the screen
        for y in range(start_y, end_y, -height):
            rect = pygame.Rect(x - width // 2, y, width, height)
            rects.append(rect)
        return rects

    def expired(self):
        return self.beam_lifetime <= 0

def projectiles_frame_update(projectiles, targets=None):
    for projectile in projectiles[:]:  # Iterate over a copy for safe removal
        projectile.update(targets)
        if projectile.expired():
            projectiles.remove(projectile)
            if projectile.sub_proj:
                projectile.sub_proj.x = projectile.x
                projectile.sub_proj.y = projectile.y
                projectile.sub_proj.angle = projectile.angle
                projectiles.append(projectile.sub_proj)

def beams_frame_update(beams, targets=None):
    for beam in beams[:]:  # Iterate over a copy for safe removal
        beam.update(targets)
        if beam.expired():
            beams.remove(beam)
            # if beam.sub_proj:
            #     beam.sub_proj.x = beam.x
            #     beam.sub_proj.y = beam.y
            #     beam.sub_proj.angle = beam.angle
            #     beams.append(beam.sub_proj)