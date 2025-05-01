from quadtree import Quadtree, Boundary, Point
import utils
from utils import SCREEN_WIDTH, SCREEN_HEIGHT
from weapons import profiles
import projectile
from projectile import Projectile
import random
import math
import pygame


class Random_Spawner:
    def __init__(self, assets):
            self.assets = assets
            self.profiles = profiles(assets)
            self.enemies = []
            self.spawn_interval = 40
            self.enemy_spawn_timer = 10
            self.enemy_projectiles = []
            self.pending_explosions = []  # For staggered wreckage explosions

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
                if isinstance(projectile, list):
                    self.enemy_projectiles.extend(projectile)
                else:
                    self.enemy_projectiles.append(projectile)
        # Handle pending staggered explosions (wreckage)
        for pe in self.pending_explosions[:]:
            pe['timer'] -= 1
            if pe['timer'] <= 0:
                if 'explosions' in pe and pe['explosions'] is not None:
                    pe['explosions'].append(Projectile(pe['x'], pe['y'], 0, pe['profile']))
                else:
                    self.enemy_projectiles.append(Projectile(pe['x'], pe['y'], 0, pe['profile']))
                self.pending_explosions.remove(pe)
        if self.enemy_spawn_timer <= 0:
            enemy_width = self.assets["enemy0"].get_width()
            enemy_x = random.randint(0, SCREEN_WIDTH - enemy_width)
            enemy_y = -50  # spawn above the screen
            enemy_type = random.randint(0, 2)
            image_key = f"enemy{enemy_type}"
            #add enemy to the list
            self.enemies.append(Enemy(enemy_x, enemy_y, self.assets[image_key], enemy_type, self.profiles.BULLET, self.assets))
            self.enemy_spawn_timer = random.randint(self.spawn_interval, self.spawn_interval + 30)
        else:
            self.enemy_spawn_timer -= 1

    def draw(self, screen):
        for enemy in self.enemies:
            enemy.draw(screen)
        for projectile in self.enemy_projectiles:
            # Fix: if projectile is a list (from boss shooting), draw each item
            if isinstance(projectile, list):
                for p in projectile:
                    p.draw(screen)
            else:
                projectile.draw(screen)

    def enemy_screen_effects(self, screen):
        return

    def game_events(self, game_state):
        for enemy in self.enemies[:]:
            if enemy.y > SCREEN_HEIGHT:
                self.enemies.remove(enemy)
                if game_state is not None and hasattr(game_state, 'run_stats'):
                    game_state.run_stats.enemies_escaped += 1
                #game_state.game_over = False # If any enemy goes off the screen, game over

    def proj_collision_check(self, projectiles, game_state, damage_numbers=None, font=None, explosions=None):
        # --- Collision Detection for Player's Projectiles vs. Enemies (USES Quadtree) ---
        enemy_qtree = Quadtree(Boundary(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)
        for enemy in self.enemies:
            enemy_qtree.insert(Point(enemy.x, enemy.y, enemy))
        for projectile in projectiles[:]:
            if projectile.name == "shockwave":
                # Use a circular hitbox with 200px radius centered on the shockwave
                center_x = projectile.x + projectile.image.get_width() // 2
                center_y = projectile.y + projectile.image.get_height() // 2
                radius = 200
                found = []
                search_area = Boundary(center_x, center_y, radius, radius)
                enemy_qtree.query(search_area, found)
                for pt in found:
                    enemy_center_x = pt.obj.x + pt.obj.image.get_width() // 2
                    enemy_center_y = pt.obj.y + pt.obj.image.get_height() // 2
                    dist = math.hypot(center_x - enemy_center_x, center_y - enemy_center_y)
                    if dist <= radius:
                        try:
                            pt.obj.health -= projectile.damage
                            if game_state is not None:
                                game_state.run_stats.bullets_hit += 1
                                game_state.run_stats.damage_done += projectile.damage
                            if damage_numbers is not None and font is not None:
                                hit_x = pt.obj.x + pt.obj.image.get_width() // 2
                                hit_y = pt.obj.y
                                damage_numbers.append(utils.DamageNumber(hit_x, hit_y, projectile.damage, font))
                            pt.obj.hit_effect_timer = 5
                            if pt.obj.health <= 0:
                                explosion_img = self.assets[f"enemyDeath{random.randint(0,2)}"]
                                explosion_profile = dict(self.profiles.EXPLOSION)
                                explosion_profile["image"] = explosion_img
                                self.enemies.remove(pt.obj)
                                ch = pygame.mixer.find_channel(5)
                                if ch:
                                    ch.set_volume(game_state.sfx_volume)
                                    ch.play(self.assets["enemyDeath"])
                                if game_state is not None:
                                    game_state.run_stats.kills += 1
                                    if hasattr(pt.obj, 'name') and str(pt.obj.name).startswith('boss'):
                                        game_state.run_stats.bosses_destroyed += 1
                                game_state.kill_count += 1
                        except ValueError:
                            pass
                # Remove the shockwave projectile after one frame (it obliterates all in range)
                projectiles.remove(projectile)
                continue
            search_area = Boundary(projectile.x, projectile.y, projectile.hit_radius, projectile.hit_radius)
            found = []
            enemy_qtree.query(search_area, found)
            for pt in found:
                if projectile.get_rect().colliderect(pt.obj.get_rect()):
                    try:
                        damage = projectile.damage
                        pt.obj.health -= damage
                        if game_state is not None:
                            game_state.run_stats.bullets_hit += 1
                            game_state.run_stats.damage_done += damage
                        if damage_numbers is not None and font is not None:
                            # Show damage number at the hit location
                            hit_x = pt.obj.x + pt.obj.image.get_width() // 2
                            hit_y = pt.obj.y
                            damage_numbers.append(utils.DamageNumber(hit_x, hit_y, damage, font))
                        # --- ENEMY HIT EFFECT ---
                        pt.obj.hit_effect_timer = 5  # show hit effect for 5 frames
                        if pt.obj.health <= 0:
                            # --- ENEMY DEATH EXPLOSION ---
                            explosion_img = self.assets["shipExplosion"]
                            explosion_profile = dict(self.profiles.EXPLOSION)
                            explosion_profile["image"] = explosion_img
                            # Save enemy trajectory for post-death explosions
                            enemy_x, enemy_y = pt.obj.x, pt.obj.y
                            enemy_w, enemy_h = pt.obj.image.get_width(), pt.obj.image.get_height()
                            enemy_speed = getattr(pt.obj, 'speed', 2)
                            # Remove enemy immediately
                            self.enemies.remove(pt.obj)
                            ch = pygame.mixer.find_channel(5)
                            if ch:
                                ch.set_volume(game_state.sfx_volume)
                                ch.play(self.assets["enemyDeath"])
                            # Boss death: spawn multiple explosions
                            if hasattr(pt.obj, 'name') and str(pt.obj.name).startswith('boss'):
                                for _ in range(10):
                                    rand_x = enemy_x + random.randint(0, enemy_w)
                                    rand_y = enemy_y + random.randint(0, enemy_h)
                                    explosion_profile2 = dict(self.profiles.EXPLOSION)
                                    explosion_profile2["image"] = explosion_img
                                    if explosions is not None:
                                        explosions.append(Projectile(rand_x, rand_y, 0, explosion_profile2))
                                    else:
                                        self.enemy_projectiles.append(Projectile(rand_x, rand_y, 0, explosion_profile2))
                            # For regular enemies, spawn a trail of explosions along their last path for 1 second
                            else:
                                if explosions is not None:
                                    steps = 6
                                    max_travel = enemy_h  # Only extend a ship's height downwards
                                    for i in range(steps):
                                        frac = i / (steps - 1)
                                        trail_x = int(enemy_x + random.randint(-8, 8))
                                        trail_y = int(enemy_y + frac * max_travel + random.randint(-4, 4))
                                        # Staggered spawn: each explosion spawns 3 frames after the previous
                                        self.pending_explosions.append({
                                            'x': trail_x,
                                            'y': trail_y,
                                            'profile': explosion_profile,
                                            'timer': i * 3,
                                            'explosions': explosions
                                        })
                                else:
                                    steps = 6
                                    max_travel = enemy_h
                                    for i in range(steps):
                                        frac = i / (steps - 1)
                                        trail_x = int(enemy_x + random.randint(-8, 8))
                                        trail_y = int(enemy_y + frac * max_travel + random.randint(-4, 4))
                                        # Staggered spawn: each explosion spawns 3 frames after the previous
                                        self.pending_explosions.append({
                                            'x': trail_x,
                                            'y': trail_y,
                                            'profile': explosion_profile,
                                            'timer': i * 3,
                                            'explosions': None
                                        })
                            if game_state is not None:
                                game_state.run_stats.kills += 1
                                if hasattr(pt.obj, 'name') and str(pt.obj.name).startswith('boss'):
                                    game_state.run_stats.bosses_destroyed += 1
                            game_state.kill_count += 1
                        # Only remove the projectile if it is not a rocket (missile)
                        if projectile.name == "missile":
                            # Spawn rocket explosion at impact
                            explosion_profile = dict(self.profiles.EXPLOSION)
                            explosion_profile["image"] = self.assets["rocketExplosion"]
                            self.enemy_projectiles.append(Projectile(projectile.x, projectile.y, 0, explosion_profile))
                            ch = pygame.mixer.find_channel(5)
                            if ch:
                                ch.set_volume(game_state.sfx_volume)
                                ch.play(self.assets["rocketDeath"])
                            projectiles.remove(projectile)
                        # Remove non-piercing projectiles immediately on hit
                        elif not getattr(projectile.profile, 'get', lambda k, d=None: None)("piercing", False):
                            projectiles.remove(projectile)
                        elif projectile.damage == 0 or projectile.name == "shockwave":
                            projectiles.remove(projectile)
                        else:
                            projectile.damage -= 1
                        break
                    except ValueError:
                        pass

    def beam_collision_check(self, beams, game_state, damage_numbers=None, font=None):
        enemy_qtree = Quadtree(Boundary(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)
        for enemy in self.enemies:
            enemy_qtree.insert(Point(enemy.x, enemy.y, enemy))
        for beam in beams[:]:
            segment_rects = beam.get_segment_rects()
            for seg_rect in segment_rects:
                search_area = Boundary(seg_rect.centerx, seg_rect.centery, seg_rect.width//2, seg_rect.height//2)
                found = []
                enemy_qtree.query(search_area, found)
                for pt in found:
                    if seg_rect.colliderect(pt.obj.get_rect()):
                        damage = beam.profile["damage"] // 10 if beam.profile["damage"] > 1 else 1
                        pt.obj.health -= damage
                        if damage_numbers is not None and font is not None:
                            hit_x = pt.obj.x + pt.obj.image.get_width() // 2
                            hit_y = pt.obj.y
                            damage_numbers.append(utils.DamageNumber(hit_x, hit_y, damage, font))
                        if pt.obj.health <= 0:
                            try:
                                self.enemies.remove(pt.obj)
                                self.enemy_projectiles.append(Projectile(pt.obj.x, pt.obj.y, 0, self.profiles.EXPLOSION))
                                ch = pygame.mixer.find_channel(5)
                                if ch:
                                    ch.set_volume(game_state.sfx_volume)
                                    ch.play(self.assets["enemyDeath"])
                                game_state.kill_count += 1
                            except ValueError:
                                pass

    def spawn_boss(self, boss_number=1):
        # Place boss at center top, just above the screen
        boss_img = self.assets["boss"]
        boss_x = SCREEN_WIDTH//2 - boss_img.get_width()//2
        boss_y = -boss_img.get_height()  # Start above the screen
        boss = BossEnemy(boss_x, boss_y, boss_img, self.assets, boss_number)
        self.enemies.append(boss)

    def boss_active(self):
        # Returns True if a boss is present
        return any(e for e in self.enemies if hasattr(e, 'name') and e.name.startswith('boss'))

    def boss_defeated(self):
        # Returns True if no boss is present
        return not self.boss_active()


class Enemy:
    def __init__(self, x, y, image, type_id, profile, assets, name="enemy"):
        self.x, self.y = x, y
        self.image = image
        self.type_id = type_id
        self.name = name
        self.profile = profile
        self.assets = assets
        # Set speed, shooting interval, and health based on type:
        if self.type_id == 0:
            # Medium speed, shoots at random intervals
            self.speed = 2.0
            self.shoot_interval = random.randint(120, 240)  # in frames (2-4 seconds at 60 FPS)
            self.health = 10
        elif self.type_id == 1:
            # Fast, does not shoot
            self.speed = 3.5
            self.shoot_interval = None
            self.health = 5
        elif self.type_id == 2:
            # Slow, shoots often
            self.speed = 1.0
            self.shoot_interval = random.randint(60, 120)  # more frequent shooting
            self.health = 20

        self.shoot_timer = self.shoot_interval if self.shoot_interval is not None else None
        self.hit_effect_timer = 0  # Timer for hit effect

    def update(self):
        self.y += self.speed
        if self.shoot_timer is not None:
            self.shoot_timer -= 1
        if self.hit_effect_timer > 0:
            self.hit_effect_timer -= 1

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
            # Use enemy bullet profile and enemyBullet.png
            from weapons import profiles
            bullet_profile = dict(profiles(self.assets).BULLET)
            bullet_profile["image"] = self.assets["enemyBullet"]
            bullet_profile["name"] = "enemy_bullet"  # Standardized name
            return projectile.Projectile(bullet_x, bullet_y, angle, bullet_profile)
        return None

    def draw(self, screen):
        if self.hit_effect_timer > 0:
            hit_image = self.assets["enemyHit"]
            screen.blit(hit_image, (self.x, self.y))
        else:
            screen.blit(self.image, (self.x, self.y))

    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))


class BossEnemy:
    def __init__(self, x, y, image, assets, boss_number=1):
        self.x = x
        self.y = y
        self.image = image
        self.assets = assets
        self.name = f"boss{boss_number}"
        self.type_id = 99
        self.health = 300 if boss_number == 1 else 500
        self.speed = 2.5 if boss_number == 1 else 3.0
        self.target_y = 0  # Boss flies in to y=0
        self.dialogue_timer = 180  # Show dialogue for 3 seconds
        self.dialogue = "you'll never make it out of this galaxy alive!" if boss_number == 1 else "You again? This time, you won't survive!"
        self.hit_effect_timer = 0
        self.shoot_timer = 120
        self.shoot_interval = 120
        self.flight_target = None  # (x, y) tuple for next move
        self.flight_timer = 0      # frames until next target
        from weapons import profiles
        self.profiles = profiles(assets)
        self.fading = False
        self.fade_alpha = 255
        self.fade_timer = 0
        self.pending_boss_explosions = []
        self.death_messages = ["IMPOSSIBLE....", "NOOOOOOO!!!!!"]
        self.death_message_timer = 0
        self.death_message_index = 0
        self.final_explosion_triggered = False

    def update(self):
        # Fly in from the top until at target_y
        if self.y < self.target_y:
            self.y += self.speed
            if self.y > self.target_y:
                self.y = self.target_y
        else:
            # After flying in, move toward a random target in the top half of the screen
            if self.flight_target is None or self.flight_timer <= 0:
                margin = 40
                target_x = random.randint(margin, SCREEN_WIDTH - margin - self.image.get_width())
                target_y = random.randint(margin, SCREEN_HEIGHT // 2 - margin)
                self.flight_target = (target_x, target_y)
                self.flight_timer = random.randint(90, 180)  # Pick a new target every 1.5-3 seconds
            else:
                tx, ty = self.flight_target
                dx = tx - self.x
                dy = ty - self.y
                dist = math.hypot(dx, dy)
                if dist > 2:
                    move_x = self.speed * dx / dist
                    move_y = self.speed * dy / dist
                    self.x += move_x
                    self.y += move_y
                else:
                    self.flight_timer = 0  # Arrived, pick new target next frame
                self.flight_timer -= 1
        # Shooting logic
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.hit_effect_timer > 0:
            self.hit_effect_timer -= 1
        if self.fading:
            self.fade_timer += 1
            # Fade out over 30 frames
            self.fade_alpha = max(0, 255 - int(self.fade_timer * (255/30)))
            # Staggered explosions: spawn every 3 frames
            if self.fade_timer % 3 == 0 and self.fade_timer <= 30:
                for _ in range(2):
                    rand_x = self.x + random.randint(0, self.image.get_width())
                    rand_y = self.y + random.randint(0, self.image.get_height())
                    explosion_profile = dict(self.profiles.EXPLOSION)
                    explosion_profile["image"] = self.assets["shipExplosion"]
                    self.pending_boss_explosions.append((rand_x, rand_y, explosion_profile))
            # Show death messages at specific fade times
            if self.fade_timer == 5:
                self.death_message_index = 0
                self.death_message_timer = 60  # 1 second
            if self.fade_timer == 20:
                self.death_message_index = 1
                self.death_message_timer = 60
            # Trigger final explosion and screen shake when fully faded
            if self.fade_alpha <= 0 and not self.final_explosion_triggered:
                self.final_explosion_triggered = True
                explosion_profile = dict(self.profiles.EXPLOSION)
                explosion_profile["image"] = self.assets["shipExplosion"]
                explosion_profile["life_timer"] = 60
                self.pending_boss_explosions.append((self.x + self.image.get_width()//2 - self.assets["shipExplosion"].get_width()//2,
                                                    self.y + self.image.get_height()//2 - self.assets["shipExplosion"].get_height()//2,
                                                    explosion_profile))
                # Request screen shake via game_state if possible (handled in main loop)

    def try_shoot(self, player=None):
        # Boss can shoot at player (simple straight shot for now)
        projectiles = []
        if self.shoot_timer <= 0:
            bullet_x = self.x + self.image.get_width() // 2
            bullet_y = self.y + self.image.get_height()
            angle = 90
            self.shoot_timer = self.shoot_interval
            # Use enemy bullet profile and enemyBullet.png
            bullet_profile = dict(self.profiles.BULLET)
            bullet_profile["image"] = self.assets["enemyBullet"]
            bullet_profile["name"] = "enemy_bullet"  # Standardized name
            projectiles.append(projectile.Projectile(bullet_x, bullet_y, angle, bullet_profile))
            # --- Bosses now fire rockets in addition to bullets ---
            missile_profile = dict(self.profiles.HOMING_MISSILE)
            missile_profile["image"] = self.assets["rocket"]
            missile_profile["name"] = "missile"
            missile_profile["sound"] = self.assets["rocketLaunch"]
            # Boss 1: single rocket, Boss 2: 3-rocket spread
            if self.name == "boss1":
                # Fire one rocket straight down
                rocket = projectile.Projectile(bullet_x, bullet_y, 90, missile_profile)
                projectiles.append(rocket)
            else:
                # Fire 3 rockets in a spread
                for spread_angle in [80, 90, 100]:
                    rocket = projectile.Projectile(bullet_x, bullet_y, spread_angle, missile_profile)
                    projectiles.append(rocket)
        if projectiles:
            return projectiles if len(projectiles) > 1 else projectiles[0]
        return None

    def draw(self, screen):
        if self.fading:
            img = self.image.copy()
            img.set_alpha(self.fade_alpha)
            screen.blit(img, (self.x, self.y))
        elif self.hit_effect_timer > 0:
            hit_image = self.assets["enemyHit"]
            screen.blit(hit_image, (self.x, self.y))
        else:
            screen.blit(self.image, (self.x, self.y))
        # Draw dialogue if timer is active
        if self.dialogue_timer > 0:
            font = pygame.font.Font("./assets/BlockCraft.otf", 32)
            text = font.render(self.dialogue, True, (255,255,0))
            screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 80))
            self.dialogue_timer -= 1
        # Draw death message if timer is active
        if self.death_message_timer > 0 and self.death_message_index < len(self.death_messages):
            font = pygame.font.Font("./assets/BlockCraft.otf", 48)
            text = font.render(self.death_messages[self.death_message_index], True, (255,80,80))
            screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 160))
            self.death_message_timer -= 1

    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))