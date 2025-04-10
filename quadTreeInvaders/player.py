from quadtree import Quadtree, Boundary, Point
import utils
from utils import SCREEN_WIDTH, SCREEN_HEIGHT
import weapons
from weapons import WEAPON_TYPES
from projectile import projectiles_frame_update, beams_frame_update
import random
import pygame

class Player:
    def __init__(self, x, y, assets):
        self.x, self.y = x, y
        self.frame = 0
        self.timer = 0
        self.inv_frames = 10
        self.fps = 8
        self.images = assets["player"]
        self.image = self.images[0]
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.assets = assets
        self.projectiles = []
        self.beams = []
        self.speed = 10
        profiles = weapons.profiles(assets)
        self.weapons = [weapons.machine_gun(profiles), weapons.homing_missile(profiles), weapons.shockwave(profiles), weapons.laser(profiles)]
        self.hull = 3


    def move(self, dx):
        self.x += dx
        self.x = max(0, min(800 - self.width, self.x))

    def update(self, targets=None):
        self.timer += 1
        self.inv_frames -= 1
        for weapon in self.weapons:
            weapon.update()
        projectiles_frame_update(self.projectiles, targets)
        beams_frame_update(self.beams, targets)

        if self.timer >= 60 // self.fps:
            self.frame = (self.frame + 1) % len(self.images)
            self.image = self.images[self.frame]
            self.timer = 0

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        for projectile in self.projectiles:
            projectile.draw(screen)
        for beam in self.beams:
            beam.draw(screen, self)
        for weapon in self.weapons:
            weapon.screen_effect(screen)

    def get_hitbox(self):
        # Create a 50x50 hitbox centered on the player's sprite.
        hitbox_width = 50
        hitbox_height = 50
        hitbox_x = self.x + (self.width - hitbox_width) // 2
        hitbox_y = self.y + (self.height - hitbox_height) // 2
        return pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)

    def on_hit(self, objects):
        self.projectiles.append(Explosion(player.x, player.y, self.assets["shipExplosion"], duration=30))
        self.assets["playerDeath"].play()  # Play player death sound
        pass

    def player_collision_check(self, objects, game_state):
        # --- Collision Detection for Player (Unified via Quadtree) ---
        # Create a quadtree covering the whole screen
            collision_qtree = Quadtree(Boundary(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)
            # Insert enemies and enemy bullets (with a type tag)
            for obj in objects:
                collision_qtree.insert(Point(obj.x, obj.y, ("name", obj.name)))

            # Query the quadtree using the player's hitbox
            player_hitbox = self.get_hitbox()
            collision_candidates = []
            collision_qtree.query(Boundary(player_hitbox.centerx, player_hitbox.centery, player_hitbox.width//2, player_hitbox.height//2), collision_candidates)
            if len(collision_candidates) > 0 and self.inv_frames <= 0:
                self.on_hit(objects)
                self.inv_frames = 10
            if self.hull <= 0: 
                game_state.game_over = True

    def game_events(self, events):
        # --- Player Input Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print(game_state.game_over)
                game_state.game_quit = True
                game_state.game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.weapons[0].trigger(self.x + self.width//2, self.y, 270, self.projectiles)
                elif event.key == pygame.K_w:
                    self.weapons[1].trigger(self.x + self.width//2, self.y, 270, self.projectiles)
                elif event.key == pygame.K_e:
                    self.weapons[2].trigger(self.x + self.width//2, self.y, 0, self.projectiles)
                elif event.key == pygame.K_r:
                    self.weapons[3].trigger(self.x + self.width//2, self.y, 0, self.beams)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.move(-10)
        if keys[pygame.K_RIGHT]:
            self.move(10)
