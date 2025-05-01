import pygame
import random
import math
import leaderboard

# *** Screen Settings ***
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

# *** Asset Loading ***
class Assets:
    def __init__(self):
        self.assets = {
        "player": [pygame.image.load(f"./assets/player{i}.png") for i in range(4)],
        "enemy0": pygame.image.load("./assets/enemy0.png"),
        "enemy1": pygame.image.load("./assets/enemy1.png"),
        "enemy2": pygame.image.load("./assets/enemy2.png"),
        "enemyBullet": pygame.image.load("./assets/enemyBullet.png"),
        "boss": pygame.image.load("./assets/boss.png"),
        "bullet": pygame.image.load("./assets/weaponBullet.png"),
        "rocket": pygame.image.load("./assets/weaponRocket.png"),
        "shockwave": pygame.image.load("./assets/weaponShockwave.png"),
        "laserBase": pygame.image.load("./assets/weaponLaserBase.png"),
        "laserBeam": pygame.image.load("./assets/weaponLaserBeam.png"),
        "background": pygame.image.load("./assets/background.png"),
        "shipExplosion": pygame.image.load("./assets/shipExplosion.png"),
        "rocketExplosion": pygame.image.load("./assets/rocketExplosion.png"),
        "enemyDeath0": pygame.image.load("./assets/enemyDeath0.png"),
        "enemyDeath1": pygame.image.load("./assets/enemyDeath1.png"),
        "enemyDeath2": pygame.image.load("./assets/enemyDeath2.png"),
        "enemyHit": pygame.image.load("./assets/enemyHit.png"),
        "gameOver": pygame.image.load("./assets/gameOver.png"),
        "pauseMenu": pygame.image.load("./assets/pauseScreen.png"),
        "preGame": pygame.image.load("./assets/preGame.png"),
        "laserSound": pygame.mixer.Sound("./assets/laserSound.mp3"),
        "rocketLaunch": pygame.mixer.Sound("./assets/rocketLaunch.mp3"),
        "basicAttack": pygame.mixer.Sound("./assets/basicAttack.mp3"),
        "shockwaveSound": pygame.mixer.Sound("./assets/shockwaveSound.mp3"),
        "enemyDeath": pygame.mixer.Sound("./assets/enemyDeath.mp3"),
        "playerDeath": pygame.mixer.Sound("./assets/playerDeath.mp3"),
        "rocketDeath": pygame.mixer.Sound("./assets/rocketDeath.mp3"),
        "backgroundMusic": pygame.mixer.Sound("./assets/backgroundMusic.mp3")
        #"backgroundMusicFile": "./assets/backgroundMusic.mp3"
        
        }

        self.font = pygame.font.Font("./assets/BlockCraft.otf", 24)

# *** Game State Settings ***
class RunStats:
    def __init__(self):
        self.bullets_fired = 0
        self.bullets_hit = 0
        self.bullets_reflected = 0
        self.kills = 0
        self.damage_done = 0
        self.bosses_destroyed = 0
        self.enemies_escaped = 0  # Track enemies that pass the player
        self.start_time = pygame.time.get_ticks()
        self.end_time = None

    def accuracy(self):
        return (self.bullets_hit / self.bullets_fired * 100) if self.bullets_fired else 0

    def run_time_seconds(self):
        if self.end_time is not None:
            return (self.end_time - self.start_time) // 1000
        else:
            return (pygame.time.get_ticks() - self.start_time) // 1000

class GameState:
    def __init__(self, assets):
        self.score = 0
        self.level = 1
        self.player_lives = 3
        self.kill_count = 0
        self.boss_kills = 0
        self.time = 0
        self.retry = False
        self.game_over = False
        self.game_quit = False
        self.assets = assets
        self.paused = False  # Add paused state
        self.total_damage_done = 0  # Track total damage
        self.volume = 0.7  # Default volume
        self.sfx_volume = 0.7  # Add SFX volume
        self.game_speed = 1.0  # Default game speed
        self.boss1_spawned = False
        self.boss1_defeated = False
        self.boss2_spawned = False
        self.boss2_defeated = False
        self.run_stats = RunStats()
    
    def reset(self):
        self.score = 0
        self.level = 1
        self.player_lives = 3
        self.kill_count = 0
        self.boss_kills = 0
        self.time = 0
        self.retry = False
        self.game_over = False
        self.game_quit = False
        self.run_stats = RunStats()

    def set_music(self, music="backgroundMusic", volume=0.7):
        # Play background music if not already playing
        self.assets[music].set_volume(volume)  # Set volume to 70%
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(self.assets["backgroundMusicFile"])
            pygame.mixer.music.play(-1)

class MenuScreens:
    def main(self, screen):
        font_large = pygame.font.SysFont(None, 48)
        font_small = pygame.font.SysFont(None, 24)
        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        exit_text = font_small.render("Press X key to exit", True, (255, 255, 255))
        retry_text = font_small.render("Press Z key to retry", True, (255, 255, 255))
        screen.fill((0, 0, 0))
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT//2))
        screen.blit(retry_text, (SCREEN_WIDTH//2 - retry_text.get_width()//2, SCREEN_HEIGHT//2 + 30))

    def main_events(self, events, game_state):
        for event in events:
            if event.type == pygame.QUIT:
                game_state.game_quit = True
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x:
                    game_state.game_quit = True
                    exit()
                elif event.key == pygame.K_z:
                    game_state.reset()

    def draw_game_over(self, screen, game_state):
        # Draw the game over background
        bg = game_state.assets["gameOver"]
        screen.blit(bg, (0, 0))
        font = pygame.font.Font("./assets/BlockCraft.otf", 36)
        small_font = pygame.font.Font("./assets/BlockCraft.otf", 24)
        # --- Run Stats (left side, left-aligned) ---
        stats_x = 60
        stats_y = 120
        line_h = 38
        run_stats = game_state.run_stats
        stats_lines = [
            f"Run Stats:",
            f"Kills: {run_stats.kills}",
            f"Bosses Defeated: {run_stats.bosses_destroyed}",
            f"Bullets Fired: {run_stats.bullets_fired}",
            f"Bullets Hit: {run_stats.bullets_hit}",
            f"Bullets Reflected: {run_stats.bullets_reflected}",
            f"Accuracy: {run_stats.accuracy():.1f}%",
            f"Damage Done: {run_stats.damage_done}",
            f"Enemies Escaped: {run_stats.enemies_escaped}",  # Add this line
            f"Time: {run_stats.run_time_seconds()}s"
        ]
        for i, line in enumerate(stats_lines):
            text = font.render(line, True, (255, 255, 0) if i == 0 else (255,255,255))
            screen.blit(text, (stats_x, stats_y + i*line_h))
        # --- Initials Entry or Retry Prompt (center bottom) ---
        if not getattr(game_state, "initials_entered", False):
            prompt = "Enter your initials: " + (game_state.initials if hasattr(game_state, "initials") else "")
            prompt_text = font.render(prompt, True, (255,255,255))
            # Move prompt to bottom of window
            prompt_y = screen.get_height() - 80
            screen.blit(prompt_text, (screen.get_width()//2 - prompt_text.get_width()//2, prompt_y))
            # Add smaller restart/exit prompt below
            restart_exit_text = small_font.render("Press R to Restart or ESC to Exit", True, (200,200,200))
            restart_exit_y = prompt_y + prompt_text.get_height() + 8
            screen.blit(restart_exit_text, (screen.get_width()//2 - restart_exit_text.get_width()//2, restart_exit_y))
        else:
            prompt = f"Score submitted as {game_state.initials}!"
            prompt_text = font.render(prompt, True, (0,255,0))
            prompt_y = screen.get_height() - 80
            screen.blit(prompt_text, (screen.get_width()//2 - prompt_text.get_width()//2, prompt_y))
            # Add smaller restart/exit prompt below
            restart_exit_text = small_font.render("Press R to Restart or ESC to Exit", True, (200,200,200))
            restart_exit_y = prompt_y + prompt_text.get_height() + 8
            screen.blit(restart_exit_text, (screen.get_width()//2 - restart_exit_text.get_width()//2, restart_exit_y))
        # --- Leaderboard (right side, right-aligned, justified) ---
        lb_x = screen.get_width() - 60
        lb_y = 120
        lb_title = font.render("Leaderboard:", True, (255, 255, 0))
        screen.blit(lb_title, (lb_x - lb_title.get_width(), lb_y))
        lb_entries = leaderboard.get_leaderboard()[:20]
        for i, entry in enumerate(lb_entries):
            name = entry['name']
            score = entry['score']
            line = f"{name: <3}   {score: >5}"
            text = small_font.render(line, True, (255,255,255))
            screen.blit(text, (lb_x - text.get_width(), lb_y + (i+1)*line_h))

    def draw_pause_menu(self, screen, game_state):
        # Draw pause overlay (600x400 centered)
        overlay = pygame.Surface((600, 400), pygame.SRCALPHA)
        overlay.blit(game_state.assets["pauseMenu"], (0, 0))
        font = pygame.font.Font("./assets/BlockCraft.otf", 32)
        small_font = pygame.font.Font("./assets/BlockCraft.otf", 24)
        # Title
        title = font.render("PAUSED", True, (255,255,255))
        overlay.blit(title, (300-title.get_width()//2, 30))
        # Resume, Restart, Exit
        overlay.blit(small_font.render("Resume", True, (255,255,255)), (80, 100))
        overlay.blit(small_font.render("Restart", True, (255,255,255)), (80, 150))
        overlay.blit(small_font.render("Exit", True, (255,255,255)), (80, 200))
        # Volume slider
        overlay.blit(small_font.render(f"Volume: {int(game_state.volume*100)}", True, (255,255,255)), (80, 260))
        pygame.draw.rect(overlay, (200,200,200), (220, 265, 300, 10))
        pygame.draw.rect(overlay, (255,255,0), (220, 265, int(300*game_state.volume), 10))
        # SFX Volume slider
        overlay.blit(small_font.render(f"SFX: {int(game_state.sfx_volume*100)}", True, (255,255,255)), (80, 285))
        pygame.draw.rect(overlay, (200,200,200), (220, 290, 300, 10))
        pygame.draw.rect(overlay, (255,100,0), (220, 290, int(300*game_state.sfx_volume), 10))
        # Game speed slider
        overlay.blit(small_font.render(f"Game Speed: {game_state.game_speed:.2f}", True, (255,255,255)), (80, 310))
        pygame.draw.rect(overlay, (200,200,200), (300, 315, 200, 10))
        pygame.draw.rect(overlay, (0,255,255), (300, 315, int(200*(game_state.game_speed/2.0)), 10))
        # Blit overlay centered
        screen.blit(overlay, (screen.get_width()//2-300, screen.get_height()//2-200))

    def handle_pause_menu_events(self, events, game_state):
        mouse = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state.paused = False
                elif event.key == pygame.K_r:
                    game_state.retry = True
                elif event.key == pygame.K_q:
                    game_state.game_quit = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = mouse
                # Resume
                if 80 <= mx - (400-300) <= 220 and 100 <= my - (300-200) <= 130:
                    game_state.paused = False
                # Restart
                if 80 <= mx - (400-300) <= 220 and 150 <= my - (300-200) <= 180:
                    game_state.retry = True
                # Exit
                if 80 <= mx - (400-300) <= 220 and 200 <= my - (300-200) <= 230:
                    game_state.game_quit = True
                # Volume slider
                if 220 <= mx - (400-300) <= 520 and 265 <= my - (300-200) <= 275:
                    game_state.volume = min(max((mx - (400-300) - 220)/300, 0), 1)
                # SFX Volume slider
                if 220 <= mx - (400-300) <= 520 and 290 <= my - (300-200) <= 300:
                    game_state.sfx_volume = min(max((mx - (400-300) - 220)/300, 0), 1)
                # Game speed slider
                if 300 <= mx - (400-300) <= 500 and 315 <= my - (300-200) <= 325:
                    game_state.game_speed = min(max((mx - (400-300) - 300)/200*2.0, 0.5), 2.0)

    def draw_pregame_menu(self, screen, game_state):
        # Parallax effect based on mouse position
        mx, my = pygame.mouse.get_pos()
        parallax_strength = 20  # pixels max offset
        center_x, center_y = screen.get_width()//2, screen.get_height()//2
        offset_x = int((mx - center_x) / center_x * parallax_strength)
        offset_y = int((my - center_y) / center_y * parallax_strength)
        # Draw the preGame background with parallax
        bg = pygame.image.load("./assets/preGame.png")
        screen.blit(bg, (offset_x, offset_y))
        font = pygame.font.Font("./assets/BlockCraft.otf", 72)
        small_font = pygame.font.Font("./assets/BlockCraft.otf", 36)
        # Multi-layered, staggered StarScourge title with parallax
        title_text = "StarScourge"
        num_layers = 20
        total_stagger = 10
        stagger_per_layer = total_stagger // (num_layers - 1)
        colors = [(0,0,0) if i%2==0 else (0,255,0) for i in range(num_layers-1)] + [(255,255,255)]  # Top is green
        title_y = 80  # base y
        for i in range(num_layers):
            color = colors[i]
            title = font.render(title_text, True, color)
            # Each layer gets a bit more offset for parallax
            layer_offset_x = offset_x * (1 + i*0.08)
            layer_offset_y = offset_y * (1 + i*0.08)
            y = title_y + i*stagger_per_layer + int(layer_offset_y//2)
            x = screen.get_width()//2 - title.get_width()//2 + int(layer_offset_x)
            screen.blit(title, (x, y))
        # Version, credits, and created by (bottom right)
        smallest_font = pygame.font.Font("./assets/BlockCraft.otf", 18)
        version_text = smallest_font.render("v0.5.7-alpha", True, (200, 200, 200))
        by_text = smallest_font.render("created by mercato", True, (200, 200, 200))
        credits_text = smallest_font.render("credits", True, (100, 200, 255))
        # Positioning
        pad = 12
        bx = screen.get_width() - pad
        by = screen.get_height() - pad
        screen.blit(version_text, (bx - version_text.get_width(), by - 60))
        screen.blit(by_text, (bx - by_text.get_width(), by - 40))
        # Credits button area
        credits_rect = pygame.Rect(bx - credits_text.get_width(), by - 20, credits_text.get_width(), credits_text.get_height())
        screen.blit(credits_text, credits_rect.topleft)
        # Store for event handling
        game_state.credits_rect = credits_rect
        # Start button (lower)
        btn_w, btn_h = 240, 70
        btn_x = screen.get_width()//2 - btn_w//2
        btn_y = screen.get_height() - 120
        pygame.draw.rect(screen, (0,0,0), (btn_x-4, btn_y-4, btn_w+8, btn_h+8), border_radius=16) # Outline
        pygame.draw.rect(screen, (40,40,40), (btn_x, btn_y, btn_w, btn_h), border_radius=16)
        start_text = small_font.render("START", True, (255,255,255))
        screen.blit(start_text, (screen.get_width()//2 - start_text.get_width()//2, btn_y + btn_h//2 - start_text.get_height()//2))
        return (btn_x, btn_y, btn_w, btn_h)

    def handle_pregame_menu_events(self, events, game_state, btn_rect):
        mouse = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.QUIT:
                game_state.game_quit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    game_state.in_menu = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = mouse
                # Start button
                if btn_rect[0] <= mx <= btn_rect[0]+btn_rect[2] and btn_rect[1] <= my <= btn_rect[1]+btn_rect[3]:
                    game_state.in_menu = False
                # Credits button
                if hasattr(game_state, "credits_rect") and game_state.credits_rect.collidepoint(mx, my):
                    # Show credits popup
                    show_credits_popup(screen)

class Background:
    def __init__(self, assets):
        self.bg_img = assets["background"].convert()
        self.bg_height = self.bg_img.get_height()
        self.bg_width = self.bg_img.get_width()
        self.bg_y = -(self.bg_height - SCREEN_HEIGHT)
        self.bg_x = (self.bg_width - SCREEN_WIDTH) // 2
        self.bg_scroll_speed = 0.3 # Speed of background scrolling AKA speed of game
        self.scrolling_done = False

    def update(self, allow_scroll_after_boss1=False):
        # Always scroll until 2700, then stop for boss 1
        if not self.scrolling_done:
            if not allow_scroll_after_boss1 and self.bg_y < 2700:
                self.bg_y += self.bg_scroll_speed
                if self.bg_y >= 2700:
                    self.bg_y = 2700
            elif allow_scroll_after_boss1 and self.bg_y < 0:
                self.bg_y += self.bg_scroll_speed
                if self.bg_y >= 0:
                    self.bg_y = 0
                    self.scrolling_done = True

class Hud:
    def draw_hud(self, screen, game_state, player):
        # --- HUD ---
        font = pygame.font.Font("./assets/BlockCraft.otf", 24)
        # --- Weapon HUD (bottom left, stacked upward, icons shifted up 2) ---
        weapon_y_start = screen.get_height() - 2  # Shift up by 2
        weapon_x = 10
        weapon_spacing = 36  # less vertical space per weapon
        icon_size = 28
        for i, weapon in enumerate(player.weapons):
            # Get weapon image and quantity/cooldown
            if hasattr(weapon, 'profile') and 'image' in weapon.profile:
                icon = weapon.profile['image']
            elif hasattr(weapon, 'profile') and 'base_image' in weapon.profile:
                icon = weapon.profile['base_image']
            else:
                icon = None
            # Draw icon
            if icon is not None:
                icon_scaled = pygame.transform.scale(icon, (icon_size, icon_size))
                screen.blit(icon_scaled, (weapon_x, weapon_y_start - (len(player.weapons) - i - 1) * weapon_spacing - icon_size))
            # Draw quantity/cooldown using weapon's hud_text() if available
            if hasattr(weapon, 'hud_text') and callable(getattr(weapon, 'hud_text')):
                text = weapon.hud_text()
                color = (0,255,0) if "READY" in text else (255,80,80) if "Cooldown" in text or "CD" in text else (255,255,255)
            elif hasattr(weapon, 'ammo'):
                text = f"x {weapon.ammo}"
                color = (255,255,255)
            elif hasattr(weapon, 'cooldown') and weapon.cooldown > 0:
                text = f"CD: {int(weapon.cooldown)}"
                color = (255,80,80)
            else:
                text = "READY"
                color = (0,255,0)
            # Move counters to left-bottom corner, stacking upward
            counter_x = 10 + icon_size + 8
            counter_y = screen.get_height() - 20 - (len(player.weapons) - i - 1) * (icon_size + 8)
            text_surf = font.render(text, True, color)
            screen.blit(text_surf, (counter_x, counter_y))
        # Only keep kill counter at top left
        kill_text = font.render(f"Kills: {game_state.kill_count}", True, (255, 255, 0))
        screen.blit(kill_text, (10, 10))

        # Draw shield counters (teal bars) in bottom right
        shield_bar_w, shield_bar_h = 40, 12
        spacing = 8
        for i in range(player.max_shields):
            x = screen.get_width() - 20 - shield_bar_w
            y = screen.get_height() - 20 - (shield_bar_h + spacing) * i
            if i < player.shields:
                # Full shield
                pygame.draw.rect(screen, (0, 220, 220), (x, y, shield_bar_w, shield_bar_h), border_radius=6)
                pygame.draw.rect(screen, (0, 120, 120), (x, y, shield_bar_w, shield_bar_h), 2, border_radius=6)
            else:
                # Recharging shield: show fill based on progress
                progress = player.shield_recharge_progress[i] / player.shield_recharge_time
                fill_w = int(shield_bar_w * progress)
                pygame.draw.rect(screen, (0, 60, 60), (x, y, shield_bar_w, shield_bar_h), border_radius=6)
                if fill_w > 0:
                    pygame.draw.rect(screen, (0, 180, 180), (x, y, fill_w, shield_bar_h), border_radius=6)
                pygame.draw.rect(screen, (0, 120, 120), (x, y, shield_bar_w, shield_bar_h), 2, border_radius=6)
        # Draw hull (health) counters (red bars) just below shields
        hull_bar_w, hull_bar_h = 40, 10
        hull_spacing = 6
        for i in range(player.hull):
            x = screen.get_width() - 20 - hull_bar_w
            # Always anchor hull bars below the maximum number of shield bars
            y = screen.get_height() - 20 - (shield_bar_h + spacing) * player.max_shields - (hull_bar_h + hull_spacing) * i - 18
            pygame.draw.rect(screen, (220, 40, 40), (x, y, hull_bar_w, hull_bar_h), border_radius=5)
            pygame.draw.rect(screen, (120, 0, 0), (x, y, hull_bar_w, hull_bar_h), 2, border_radius=5)
        # Draw reflector charge bar (orange) at the very bottom, 400px wide, centered, half as thick
        bar_w, bar_h = 400, 7
        bar_x = (screen.get_width() - bar_w) // 2
        bar_y = screen.get_height() - bar_h - 4
        pygame.draw.rect(screen, (80, 40, 0), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * (player.reflector_charge / 100.0))
        pygame.draw.rect(screen, (255, 140, 0), (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(screen, (255, 180, 80), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)


class FXManager:
    def __init__(self):
        self.flash_duration = 0 
        self.flash_color = (255, 255, 255) #default white
        self.shake_duration = 0
        self.shake_intensity = 0
        self.offset = pygame.Vector2(0, 0)
        self.sway_offset = 0
        self.bg_center_offset = -100
        self.bg_offset_decay = 1
        self.bg_offset_max = 30
        self.bg_offset_x = -100
        self.drift_speed = 0.7

    def flash(self, duration=3, color=(255, 255, 255)):
        self.flash_duration = duration
        self.flash_color = color

    def shake(self, duration=10, intensity=5):
        self.shake_duration = duration
        self.shake_intensity = intensity

    def sway_left(self):
        self.bg_offset_x = max(self.bg_center_offset - self.bg_offset_max, self.bg_offset_x - self.drift_speed)

    def sway_right(self):
        self.bg_offset_x = min(self.bg_center_offset + self.bg_offset_max, self.bg_offset_x + self.drift_speed)



    def update(self):
        # Handle screen shake logic
        if self.shake_duration > 0:
            self.shake_duration -= 1
            self.offset.x = random.randint(-self.shake_intensity, self.shake_intensity)
            self.offset.y = random.randint(-self.shake_intensity, self.shake_intensity)
        else:
            self.offset = pygame.Vector2(0, 0)

        # Handle flash fade
        if self.flash_duration > 0:
            self.flash_duration -= 1
        
        # Background sway decay logic
       # if self.bg_offset_x > self.bg_center_offset:
        #    self.bg_offset_x = max(self.bg_center_offset, self.bg_offset_x - self.bg_offset_decay)
        #elif self.bg_offset_x < self.bg_center_offset:
         #   self.bg_offset_x = min(self.bg_center_offset, self.bg_offset_x + self.bg_offset_decay)



        
    def apply_offset(self, pos):
        return (pos[0] + self.offset.x, pos[1] + self.offset.y)

    def draw(self, screen):
        if self.flash_duration > 0:
            overlay = pygame.Surface(screen.get_size())
            overlay.fill(self.flash_color)
            overlay.set_alpha(180)
            screen.blit(overlay, (0, 0))

# *** Damage Number Class *** 
# Shout out vampire survivors
# This class handles the display of damage numbers that appear when enemies are hit.
class DamageNumber:
    def __init__(self, x, y, value, font, color=(0,255,0), duration=30):
        self.x = x + random.randint(-7, 7)  # Add slight random offset
        self.y = y + random.randint(-7, 7)
        self.value = value
        self.font = font
        self.color = color
        self.duration = duration
        self.alpha = 255
        self.dy = -1  # float upward

    def update(self):
        self.y += self.dy
        self.duration -= 1
        if self.alpha > 0:
            self.alpha -= 8  # fade out
        if self.alpha < 0:
            self.alpha = 0

    def draw(self, screen):
        outline_color = (0, 0, 0)
        surf_outline = self.font.render(str(self.value), True, outline_color)
        surf_outline.set_alpha(self.alpha)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    screen.blit(surf_outline, (self.x + dx, self.y + dy))
        # Render the main text
        surf = self.font.render(str(self.value), True, self.color)
        surf.set_alpha(self.alpha)
        screen.blit(surf, (self.x, self.y))


# *** Music Mixer ***
# This class manages different music tracks and their transitions based on game state.
# # It uses dedicated channels for each track to allow simultaneous playback and fading.
# to trigger: music_mixer.set_state("game") or music_mixer.set_state("boss") 
class MusicMixer:
    def __init__(self, assets):
        # Reserve first 5 channels for music, rest for SFX
        pygame.mixer.set_num_channels(16)
        try:
            self.tracks = {
                "game": pygame.mixer.Sound("./Ableton Files/gameMusic.wav"),
                "boss": pygame.mixer.Sound("./Ableton Files/bossMusic.wav"),
                "pause": pygame.mixer.Sound("./Ableton Files/pauseMusic.wav"),
                "pregame": pygame.mixer.Sound("./Ableton Files/gameOver.wav"),
                "gameover": pygame.mixer.Sound("./Ableton Files/gameOver.wav"),
            }
        except Exception as e:
            print(f"[MusicMixer] Error loading music: {e}")
            self.tracks = {}
        self.channels = {name: pygame.mixer.Channel(i) for i, name in enumerate(self.tracks)}
        self.state = None
        self.master_volume = 0.7
        self.fade_speed = 1.0  # Fast fade for responsiveness
        self._init_play()

    def _init_play(self):
        # Start all tracks, set initial volume to 0, and loop forever
        for name, track in self.tracks.items():
            ch = self.channels[name]
            try:
                ch.play(track, loops=-1)
                ch.set_volume(0)
            except Exception as e:
                print(f"[MusicMixer] Error playing {name}: {e}")

    def set_state(self, state):
        if state != self.state:
            print(f"[MusicMixer] Changing state to {state}")
            self.state = state
            # Instantly set gameover music to full volume, others to 0
            if state == "gameover":
                for name, ch in self.channels.items():
                    if name == "gameover":
                        ch.set_volume(self.master_volume)
                    else:
                        ch.set_volume(0)

    def set_master_volume(self, volume):
        self.master_volume = volume

    def update(self):
        targets = {
            "pregame": {"pregame": 1, "game": 0, "boss": 0, "pause": 0, "gameover": 0},
            "game":    {"pregame": 0, "game": 1, "boss": 0, "pause": 0, "gameover": 0},
            "boss":    {"pregame": 0, "game": 0, "boss": 1, "pause": 0, "gameover": 0},
            "pause":   {"pregame": 0, "game": 0, "boss": 0, "pause": 1, "gameover": 0},
            "gameover":{"pregame": 0, "game": 0, "boss": 0, "pause": 0, "gameover": 1},
        }
        if self.state not in targets:
            return
        for name, ch in self.channels.items():
            target = targets[self.state][name] * self.master_volume
            current = ch.get_volume()
            if abs(current - target) < self.fade_speed:
                ch.set_volume(target)
            elif current < target:
                ch.set_volume(min(current + self.fade_speed, target))
            else:
                ch.set_volume(max(current - self.fade_speed, target))

def show_credits_popup(screen):
    # Create a popup surface
    popup_w, popup_h = 200, 200
    popup = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
    popup.fill((30, 30, 30, 240))
    # Try to load credits.png
    try:
        credits_img = pygame.image.load("./assets/credits.png")
        credits_img = pygame.transform.smoothscale(credits_img, (popup_w, popup_h))
        popup.blit(credits_img, (0, 0))
    except Exception as e:
        font = pygame.font.Font("./assets/BlockCraft.otf", 18)
        err = font.render("credits.png not found", True, (255, 100, 100))
        popup.blit(err, (10, popup_h//2 - 10))
    # Draw popup centered
    x = screen.get_width()//2 - popup_w//2
    y = screen.get_height()//2 - popup_h//2
    screen.blit(popup, (x, y))
    pygame.display.flip()
    # Wait for click or key to close
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT):
                waiting = False