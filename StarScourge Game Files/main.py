import pygame
from quadtree import Quadtree, Boundary, Point
from projectile import Projectile
import random
import utils
import baddies
import leaderboard
from player import Player
from weapons import profiles
from utils import SCREEN_WIDTH, SCREEN_HEIGHT, FXManager


# Explicitly initialize the mixer with safe settings for macOS
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.init()

def main():
    #Setup initial variables
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("StarScourge")
    clock = pygame.time.Clock()
    asset_manager = utils.Assets()
    game_state = utils.GameState(asset_manager.assets)
    background = utils.Background(asset_manager.assets)
    menus = utils.MenuScreens()
    hud_manager = utils.Hud()
    fx = FXManager()
    profile = profiles(asset_manager.assets)
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70, asset_manager.assets, fx, profile)
    enemy_manager = baddies.Random_Spawner(asset_manager.assets)
    damage_numbers = []  # Track all active damage numbers
    music_mixer = utils.MusicMixer(asset_manager.assets)
    prev_music_state = None

    game_over_delay = 0  # No delay, instant game over
    game_over_timer = 0
    player_alive = True

    game_state.in_menu = True
    # ---- Main Loop ----
    while game_state.game_quit == False:
        # --- PRE-GAME MENU ---
        while getattr(game_state, 'in_menu', False):
            music_mixer.set_state("pregame")
            btn_rect = menus.draw_pregame_menu(screen, game_state)
            menus.handle_pregame_menu_events(pygame.event.get(), game_state, btn_rect)
            music_mixer.set_master_volume(game_state.volume)
            music_mixer.update()
            pygame.display.flip()
            clock.tick(60)
            if game_state.game_quit:
                pygame.quit()
                return

        # ---- Gameplay Loop ----
        while game_state.game_over == False:
            # Bossfight triggers and music switching
            #print(f"[DEBUG] bg_y: {background.bg_y}") # DEBUGGER ====================
            boss1_should_spawn = (not game_state.boss1_spawned and background.bg_y >= -2200)
            boss2_should_spawn = (not game_state.boss2_spawned and background.bg_y >= 0 and background.scrolling_done)
            # Spawn Boss 1
            if boss1_should_spawn:
                #print("[DEBUG] Spawning Boss 1!") # DEBUGGER ====================
                enemy_manager.spawn_boss(1)
                #print(f"[DEBUG] Enemies after spawn: {[e.name for e in enemy_manager.enemies]}") # DEBUGGER ====================
                game_state.boss1_spawned = True
                music_mixer.set_state("boss")
            # Pause scrolling for boss 1 if active
            boss1_active = game_state.boss1_spawned and not game_state.boss1_defeated and enemy_manager.boss_active()
            # Resume scrolling after boss 1 defeated
            if game_state.boss1_spawned and not enemy_manager.boss_active() and not game_state.boss1_defeated:
                #print("[DEBUG] Boss 1 defeated!") # DEBUGGER ====================
                game_state.boss1_defeated = True
                music_mixer.set_state("game")
            # Spawn Boss 2
            if boss2_should_spawn and game_state.boss1_defeated:
                enemy_manager.spawn_boss(2)
                game_state.boss2_spawned = True
                music_mixer.set_state("boss")
            # Mark boss 2 defeated
            if game_state.boss2_spawned and not enemy_manager.boss_active() and not game_state.boss2_defeated:
                game_state.boss2_defeated = True
                music_mixer.set_state("game")
            # Determine the correct music state based on game state (check every frame)
            if game_state.game_over:
                music_state = "gameover"
            elif game_state.paused:
                music_state = "pause"
            elif boss1_active or (game_state.boss2_spawned and not game_state.boss2_defeated and enemy_manager.boss_active()):
                music_state = "boss"
            else:
                music_state = "game"
            if music_state != prev_music_state:
                music_mixer.set_state(music_state)
                prev_music_state = music_state
            music_mixer.set_master_volume(game_state.volume)
            music_mixer.update()
            # Handle pause FIRST
            if game_state.paused:
                menus.draw_pause_menu(screen, game_state)
                menus.handle_pause_menu_events(pygame.event.get(), game_state)
                pygame.display.flip()
                clock.tick(60)
                if game_state.retry:
                    return main()
                if game_state.game_quit:
                    pygame.quit()
                    return
                continue
            # setup background and HUD
            screen.fill((0, 0, 0))
            background.update(allow_scroll_after_boss1=game_state.boss1_defeated)
            screen.blit(background.bg_img, (fx.bg_offset_x, background.bg_y))
            hud_manager.draw_hud(screen, game_state, player)
            player.game_events(pygame, background, game_state)
            player.update(enemy_manager.enemies)
            player.update_reflector(enemy_manager.enemy_projectiles, game_state)

            # Check for player death
            if player.hull <= 0 and player_alive:
                player_alive = False
                game_state.game_over = True
                game_state.run_stats.end_time = pygame.time.get_ticks()
                game_over_timer = 0

            if not player_alive:
                # Instantly break to game over screen
                break

            player.draw(screen)
            enemy_manager.update(game_state.kill_count, player)   
            enemy_manager.draw(screen)
            enemy_manager.game_events(game_state)
            player.player_collision_check(enemy_manager.enemies+enemy_manager.enemy_projectiles, game_state)
            # EXPLOSIONS: update and draw
            if not hasattr(game_state, 'explosions'):
                game_state.explosions = []
            for ex in game_state.explosions[:]:
                ex.update()
                ex.draw(screen)
                if ex.life_timer <= 0:
                    game_state.explosions.remove(ex)
            enemy_manager.proj_collision_check(player.projectiles, game_state, damage_numbers, asset_manager.font, explosions=game_state.explosions)
            enemy_manager.beam_collision_check(player.beams, game_state, damage_numbers, asset_manager.font)
            fx.update()
            fx.draw(screen)
            for dn in damage_numbers[:]:
                dn.update()
                dn.draw(screen)
                if dn.duration <= 0:
                    damage_numbers.remove(dn)
            # Handle boss fade-out and explosions
            for enemy in enemy_manager.enemies[:]:
                if hasattr(enemy, 'fading') and enemy.fading and hasattr(enemy, 'pending_boss_explosions'):
                    for bx, by, bprofile in enemy.pending_boss_explosions[:]:
                        game_state.explosions.append(Projectile(bx, by, 0, bprofile))
                        enemy.pending_boss_explosions.remove((bx, by, bprofile))
                    # Trigger screen shake on final explosion
                    if hasattr(enemy, 'final_explosion_triggered') and enemy.final_explosion_triggered:
                        fx.shake(duration=20, intensity=16)
                        enemy.final_explosion_triggered = False  # Only trigger once
                    # Remove boss when fully faded
                    if enemy.fade_alpha <= 0:
                        enemy_manager.enemies.remove(enemy)
            for enemy in enemy_manager.enemies:
                pygame.draw.rect(screen, (0, 255, 0), enemy.get_rect(), 2)
            for beam in player.beams:
                pygame.draw.rect(screen, (255, 0, 0), beam.get_rect(), 2)
            game_state.time += 1
            pygame.display.flip()
            clock.tick(int(60 * game_state.game_speed))

        # --- Game Over Screen ---
        music_mixer.set_state("gameover")  # Ensure gameover music always plays
        while not game_state.game_quit and game_state.game_over:
            # --- In-game initials entry ---
            if not hasattr(game_state, "initials"):  # Track initials entry state
                game_state.initials = ""
                game_state.initials_entered = False
                game_state.score_submitted = False
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and not game_state.initials_entered:
                    if event.key == pygame.K_BACKSPACE:
                        game_state.initials = game_state.initials[:-1]
                    elif event.key >= pygame.K_a and event.key <= pygame.K_z and len(game_state.initials) < 3:
                        game_state.initials += chr(event.key).upper()
                    elif event.key == pygame.K_RETURN and len(game_state.initials) == 3:
                        game_state.initials_entered = True
                elif event.type == pygame.KEYDOWN and game_state.initials_entered:
                    if event.key == pygame.K_r:
                        return main()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    return
            # Auto-submit when 3 letters entered
            if len(game_state.initials) == 3 and not game_state.score_submitted:
                leaderboard.submit_score(game_state.initials, game_state.kill_count)
                game_state.score_submitted = True
                game_state.initials_entered = True
            menus.draw_game_over(screen, game_state)
            pygame.display.flip()
            clock.tick(60)
            
    pygame.quit()

if __name__ == "__main__":
    main()