import pygame
from entity import Player, Enemy, Bullet, Rocket, Shockwave, LaserBeam, LaserWindup, Explosion
from quadtree import Quadtree, Boundary, Point
import random

def main():
    pygame.init()

    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Quadtree Invaders")
    clock = pygame.time.Clock()

    # *** Asset Loading ***
    assets = {
        "player": [pygame.image.load(f"assets/player{i}.png") for i in range(4)],
        "enemy0": pygame.image.load("assets/enemy0.png"),
        "enemy1": pygame.image.load("assets/enemy1.png"),
        "enemy2": pygame.image.load("assets/enemy2.png"),
        "enemy_bullet": pygame.image.load("assets/enemyBullet.png"),
        "boss": pygame.image.load("assets/boss.png"),
        "bullet": pygame.image.load("assets/weaponBullet.png"),
        "rocket": pygame.image.load("assets/weaponRocket.png"),
        "shockwave": pygame.image.load("assets/weaponShockwave.png"),
        "laserBase": pygame.image.load("assets/weaponLaserBase.png"),
        "laserBeam": pygame.image.load("assets/weaponLaserBeam.png"),
        "background": pygame.image.load("assets/background.png").convert(),
        "shipExplosion": pygame.image.load("assets/shipExplosion.png"),
        "rocketExplosion": pygame.image.load("assets/rocketExplosion.png"),
        "laserSound": pygame.mixer.Sound("assets/laserSound.mp3"),
        "rocketLaunch": pygame.mixer.Sound("assets/rocketLaunch.mp3"),
        "basicAttack": pygame.mixer.Sound("assets/basicAttack.mp3"),
        "shockwaveSound": pygame.mixer.Sound("assets/shockwaveSound.mp3"),
        "enemyDeath": pygame.mixer.Sound("assets/enemyDeath.mp3"),
        "playerDeath": pygame.mixer.Sound("assets/playerDeath.mp3"),
        "rocketDeath": pygame.mixer.Sound("assets/rocketDeath.mp3"),
        "backgroundMusic": pygame.mixer.Sound("assets/backgroundMusic.mp3")


    }

    # Game state flags and counters
    game_over = False
    retry = False
    kill_count = 0  # NEW: Kill counter

    # || Background Setup |||
    bg_img = assets["background"]
    bg_height = bg_img.get_height()
    bg_y = -(bg_height - SCREEN_HEIGHT)
    bg_scroll_speed = 0.3
    scrolling_done = False

    # /// Player Setup \\\
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70, assets["player"])

    # Game Entities
    enemies = []
    # Start with a few enemies
    #for i in range(10):
     #   image_key = f"enemy{i % 3}"  # Cycle through enemy0 to enemy2
      #  enemies.append(Enemy(i * 60 + 40, 100, assets[image_key], i % 3))

    enemy_spawn_timer = 0
    enemy_bullets = []

    ## background music


    # Init Weapons / Projectiles
    bullets = []
    rockets = []
    shockwaves = []
    laser_beams = []
    windups = []
    rocket_ammo = 10
    shock_active = False
    laser_ready = True
    laser_timer = 0
    flash_timer = 0
    fireBullet = False
    fireRockets = False

    explosions = []  # List to hold explosion effects

    # ---- Main Game Loop ----
    running = True
    while running:
        screen.fill((0, 0, 0))

        # Play background music if not already playing
        assets["backgroundMusic"].set_volume(0.7)  # Set volume to 70%
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load("assets/backgroundMusic.mp3")
            pygame.mixer.music.play(-1)

        # Background Scrolling
        if not scrolling_done:
            bg_y += bg_scroll_speed
            if bg_y >= 0:
                bg_y = 0
                scrolling_done = True
        screen.blit(bg_img, (0, int(bg_y)))

        # --- Dynamic Enemy Spawning ---

        # Spawn interval decreases (more enemies) as kill_count increases.
        # For example: spawn_interval = max(120 - (kill_count // 5), 30)
        spawn_interval = max(40 - (kill_count // 2), 20)

        if enemy_spawn_timer <= 0:
            enemy_width = assets["enemy0"].get_width()
            enemy_x = random.randint(0, SCREEN_WIDTH - enemy_width)
            enemy_y = -50  # spawn above the screen
            enemy_type = random.randint(0, 2)
            image_key = f"enemy{enemy_type}"
            enemies.append(Enemy(enemy_x, enemy_y, assets[image_key], enemy_type))
            enemy_spawn_timer = random.randint(spawn_interval, spawn_interval + 30)
        else:
            enemy_spawn_timer -= 1

        # Process Input Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    fireBullet = True
                    assets["basicAttack"].play()  # Play basic attack sound effect
                elif event.key == pygame.K_w and rocket_ammo > 0:
                    fireRockets = True
                    assets["rocketLaunch"].play()  # Play rocket launch sound effect
                elif event.key == pygame.K_e and not shock_active:
                    shockwaves.append(Shockwave(player.x + 24, player.y, assets["shockwave"]))
                    shock_active = True
                    assets["shockwaveSound"].play()  # Play shockwave sound effect
                elif event.key == pygame.K_r and laser_ready:
                    windups.append(LaserWindup(player, assets["shockwave"]))
                    laser_timer = 60
                    laser_ready = False
                    assets["laserSound"].play()  # Play laser sound effect

        # Continuous Input (Movement)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.move(-10)
        if keys[pygame.K_RIGHT]:
            player.move(10)

        # Weapons Logic
        if fireBullet:
            bullet_x = player.x + player.width // 2 - assets["bullet"].get_width() // 2
            bullet_y = player.y
            bullets.append(Bullet(bullet_x, bullet_y, assets["bullet"]))
            fireBullet = False

        if fireRockets:
            rocket_x = player.x + player.width // 2 - assets["rocket"].get_width() // 2
            for offset in range(-60, 61, 20):
                rockets.append(Rocket(rocket_x + offset, player.y, assets["rocket"]))
            rocket_ammo -= 1
            fireRockets = False

        if laser_timer > 0:
            laser_timer -= 1
            if laser_timer == 0:
                laser_beams.append(LaserBeam(player, assets["laserBase"], assets["laserBeam"], stack_index=len(laser_beams)))
                flash_timer = 5

        # Update and Draw Player
        player.update()
        player.draw(screen)

        # Update/Draw Enemies
        for enemy in enemies:
            enemy.update()
            enemy.draw(screen)
            if enemy.y > SCREEN_HEIGHT:
               game_over = True  # If any enemy goes off the screen, game over
            

        # Update/Draw Player Projectiles
        for bullet in bullets:
            bullet.update()
            bullet.draw(screen)
        for rocket in rockets:
            rocket.update(enemies)
            if rocket.exploded:
                explosions.append(Explosion(rocket.x, rocket.y, assets["rocketExplosion"], duration=30))
                assets["rocketDeath"].play()  # Play rocket explosion sound 
                rockets.remove(rocket)
            rocket.draw(screen)
        for shock in shockwaves[:]:
            shock.update()
            shock.draw(screen)
            if shock.duration <= 0:
                shockwaves.remove(shock)
                shock_active = False
        for windup in windups[:]:
            windup.update()
            windup.draw(screen)
            if windup.duration <= 0:
                windups.remove(windup)
        for laser in laser_beams[:]:
            laser.update()
            laser.draw(screen)
            if laser.duration <= 0:
                laser_beams.remove(laser)
                laser_ready = True

        # Update and draw explosions
        for explosion in explosions[:]:
            explosion.update()
            explosion.draw(screen)
            if explosion.is_finished():
                explosions.remove(explosion)


        # *** Enemy Bullets Logic ***
        for enemy in enemies:
            bullet = enemy.try_shoot(assets["enemy_bullet"], player)
            if bullet is not None:
                enemy_bullets.append(bullet)

        # Update and Draw Enemy Bullets (without individual collision checks)
        for eb in enemy_bullets:
            eb.update()
            eb.draw(screen)

        # --- Collision Detection for Player (Unified via Quadtree) ---

        # Create a quadtree covering the whole screen
        collision_qtree = Quadtree(Boundary(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)

        # Insert enemies and enemy bullets (with a type tag)
        for enemy in enemies:
            collision_qtree.insert(Point(enemy.x, enemy.y, ("enemy", enemy)))
        for eb in enemy_bullets:
            collision_qtree.insert(Point(eb.x, eb.y, ("enemy_bullet", eb)))

        # Query the quadtree using the player's hitbox
        player_hitbox = player.get_hitbox()
        collision_candidates = []
        collision_qtree.query(Boundary(player_hitbox.centerx, player_hitbox.centery, player_hitbox.width//2, player_hitbox.height//2), collision_candidates)
        for candidate in collision_candidates:
            obj_type, obj = candidate.obj
            if obj_type in ("enemy", "enemy_bullet"):
                explosions.append(Explosion(player.x, player.y, assets["shipExplosion"], duration=30))
                assets["playerDeath"].play()  # Play player death sound
                game_over = True

        # --- Collision Detection for Player's Projectiles vs. Enemies (USES Quadtree) ---
        # Build a quadtree for enemy collisions (for bullets, rockets, shockwaves, laser)
        enemy_qtree = Quadtree(Boundary(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)
        for enemy in enemies:
            enemy_qtree.insert(Point(enemy.x, enemy.y, enemy))
        # Check collisions for bullets
        for bullet in bullets[:]:
            search_area = Boundary(bullet.x, bullet.y, 32, 32)
            found = []
            enemy_qtree.query(search_area, found)
            for pt in found:
                if bullet.get_rect().colliderect(pt.obj.get_rect()):
                    try:
                        enemies.remove(pt.obj)
                        bullets.remove(bullet)
                        explosion_x = pt.obj.x
                        explosion_y = pt.obj.y
                        explosions.append(Explosion(explosion_x, explosion_y, assets["shipExplosion"], duration=30))
                        assets["enemyDeath"].play()  # Play enemy death sound
                        kill_count += 1  # Increment kill counter
                        break
                    except ValueError:
                        pass
        # Check collisions for rockets
        for rocket in rockets[:]:
            search_area = Boundary(rocket.x, rocket.y, 64, 64)
            found = []
            enemy_qtree.query(search_area, found)
            for pt in found:
                if rocket.get_rect().colliderect(pt.obj.get_rect()):
                    try:
                        enemies.remove(pt.obj)
                        rockets.remove(rocket)
                        explosion_x = pt.obj.x
                        explosion_y = pt.obj.y
                        explosions.append(Explosion(explosion_x, explosion_y, assets["shipExplosion"], duration=30))
                        assets["enemyDeath"].play()  # Play enemy death sound
                        kill_count += 1
                        break
                    except ValueError:
                        pass
        # Check collisions for shockwaves
        for shock in shockwaves[:]:
            search_area = Boundary(shock.x, shock.y, shock.radius, shock.radius)
            found = []
            enemy_qtree.query(search_area, found)
            for pt in found:
                if shock.get_rect().colliderect(pt.obj.get_rect()):
                    try:
                        enemies.remove(pt.obj)
                        explosion_x = pt.obj.x
                        explosion_y = pt.obj.y
                        explosions.append(Explosion(explosion_x, explosion_y, assets["shipExplosion"], duration=30))
                        assets["enemyDeath"].play()  # Play enemy death sound
                        kill_count += 1
                    except ValueError:
                        pass
        # Check collisions for lasers
        for laser in laser_beams:
            laser_rect = laser.get_rect()
            search_area = Boundary(laser_rect.centerx, laser_rect.centery, laser_rect.width//2, laser_rect.height//2)
            found = []
            enemy_qtree.query(search_area, found)
            for pt in found:
                if laser_rect.colliderect(pt.obj.get_rect()):
                    try:
                        enemies.remove(pt.obj)
                        explosion_x = pt.obj.x
                        explosion_y = pt.obj.y
                        explosions.append(Explosion(explosion_x, explosion_y, assets["shipExplosion"], duration=30))
                        assets["enemyDeath"].play()  # Play enemy death sound
                        kill_count += 1
                    except ValueError:
                        pass

        # --- HUD ---
        font = pygame.font.SysFont(None, 24)
        ammo_text = font.render(f"Rockets: {rocket_ammo}", True, (255, 255, 255))
        screen.blit(ammo_text, (10, 10))
        laser_color = (0, 255, 0) if laser_ready else (255, 0, 0)
        laser_status = "Laser: READY" if laser_ready else "Laser: ON COOLDOWN"
        laser_text = font.render(laser_status, True, laser_color)
        screen.blit(laser_text, (10, 30))
        shock_color = (0, 255, 0) if not shock_active else (255, 165, 0)
        shock_status = "Shockwave: READY" if not shock_active else "Shockwave: COOLDOWN"
        shock_text = font.render(shock_status, True, shock_color)
        screen.blit(shock_text, (10, 50))
        # Display Kill Counter
        kill_text = font.render(f"Kills: {kill_count}", True, (255, 255, 0))
        screen.blit(kill_text, (10, 70))

        # Laser flash effect
        if flash_timer > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.set_alpha(150)
            flash_surface.fill((255, 255, 255))
            screen.blit(flash_surface, (0, 0))
            flash_timer -= 1

        pygame.display.flip()
        clock.tick(60)

        if game_over:
            running = False

    # --- End of Main Game Loop ---
    if game_over:
        # Game Over Screen Loop with Retry Option
        font_large = pygame.font.SysFont(None, 48)
        font_small = pygame.font.SysFont(None, 24)
        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        exit_text = font_small.render("Press X key to exit", True, (255, 255, 255))
        retry_text = font_small.render("Press Z key to retry", True, (255, 255, 255))
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_x:
                        pygame.quit()
                        exit()
                    elif event.key == pygame.K_z:
                        retry = True
                        break
            if retry:
                break

            screen.fill((0, 0, 0))
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT//2))
            screen.blit(retry_text, (SCREEN_WIDTH//2 - retry_text.get_width()//2, SCREEN_HEIGHT//2 + 30))
            pygame.display.flip()
            clock.tick(60)
        
        if retry:
            main()

    pygame.quit()

if __name__ == "__main__":
    main()

