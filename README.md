# StarScourge

A pixelized retro space shooter built with pygame, featuring modernized mechanics and a modular codebase.

## Features

- **Advanced Weapons System:** Multiple weapon types including machine gun, homing missiles, shockwave, and laser.
- **Enemy Variety:** Randomly spawning enemies with different behaviors and bosses with unique patterns.
- **Quadtree Collision:** Efficient collision detection for projectiles and entities.
- **Modernized HUD:** Displays ammo, weapon status, kill count, and more.
- **Refactored Architecture:** Modular code with separate files for player, enemies, projectiles, weapons, and utilities.
- **Dynamic Music & SFX:** Music and sound effects adapt to game state and can be adjusted in-game.
- **Pause & Game Over Menus:** In-game menus for pausing, restarting, and adjusting settings.
- 

## Controls

- How to Run

1. Install Python 3.x and [pygame](https://www.pygame.org/).
2. Place all assets in the `assets/` directory as referenced in the code.
3. Run the main game:
   ```bash
   python "StarScourge Game Files/main.py"
   ```
4. Enjoy!

## File Structure

- `StarScourge Game Files/`
  - `main.py` - Main game loop and setup.
  - `player.py` - Player class and logic.
  - `baddies.py` - Enemy and boss logic.
  - `weapons.py` - Weapon profiles and firing logic.
  - `projectile.py` - Projectile and beam classes.
  - powerups.py - Powerup container and logic
  - `utils.py` - Utilities, HUD, menus, FX, and asset loading.
  - `assets/` - Sprites, sounds, and fonts.
  - Ableton Files/ - In progress audio system
  - leaderboard.py - Global leaderboard linked to RESTful bin

## Credits

- Developed for CSC310, Dakota State University.
- Sprites, sounds, and fonts are original creations by Owen Mechling (mercato)

## License

For educational use only.
