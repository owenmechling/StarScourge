import pygame
from quadtree import Quadtree, Boundary, Point
from projectile import Projectile
import random
import utils
import baddies
from player import Player
from weapons import profiles
from utils import SCREEN_WIDTH, SCREEN_HEIGHT, FXManager

def main():
    #Setup initial variables
    pygame.init()
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
    

    # ---- Main Loop ----
    while game_state.game_quit == False:
        #start music
        game_state.set_music()
        # ---- Gameplay Loop ----
        while game_state.game_over == False:
            # setup background and HUD
            screen.fill((0, 0, 0))
            background.update()
            screen.blit(background.bg_img, (fx.bg_offset_x, background.bg_y))
            #screen.blit(background.bg_img, (background.bg_x, background.bg_y))
            hud_manager.draw_hud(screen, game_state, player)
            # Update and draw player and player objects
            player.game_events(pygame, background)
            player.update(enemy_manager.enemies)
            player.draw(screen)
            # Update/Draw enemies and enemy projectiles/effects
            enemy_manager.update(game_state.kill_count, player)   
            enemy_manager.draw(screen)
            enemy_manager.game_events(game_state)
            # Run quadtree collision detection for player and enemy ships
            player.player_collision_check(enemy_manager.enemies+enemy_manager.enemy_projectiles, game_state)
            enemy_manager.proj_collision_check(player.projectiles, game_state)
            enemy_manager.beam_collision_check(player.beams, game_state)
            # Update and draw FX
            fx.update()
            fx.draw(screen)
            # display and move to the next frame
            pygame.display.flip()
            clock.tick(60)

        # --- Main Menu Loop ---
        while not game_state.game_quit and game_state.game_over:
            # Game Over Screen Loop with Retry Option
            menus.main(screen)
            menus.main_events(pygame.event.get(), game_state)
            pygame.display.flip()
            clock.tick(60)   
            
    pygame.quit()

if __name__ == "__main__":
    main()