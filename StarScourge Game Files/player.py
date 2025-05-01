from quadtree import Quadtree, Boundary, Point
import utils
from utils import SCREEN_WIDTH, SCREEN_HEIGHT, GameState
import weapons
from weapons import WEAPON_TYPES, profiles 
import projectile
from projectile import projectiles_frame_update, beams_frame_update, Projectile 
import random
import pygame
import math

class Player:
    def __init__(self, x, y, assets, fx_manager, profiles):
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
        self.profiles = profiles  # Use the passed-in profiles object
        # Set MG ammo to 200, rockets to 20, shockwave cooldown to 300 (5s), laser beam_cooldown to 600 (10s)
        mg_ammo = 200
        rocket_ammo = 20
        shockwave_cooldown = 300  # 5 seconds at 60 FPS
        laser_beam_cooldown = 600 # 10 seconds at 60 FPS
        # Patch the profiles for cooldowns
        self.profiles.LASER["beam_cooldown"] = laser_beam_cooldown
        self.weapons = [
            weapons.machine_gun(self.profiles, ammo=mg_ammo),
            weapons.homing_missile(self.profiles, ammo=rocket_ammo),
            weapons.shockwave(self.profiles, cooldown=shockwave_cooldown),
            weapons.laser(self.profiles)
        ]
        self.hull = 10 # Player Health
        self.fx = fx_manager
        self.shields = 3  # Player shield counters 
        self.max_shields = 3
        self.shield_recharge_progress = [5.0 for _ in range(self.max_shields)]  # 5 seconds per shield
        self.shield_recharge_time = 5.0  # seconds per shield
        self.shield_recharge_cooldown = 0.0  # time left before recharge resumes
        self.reflector_charge = 100.0  # Percent, 0-100
        self.reflector_active = False
        self.reflector_drain_rate = 100.0 / 3.0  # % per second (drain in 3s)
        self.reflector_recharge_rate = self.reflector_drain_rate / 2  # recharge is half as fast
        self.reflector_fx_timer = 0  # For FXManager vibration

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

        # Reflector charge logic
        dt = 1/60  # Assume 60 FPS for now
        if self.reflector_active and self.reflector_charge > 0:
            self.reflector_charge -= self.reflector_drain_rate * dt
            if self.reflector_charge < 0:
                self.reflector_charge = 0
                self.reflector_active = False
        elif not self.reflector_active and self.reflector_charge < 100:
            self.reflector_charge += self.reflector_recharge_rate * dt
            if self.reflector_charge > 100:
                self.reflector_charge = 100

        # Shield recharge logic
        if self.shields < self.max_shields:
            if self.shield_recharge_cooldown > 0:
                self.shield_recharge_cooldown -= dt
            else:
                # Recharge the lowest shield first
                for i in range(self.max_shields-1, -1, -1):
                    if self.shield_recharge_progress[i] < self.shield_recharge_time:
                        self.shield_recharge_progress[i] += dt
                        if self.shield_recharge_progress[i] >= self.shield_recharge_time:
                            self.shield_recharge_progress[i] = self.shield_recharge_time
                            self.shields += 1
                        break

        if self.timer >= 60 // self.fps:
            self.frame = (self.frame + 1) % len(self.images)
            self.image = self.images[self.frame]
            self.timer = 0

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        for projectile in self.projectiles:
            projectile.draw(screen)
        for beam in self.beams:
            beam.draw(beam, screen, self)
        for weapon in self.weapons:
            weapon.screen_effect(screen)

        # Draw reflector FX
        if self.reflector_active and self.reflector_charge > 0:
            px, py = self.x + self.width//2, self.y + self.height//2
            radius = 60 + random.randint(-4, 4)
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,140,0, 120), (radius, radius), radius)
            screen.blit(surf, (px-radius, py-radius))

    def get_hitbox(self):
        # Create a 50x50 hitbox centered on the player's sprite.
        hitbox_width = 50
        hitbox_height = 50
        hitbox_x = self.x + (self.width - hitbox_width) // 2
        hitbox_y = self.y + (self.height - hitbox_height) // 2
        return pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)

    def on_hit(self, objects, game_state=None):
        explosion_profile = dict(self.profiles.EXPLOSION)
        explosion_profile["image"] = self.assets["shipExplosion"]
        self.projectiles.append(Projectile(self.x, self.y, 0, explosion_profile))
        if game_state is not None:
            ch = pygame.mixer.find_channel(5)
            if ch:
                ch.set_volume(game_state.sfx_volume)
                ch.play(self.assets["playerDeath"])
            # Decrement hull when player is hit with no shields
            self.hull -= 1
            # Mark run end time if hull is 0
            if self.hull <= 0:
                game_state.run_stats.end_time = pygame.time.get_ticks()
        else:
            self.assets["playerDeath"].play()
        pass

    def player_collision_check(self, objects, game_state):
        # --- Collision Detection for Player (Unified via Quadtree) ---
        # Create a quadtree covering the whole screen
        collision_qtree = Quadtree(Boundary(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)
        # Insert enemies and enemy bullets (with a type tag)
        for obj in objects:
            collision_qtree.insert(Point(obj.x, obj.y, obj))

        # Query the quadtree using the player's hitbox
        player_hitbox = self.get_hitbox()
        collision_candidates = []
        collision_qtree.query(Boundary(player_hitbox.centerx, player_hitbox.centery, player_hitbox.width//2, player_hitbox.height//2), collision_candidates)
        for pt in collision_candidates:
            obj = pt.obj
            # Only check for enemy bullets and enemies
            if hasattr(obj, 'name') and (obj.name == 'enemy_bullet' or obj.name.startswith('enemy')):
                if player_hitbox.colliderect(obj.get_rect()) and self.inv_frames <= 0:
                    # If reflector is active and charge > 0, do not lose shield, just reflect
                    if self.reflector_active and self.reflector_charge > 0:
                        # Remove the enemy bullet (it will be reflected in update_reflector)
                        if obj.name == 'enemy_bullet' and obj in objects:
                            objects.remove(obj)
                        # Play FX for reflection
                        if self.fx:
                            self.fx.flash(duration=4, color=(255,140,0))
                        return
                    if self.shields > 0:
                        self.shields -= 1
                        self.shield_recharge_progress[self.shields] = 0.0  # Start recharge for this shield
                        self.shield_recharge_cooldown = 5.0  # 5s cooldown before recharge resumes
                        self.inv_frames = 20
                        # Play teal circle FX (flash)
                        if self.fx:
                            self.fx.flash(duration=8, color=(0,255,255))
                            self.fx.shake(duration=10, intensity=8)  # Add vibration when shield is expended
                        # Remove the enemy bullet
                        if obj.name == 'enemy_bullet' and obj in objects:
                            objects.remove(obj)
                        return  # Don't die, just lose shield
                    else:
                        self.on_hit(objects, game_state)
                        self.inv_frames = 10
                        if self.hull <= 0:
                            game_state.game_over = True
                        return

    def update_reflector(self, enemy_projectiles, game_state):
        # Reflector logic: reflect enemy bullets if active
        if self.reflector_active and self.reflector_charge > 0:
            reflect_radius = 80
            px, py = self.x + self.width//2, self.y + self.height//2

            # Find the machine gun weapon
            mg_weapon = None
            for weapon in self.weapons:
                if hasattr(weapon, 'trigger') and hasattr(weapon, 'profile') and weapon.profile["name"] == "bullet":
                    mg_weapon = weapon
                    break
            for proj in enemy_projectiles:
                if hasattr(proj, 'name') and proj.name == 'enemy_bullet':
                    dx = (proj.x + proj.image.get_width()//2) - px
                    dy = (proj.y + proj.image.get_height()//2) - py
                    dist = (dx**2 + dy**2)**0.5
                    if dist < reflect_radius and mg_weapon is not None:
                        # Mark projectile as expired instead of removing directly
                        proj.life_timer = 0
                        # Find nearest enemy
                        nearest_enemy = None
                        min_dist = float('inf')
                        if hasattr(game_state, 'enemy_manager'):
                            enemies = game_state.enemy_manager.enemies
                        else:
                            enemies = []
                        for enemy in enemies:
                            ex = enemy.x + getattr(enemy, 'width', enemy.image.get_width())//2
                            ey = enemy.y + getattr(enemy, 'height', enemy.image.get_height())//2
                            edist = ((ex - proj.x)**2 + (ey - proj.y)**2)**0.5
                            if edist < min_dist:
                                min_dist = edist
                                nearest_enemy = enemy
                        if nearest_enemy:
                            ex = nearest_enemy.x + getattr(nearest_enemy, 'width', nearest_enemy.image.get_width())//2
                            ey = nearest_enemy.y + getattr(nearest_enemy, 'height', nearest_enemy.image.get_height())//2
                            dx = ex - proj.x
                            dy = ey - proj.y
                            angle = math.degrees(math.atan2(dy, dx))
                        else:
                            angle = -90  # Default: send upward
                        # BYPASS COOLDOWN: temporarily set last_shot to 0
                        old_last_shot = mg_weapon.last_shot
                        mg_weapon.last_shot = 0
                        # Trigger a machine gun shot from the center of the reflector
                        mg_weapon.trigger(
                            proj.x + proj.image.get_width() // 2,
                            proj.y + proj.image.get_height() // 2,
                            angle,
                            self.projectiles,
                            game_state
                        )
                        mg_weapon.last_shot = old_last_shot
                        # Add 2 ammo to machine gun for each reflected bullet
                        mg_weapon.ammo += 2
                        # Track bullets reflected
                        if game_state is not None:
                            game_state.run_stats.bullets_reflected += 1
                        # Optionally, add FX
                        if self.fx:
                            self.fx.flash(duration=4, color=(255,140,0))
        # Vibrating orange circle FX
        if self.reflector_active and self.reflector_charge > 0 and self.fx:
            self.fx.shake(duration=2, intensity=3)

    def game_events(self, events, background, game_state=None):
        # --- Player Input Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print(utils.GameState.game_over)
                utils.GameState.game_quit = True
                utils.GameState.game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.weapons[0].trigger(self.x + self.width//2, self.y, 270, self.projectiles, game_state)
                    if game_state is not None:
                        game_state.run_stats.bullets_fired += 1
                elif event.key == pygame.K_w:
                    self.weapons[1].trigger(self.x + self.width//2, self.y, 270, self.projectiles, game_state)
                    if game_state is not None:
                        game_state.run_stats.bullets_fired += 1
                elif event.key == pygame.K_e:
                    self.weapons[2].trigger(self, 270, self.projectiles, game_state)
                    if game_state is not None:
                        game_state.run_stats.bullets_fired += 1
                elif event.key == pygame.K_r:
                    self.weapons[3].trigger(self, 270, self.beams, game_state)
                    if game_state is not None:
                        game_state.run_stats.bullets_fired += 1
                elif event.key == pygame.K_ESCAPE and game_state is not None:
                    game_state.paused = not game_state.paused
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.fx.sway_left()
            self.move(-10)
        if keys[pygame.K_RIGHT]:
            self.move(10)
            self.fx.sway_right()
        # Reflector activation
        if keys[pygame.K_SPACE] and self.reflector_charge > 0:
            self.reflector_active = True
        else:
            self.reflector_active = False
