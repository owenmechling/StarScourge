import pygame
import random
import math

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
        "enemy_bullet": pygame.image.load("./assets/enemyBullet.png"),
        "boss": pygame.image.load("./assets/boss.png"),
        "bullet": pygame.image.load("./assets/weaponBullet.png"),
        "rocket": pygame.image.load("./assets/weaponRocket.png"),
        "shockwave": pygame.image.load("./assets/weaponShockwave.png"),
        "laserBase": pygame.image.load("./assets/weaponLaserBase.png"),
        "laserBeam": pygame.image.load("./assets/weaponLaserBeam.png"),
        "background": pygame.image.load("./assets/background.png"),
        "shipExplosion": pygame.image.load("./assets/shipExplosion.png"),
        "rocketExplosion": pygame.image.load("./assets/rocketExplosion.png"),
        "gameOver": pygame.image.load("./assets/gameOverScreen.png"),
        "laserSound": pygame.mixer.Sound("./assets/laserSound.mp3"),
        "rocketLaunch": pygame.mixer.Sound("./assets/rocketLaunch.mp3"),
        "basicAttack": pygame.mixer.Sound("./assets/basicAttack.mp3"),
        "shockwaveSound": pygame.mixer.Sound("./assets/shockwaveSound.mp3"),
        "enemyDeath": pygame.mixer.Sound("./assets/enemyDeath.mp3"),
        "playerDeath": pygame.mixer.Sound("./assets/playerDeath.mp3"),
        "rocketDeath": pygame.mixer.Sound("./assets/rocketDeath.mp3"),
        "backgroundMusic": pygame.mixer.Sound("./assets/backgroundMusic.mp3"),
        "backgroundMusicFile": "./assets/backgroundMusic.mp3"
        
        }

        self.font = pygame.font.Font("./assets/BlockCraft.otf", 24)

# *** Game State Settings ***
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

class Background:
    def __init__(self, assets):
        self.bg_img = assets["background"].convert()
        self.bg_height = self.bg_img.get_height()
        self.bg_width = self.bg_img.get_width()
        self.bg_y = -(self.bg_height - SCREEN_HEIGHT)
        self.bg_x = (self.bg_width - SCREEN_WIDTH) // 2
        self.bg_scroll_speed = 0.2
        self.scrolling_done = False


    def update(self):
        if not self.scrolling_done:
            self.bg_y += self.bg_scroll_speed
            if self.bg_y >= 0:
                self.bg_y = 0
                self.scrolling_done = True

class Hud:
    def draw_hud(self, screen, game_state, player):
        # --- HUD ---
        font = pygame.font.Font("./assets/BlockCraft.otf", 24)
        #TODO math
        # for weapon in player.weapons:
        #     weapon_text = weapon.hud_text()

        ammo_text = font.render(player.weapons[0].hud_text(), True, (255, 255, 255))
        screen.blit(ammo_text, (10, 10))
        laser_color = (0, 255, 0) if player.weapons[2].cooldown <= 0 else (255, 0, 0)
        laser_status = "Laser: READY" if player.weapons[2].cooldown <= 0 else "Laser: ON COOLDOWN"
        laser_text = font.render(laser_status + player.weapons[2].hud_text(), True, laser_color)
        screen.blit(laser_text, (10, 30))
        shock_color = (0, 255, 0) if player.weapons[3].cooldown >= 0 else (255, 165, 0)
        shock_status = "Shockwave: READY" if player.weapons[3].cooldown >= 0 else "Shockwave: COOLDOWN"
        shock_text = font.render(shock_status + player.weapons[3].hud_text(), True, shock_color)
        screen.blit(shock_text, (10, 50))
        # Display Kill Counter
        kill_text = font.render(f"Kills: {game_state.kill_count}", True, (255, 255, 0))
        screen.blit(kill_text, (10, 70))


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