from quadtree import Quadtree, Boundary, Point
from utils import SCREEN_WIDTH, SCREEN_HEIGHT
from weapons import profiles
import projectile
from projectile import Projectile
import random
import math


class Random_Spawner:
    def __init__(self, assets):
            self.assets = assets
            self.profiles = profiles(assets)
            self.enemies = []
            self.spawn_interval = 40
            self.enemy_spawn_timer = 10
            self.enemy_projectiles = []

    def update(self, kill_count, player):
        self.spawn_interval = max(40 - (kill_count // 2), 20)
        for projectile in self.enemy_projectiles:
            projectile.update()
            if projectile.life_timer <= 0:
                self.enemy_projectiles.remove(projectile)
        for enemy in self.enemies:
            enemy.update()
            projectile = enemy.try_shoot(player)
            if projectile is not None:
                self.enemy_projectiles.append(projectile)
        if self.enemy_spawn_timer <= 0:
            enemy_width = self.assets["enemy0"].get_width()
            enemy_x = random.randint(0, SCREEN_WIDTH - enemy_width)
            enemy_y = -50  # spawn above the screen
            enemy_type = random.randint(0, 2)
            image_key = f"enemy{enemy_type}"
            #add enemy to the list
            self.enemies.append(Enemy(enemy_x, enemy_y, self.assets[image_key], enemy_type, self.profiles.BULLET))
            self.enemy_spawn_timer = random.randint(self.spawn_interval, self.spawn_interval + 30)
        else:
            self.enemy_spawn_timer -= 1

    def draw(self, screen):
        for enemy in self.enemies:
            enemy.draw(screen)
        for projectile in self.enemy_projectiles:
            projectile.draw(screen)

    def enemy_screen_effects(self, screen):
        return

    def game_events(self, game_state):
        for enemy in self.enemies:
            if enemy.y > SCREEN_HEIGHT:
                self.enemies.remove(enemy)
                #game_state.game_over = False # If any enemy goes off the screen, game over

    def proj_collision_check(self, projectiles, game_state):
        # --- Collision Detection for Player's Projectiles vs. Enemies (USES Quadtree) ---
        # Build a quadtree for enemy collisions (for bullets, rockets, shockwaves, laser)
        enemy_qtree = Quadtree(Boundary(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)
        for enemy in self.enemies:
            enemy_qtree.insert(Point(enemy.x, enemy.y, enemy))
        for projectile in projectiles[:]:
            search_area = Boundary(projectile.x, projectile.y, projectile.hit_radius, projectile.hit_radius)
            found = []
            enemy_qtree.query(search_area, found)
            for pt in found:
                if projectile.get_rect().colliderect(pt.obj.get_rect()):
                    try:
                        if projectile.damage == 0:
                            projectiles.remove(projectile)
                        else:
                            projectile.damage -= 1
                        # Create an default explosion
                        self.enemies.remove(pt.obj)
                        # Create an default explosion
                        self.enemy_projectiles.append(Projectile(pt.obj.x, pt.obj.y, 0, self.profiles.EXPLOSION))
                        self.assets["enemyDeath"].play()  # Play enemy death sound
                        game_state.kill_count += 1  # Increment kill counter
                        break
                    except ValueError:
                        pass

    def beam_collision_check(self, beams, game_state):
        # --- Collision Detection for Player's Projectiles vs. Enemies (USES Quadtree) ---
        # Build a quadtree for enemy collisions (for bullets, rockets, shockwaves, laser)
        enemy_qtree = Quadtree(Boundary(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)
        for enemy in self.enemies:
            enemy_qtree.insert(Point(enemy.x, enemy.y, enemy))
        for beam in beams[:]:
            search_area = Boundary(beam.x, beam.y, beam.hit_radius, beam.hit_radius)
            found = []
            enemy_qtree.query(search_area, found)
            for pt in found:
                if beam.get_rect().colliderect(pt.obj.get_rect()):
                    try:
                        #target.hull -= beam.damage
                        self.enemies.remove(pt.obj)
                        # Create an default explosion
                        self.enemy_projectiles.append(Projectile(pt.obj.x, pt.obj.y, 0, self.profiles.EXPLOSION))
                        self.assets["enemyDeath"].play()  # Play enemy death sound
                        game_state.kill_count += 1  # Increment kill counter
                        break
                    except ValueError:
                        pass

class Enemy:
    def __init__(self, x, y, image, type_id, profile, name="enemy"):
        self.x, self.y = x, y
        self.image = image
        self.type_id = type_id
        self.name = name
        self.profile = profile

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

    def try_shoot(self, player=None):
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
            return projectile.Projectile(bullet_x, bullet_y, angle, self.profile)
        return None

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))