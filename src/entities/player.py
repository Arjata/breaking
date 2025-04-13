import pygame
from pygame.math import Vector2
from random import random

# Assuming Config is imported correctly
try:
    from ..core.config import Config
except ImportError:
    # Fallback for running standalone
    class Config:
        WIDTH = 1280
        HEIGHT = 720


from ..entities.powerup import PowerUpType


# Assuming Bullet and PowerBullet classes are defined below or imported
# from ..entities.bullet import Bullet, PowerBullet # Example import


class Player(pygame.sprite.Sprite):
    """Represents the player character."""

    def __init__(self, pos: tuple[int, int]):
        """
        Initializes the player sprite.

        Args:
            pos: Initial center position (x, y) for the player.
        """
        super().__init__()

        # --- Core Attributes ---
        self.speed = 450  # Pixels per second
        self.max_health = 7
        self.health = self.max_health
        self.invincible = False  # Currently invincible?
        self.invincible_duration = 1.5  # Seconds
        self.invincible_timer = 0.0  # Float for dt accuracy

        # --- Image and Position ---
        self.image = None  # Will be loaded by _load_image
        self.rect = None  # Will be set by _load_image
        self.hitbox = None  # Will be set by _load_image
        self._load_image(pos)  # Load graphics and set initial position

        # --- Shooting ---
        self.shoot_cooldown = 0.2  # Default seconds between shots
        self.last_shot_time = 0.0  # Use float seconds
        self.crit_chance = 0.1  # 10% critical hit chance
        # self.bullet_type = "normal" # Can be managed by powerups

        # --- Powerups ---
        self.active_powerups = []
        self.powerup_timer_fire_power = 0.0
        self.powerup_duration_fire_power = 0.0
        self.shield_count = 0

        # Note: Removed self.is_alive, use self.alive() inherited from Sprite

        self.velocity = Vector2(0, 0)
        self.killed_enemy_count = 0

    def _load_image(self, pos: tuple[int, int]):
        """Loads the player's image and sets up rect and hitbox."""
        try:
            # Load image with transparency support
            # Make sure 'assets/sprites/player.png' path is correct
            self.image = pygame.image.load("assets/sprites/player.png").convert_alpha()
            # Scale if needed, e.g., pygame.transform.scale(self.image, (new_width, new_height))
        except (FileNotFoundError, pygame.error) as e:
            print(f"Error loading player image: {e}")
            # Create a fallback placeholder surface
            self.image = pygame.Surface(
                (32, 32), pygame.SRCALPHA
            )  # Use SRCALPHA for potential transparency
            self.image.fill((0, 0, 0, 0))  # Transparent background
            pygame.draw.polygon(
                self.image, (0, 200, 255), [(16, 0), (0, 32), (32, 32)]
            )  # Blue triangle fallback
            pygame.draw.rect(
                self.image, (255, 0, 0), (14, 25, 4, 6)
            )  # Small red rectangle (engine?)

        self.rect = self.image.get_rect(center=pos)
        # Adjust hitbox size relative to the image (e.g., slightly smaller)
        self.hitbox = self.rect.inflate(
            -int(self.rect.width * 0.2), -int(self.rect.height * 0.2)
        )

    def take_damage(self, amount: int):
        """
        Applies damage to the player if not invincible or shielded.

        Args:
            amount: The amount of damage to take.
        """
        # Ignore damage if shielded or invincible
        if self.shield_count > 0:
            print("Shield blocked damage!")
            # Optionally trigger shield hit effect/sound
            # Maybe deactivate shield after one hit? Depends on design.
            self.shield_count -= 1
            return
        if self.invincible:
            return

        # Apply damage
        self.health -= amount
        print(
            f"Player took {amount} damage! Health: {self.health}/{self.max_health}"
        )  # Debug

        # Check for death
        if self.health <= 0:
            self.health = 0  # Prevent negative health display
            self._die()
        else:
            # Activate invincibility frames if damaged but not dead
            self._activate_invincibility()

    def _die(self):
        """Handles player death."""
        print("Player Died!")
        # Add death effects (explosion particles, sound) here if needed
        # Example: Make player semi-transparent or change image
        # self.image.set_alpha(100)
        self.kill()  # Crucial: Remove sprite from all groups

    def _activate_invincibility(self):
        """Activates temporary invincibility."""
        self.invincible = True
        self.invincible_timer = 0.0  # Reset timer
        # Ensure sprite is fully visible when invincibility starts
        if self.image:
            self.image.set_alpha(255)

    def handle_movement_input(self, keys: pygame.key.ScancodeWrapper, dt: float):
        """
        Handles player movement based on currently pressed keys.

        Args:
            keys: The dictionary of key states from pygame.key.get_pressed().
            dt: Delta time (time since last frame in seconds).
        """
        move_dir = Vector2(0, 0)  # Use Vector2 for direction
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_dir.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_dir.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_dir.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_dir.x += 1

        # Normalize diagonal movement to prevent faster speed
        if move_dir.length_squared() > 0:  # Use length_squared() for efficiency
            move_dir = move_dir.normalize()

        # Apply movement based on direction, speed, and delta time
        new_pos = Vector2(self.rect.center) + move_dir * self.speed * dt
        self.rect.center = (round(new_pos.x), round(new_pos.y))  # Update position

        # Keep player within screen bounds
        self._clamp_position()

    def _clamp_position(self):
        """Restricts player movement to screen boundaries."""
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, Config.WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, Config.HEIGHT)
        # Update hitbox position after clamping rect
        self.hitbox.center = self.rect.center

    def shoot(self, bullet_group: pygame.sprite.Group):
        """
        Attempts to fire a bullet if cooldown allows.

        Args:
            bullet_group: The sprite group to add the new bullet to.
        """
        # Use float time for better accuracy with dt
        now = pygame.time.get_ticks() / 1000.0
        if now - self.last_shot_time >= self.shoot_cooldown:
            self.last_shot_time = now

            # Calculate damage (base + crit)
            (damage, is_critical) = self._calculate_damage()
            spawn_pos = self.rect.midtop  # Bullet spawn position

            # --- Determine Bullet Type ---
            # Example: Powerup might change bullet type or add more bullets
            if PowerUpType.FIREPOWER in self.active_powerups:
                # Firepower boost could mean faster/stronger bullets or multi-shot
                # Example: Fire a PowerBullet
                bullet = PowerBullet(
                    spawn_pos, Vector2(0, -1), damage * 3, is_critical
                )  # PowerBullet already sets its damage
                # Example: Fire multiple normal bullets
                # bullet1 = Bullet(self.rect.topleft, Vector2(0, -1), damage)
                # bullet2 = Bullet(self.rect.topright, Vector2(0, -1), damage)
                # bullet_group.add(bullet1, bullet2)
                # return # Exit if handled multi-shot
            else:
                # Default: Normal bullet
                bullet = Bullet(spawn_pos, Vector2(0, -1), damage, is_critical)

            bullet_group.add(bullet)  # Add the created bullet(s) to the group
            # Add shoot sound effect here

    def update(self, dt: float):
        """
        Updates player state (invincibility, powerups, hitbox).

        Args:
            dt: Delta time (time since last frame in seconds).
        """
        if Config.HOLD_HP:
            self.health = self.max_health
        # --- Update Invincibility ---
        if self.invincible:
            self.invincible_timer += dt
            # Blinking effect (alpha changes rapidly)
            alpha = (
                255 if int(self.invincible_timer * 12) % 2 == 0 else 100
            )  # Faster blink
            if self.image:
                self.image.set_alpha(alpha)

            # Check if invincibility ends
            if self.invincible_timer >= self.invincible_duration:
                self.invincible = False
                self.invincible_timer = 0.0
                if self.image:
                    self.image.set_alpha(255)  # Ensure fully visible

        # --- Update Powerup Timer ---
        if len(self.active_powerups) > 0:
            if PowerUpType.FIREPOWER in self.active_powerups:
                self.powerup_timer_fire_power += dt
                if self.powerup_timer_fire_power >= self.powerup_duration_fire_power:
                    self.deactivate_power_boost()

        # --- Update Hitbox Position ---
        self.rect.center += self.velocity * dt
        # Ensure hitbox stays centered on the player's rect
        if self.rect and self.hitbox:  # Check if rect/hitbox exist
            self.hitbox.center = self.rect.center

    def draw_health_bar(self, surface: pygame.Surface):
        """Draws a health bar above the player."""
        if self.health <= 0 or not self.rect:
            return  # Don't draw if dead or rect not set

        bar_width = 40
        bar_height = 6
        # Position above the player sprite
        pos_x = self.rect.centerx - bar_width // 2
        pos_y = self.rect.top - 15

        # Calculate current health percentage
        health_percent = self.health / self.max_health
        fill_width = int(bar_width * health_percent)

        # Define rectangles
        background_rect = pygame.Rect(pos_x, pos_y, bar_width, bar_height)
        health_fill_rect = pygame.Rect(pos_x, pos_y, fill_width, bar_height)

        # Draw background (dark grey)
        pygame.draw.rect(surface, (80, 80, 80), background_rect)
        # Draw health fill (green)
        if fill_width > 0:
            pygame.draw.rect(surface, (0, 220, 0), health_fill_rect)
        # Optional border
        pygame.draw.rect(surface, (200, 200, 200), background_rect, 1)

    def _calculate_damage(self) -> (int, bool):
        """Calculates bullet damage, including critical hits."""
        base_damage = 1
        calculated_base_damage = base_damage * (1 + self.killed_enemy_count * 0.5)
        # Apply critical hit chance
        if random() < self.crit_chance:
            return (
                calculated_base_damage * 2,
                True,
            )  # Example: Double damage on crit
        return (calculated_base_damage, False)

    # --- Powerup Handling ---

    def apply_powerup(self, power_type):
        """统一处理道具效果"""
        if power_type == PowerUpType.HEALTH:
            self.health = min(self.max_health, self.health + 1)
        elif power_type == PowerUpType.SHIELD:
            self.activate_shield()
        elif power_type == PowerUpType.FIREPOWER:
            self.activate_power_boost()

    def activate_shield(self):
        """Activates the shield effect."""
        print("Shield Activated!")
        self.shield_count += 1
        # Add visual indicator for shield if needed (e.g., draw a circle around player)

    def activate_power_boost(self):
        """Activates the firepower boost effect."""
        print("Firepower Boost Activated!")

        # Optionally change bullet type or add multi-shot in shoot() method
        if PowerUpType.FIREPOWER not in self.active_powerups:
            self.active_powerups.append(PowerUpType.FIREPOWER)
            self.shoot_cooldown = 0.1  # Increase fire rate
            self.powerup_duration_fire_power = 10
        else:
            self.powerup_timer_fire_power = 0

    def deactivate_power_boost(self):
        for i in range(len(self.active_powerups)):
            if self.active_powerups[i] == PowerUpType.FIREPOWER:
                self.active_powerups.pop(i)
        self.powerup_timer_fire_power = 0
        self.powerup_duration_fire_power = 0
        self.shoot_cooldown = 0.2

    def _reset_effects(self):
        """Resets effects that might persist between powerups."""
        # Called by apply_powerup before activating new one
        self.shoot_cooldown = 0.2  # Reset fire rate to default
        self.shield_count = 0  # Ensure shield is off unless explicitly activated

    def _reset_powerup(self):
        """Resets all powerup effects when the timer expires."""
        self.deactivate_power_boost()
        self.active_powerups = []
        self.powerup_timer_fire_power = 0.0
        self.powerup_duration_fire_power = 0.0


# --- Bullet Classes (Example definitions) ---
class Bullet(pygame.sprite.Sprite):
    """Basic player bullet."""

    def __init__(self, pos, direction, damage=1, is_critical=False):
        super().__init__()
        self.damage = damage
        try:
            self.image = pygame.image.load(
                "assets/sprites/bullet_player.png"
            ).convert_alpha()
        except (FileNotFoundError, pygame.error):
            self.image = pygame.Surface((5, 15))
            self.image.fill((100, 200, 255))  # Light blue fallback
        self.rect = self.image.get_rect(center=pos)
        self.speed = 800
        self.direction = direction.normalize()  # Ensure direction is normalized
        self.is_critical = is_critical

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        # Kill if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()


class PowerBullet(Bullet):
    """Stronger player bullet."""

    def __init__(self, pos, direction, damage, is_critical=False):
        # Power bullets have higher base damage
        super().__init__(pos, direction, damage, is_critical)
        try:
            # Use a different graphic for power bullets
            self.image = pygame.image.load(
                "assets/sprites/bullet_player_power.png"
            ).convert_alpha()
        except (FileNotFoundError, pygame.error):
            self.image = pygame.Surface((8, 20))  # Slightly larger fallback
            self.image.fill((255, 100, 255))  # Magenta fallback
        self.rect = self.image.get_rect(center=pos)  # Update rect for new image size
        self.speed = 1000  # Faster speed
