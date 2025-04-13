
import pygame
import random
import math

class Player:
    def __init__(self, x, y, images):
        self.x, self.y = x, y
        self.images = images
        self.frame = 0
        self.timer = 0
        self.fps = 8
        self.image = self.images[0]
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def move(self, dx):
        self.x += dx
        self.x = max(0, min(800 - self.width, self.x))

    def update(self):
        self.timer += 1
        if self.timer >= 60 // self.fps:
            self.frame = (self.frame + 1) % len(self.images)
            self.image = self.images[self.frame]
            self.timer = 0

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def get_hitbox(self):
        # Create a 50x50 hitbox centered on the player's sprite.
        hitbox_width = 50
        hitbox_height = 50
        hitbox_x = self.x + (self.width - hitbox_width) // 2
        hitbox_y = self.y + (self.height - hitbox_height) // 2
        return pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)

class Enemy:
    def __init__(self, x, y, image, type_id):
        self.x, self.y = x, y
        self.image = image
        self.type_id = type_id

        # Set speed and shooting interval based on type:
        if self.type_id == 0:
            # Medium speed, shoots at random intervals
            self.speed = 2.0
            self.shoot_interval = random.randint(120, 240)  # in frames (2-4 seconds at 60 FPS)
        elif self.type_id == 1:
            # Fast, does not shoot
            self.speed = 3.5
            self.shoot_interval = None
        elif self.type_id == 2:
            # Slow, shoots often
            self.speed = 1.0
            self.shoot_interval = random.randint(60, 120)  # more frequent shooting

        self.shoot_timer = self.shoot_interval if self.shoot_interval is not None else None

    def update(self):
        self.y += self.speed
        if self.shoot_timer is not None:
            self.shoot_timer -= 1

    def try_shoot(self, enemy_bullet_image, player=None):
        if self.shoot_timer is not None and self.shoot_timer <= 0:
            # Reset timer based on type
            if self.type_id == 0:
                self.shoot_interval = random.randint(120, 240)
            elif self.type_id == 2:
                self.shoot_interval = random.randint(60, 120)
            self.shoot_timer = self.shoot_interval

            # Spawn a bullet from the center bottom of the enemy sprite
            bullet_x = self.x + self.image.get_width() // 2
            bullet_y = self.y + self.image.get_height()

            if self.type_id == 0:
                # Enemy0 shoots straight down (90°)
                angle = 90
            elif self.type_id == 2:
                if player is not None:
                    # Calculate angle from enemy center to player center
                    enemy_center_x = self.x + self.image.get_width() // 2
                    enemy_center_y = self.y + self.image.get_height() // 2
                    player_center_x = player.x + player.width // 2
                    player_center_y = player.y + player.height // 2
                    dx = player_center_x - enemy_center_x
                    dy = player_center_y - enemy_center_y
                    angle = math.degrees(math.atan2(dy, dx))
                else:
                    # Fallback if no player provided
                    angle = random.randint(60, 120)
            return EnemyBullet(bullet_x, bullet_y, enemy_bullet_image, angle)
        return None

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))
    
class EnemyBullet:
    def __init__(self, x, y, image, angle=90):
        self.x = x
        self.y = y
        self.image = image
        speed = 5  # adjust bullet speed as needed
        rad = math.radians(angle)
        self.vx = speed * math.cos(rad)
        self.vy = speed * math.sin(rad)

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        bullet_width, bullet_height = 20, 20  # adjust as needed
        return pygame.Rect(self.x, self.y, bullet_width, bullet_height)

class Bullet:
    def __init__(self, x, y, image):
        self.x, self.y = x, y
        self.image = image
        self.speed = 10

    def update(self):
        self.y -= self.speed

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))
""" old rocket class
class Rocket:
    def __init__(self, x, y, image):
        self.x, self.y = x, y
        self.image = image
        self.speed = 5

    def update(self):
        self.y -= self.speed

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))
"""
class Rocket:
    def __init__(self, x, y, image, target=None):
        self.x = x
        self.y = y
        self.image = image
        self.speed = 5
        self.target = target  # The enemy this rocket is homing in on
        self.angle = -90     # Initial angle (in degrees) going upward
        self.turn_rate = 3   # Maximum change in degrees per update
        self.life_timer = 180  # Rocket will self-destruct after 180 frames (3 seconds at 60FPS)
        self.exploded = False

    def update(self, enemies):
        # Decrease the life timer
        self.life_timer -= 1
        if self.life_timer <= 0:
            self.exploded = True
            return  # Skip further updates if time is up

        # Acquire a target if we don't have one
        if self.target is None and enemies:
            self.target = min(enemies, key=lambda e: (self.x - (e.x + e.image.get_width()/2))**2 + (self.y - (e.y + e.image.get_height()/2))**2)
        
        if self.target:
            # Compute the desired angle towards the target enemy's center
            target_center_x = self.target.x + self.target.image.get_width() / 2
            target_center_y = self.target.y + self.target.image.get_height() / 2
            dx = target_center_x - self.x
            dy = target_center_y - self.y
            desired_angle = math.degrees(math.atan2(dy, dx))
            
            # Calculate the smallest angle difference
            angle_diff = (desired_angle - self.angle + 180) % 360 - 180
            # Limit the change by the turn rate
            if angle_diff > self.turn_rate:
                angle_diff = self.turn_rate
            elif angle_diff < -self.turn_rate:
                angle_diff = -self.turn_rate
            
            # Update the rocket's angle with some random variation for a wobbly effect
            self.angle += angle_diff + random.uniform(-1, 1)
        
        # Optional alternative: Prevent downward movement (if vy > 0, set it to 0)
        rad = math.radians(self.angle)
        vx = self.speed * math.cos(rad)
        vy = self.speed * math.sin(rad)
        if vy > 0:
            vy = 0  # Do not allow downward movement

        self.x += vx
        self.y += vy
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
    
    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))

class Shockwave:
    def __init__(self, x, y, image):
        self.x, self.y = x, y
        self.image = image
        self.radius = 0
        self.max_radius = 100
        self.duration = 60

    def update(self):
        self.radius += 3
        self.duration -= 1

    def draw(self, screen):
        if self.duration > 0:
            scaled = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
            rect = scaled.get_rect(center=(self.x, self.y))
            screen.blit(scaled, rect)

    def get_rect(self):
        # Simple bounding box around the shockwave
        return pygame.Rect(
            self.x - self.radius, 
            self.y - self.radius, 
            self.radius * 2, 
            self.radius * 2
        )

class LaserWindup:
    def __init__(self, player, image):
        self.player = player
        self.image = image
        self.duration = 60
        self.max_radius = 100

    def update(self):
        self.x = self.player.x + self.player.width // 2
        self.y = self.player.y
        self.duration -= 1

    def draw(self, screen):
        progress = 1 - (self.duration / 60)
        radius = int(self.max_radius * progress)
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 255, 255, 100), (radius, radius), radius)
        screen.blit(surf, (self.x - radius, self.y - radius))

class LaserBeam:
    def __init__(self, player, base_image, beam_image, stack_index=0):
        self.player = player
        self.base_image = base_image
        self.beam_image = beam_image
        self.duration = 300
        self.stack_index = stack_index  # used for stacking offset

    def update(self):
        self.duration -= 1

    def draw(self, screen):
        # Get the player's horizontal center
        base_x = self.player.x + self.player.width // 2

        # vibration effect based on time; tweak amplitude/frequency
        time_now = pygame.time.get_ticks()
        vibration = int(2 * math.sin(time_now * 0.09 + self.stack_index))
        x = base_x + vibration

        # Calculate vertical offset for stacking
        vertical_offset = self.stack_index * 6

        # Draw the base image at the player's top, applying the vertical offset.
        base_rect = self.base_image.get_rect(midbottom=(x, self.player.y - vertical_offset))
        screen.blit(self.base_image, base_rect)

        # Draw the beam segments upward from the player's y position.
        start_y = self.player.y - 128
        end_y = -128  # adjust if needed to reach the top of the screen
        beam_height = self.beam_image.get_height()

        for y in range(start_y, end_y, -beam_height):
            beam_rect = self.beam_image.get_rect(midtop=(x, y))
            screen.blit(self.beam_image, beam_rect)

    def get_rect(self):
        x = self.player.x + self.player.width // 2
        width = self.beam_image.get_width()
        return pygame.Rect(x - width // 2, 0, width, 600)


class Explosion:
    def __init__(self, x, y, image, duration=30):
        self.x = x
        self.y = y
        self.image = image
        self.duration = duration  # Duration in frames

    def update(self):
        self.duration -= 1

    def draw(self, screen):
        # You could also add scaling or animation here if desired.
        screen.blit(self.image, (self.x, self.y))

    def is_finished(self):
        return self.duration <= 0

