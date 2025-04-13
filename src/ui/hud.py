# src/ui/hud.py
import pygame
from pygame.locals import *

# Assuming Config is imported correctly and defines WIDTH, HEIGHT
try:
    from ..core.config import Config
except ImportError:
    # Provide fallback config if running standalone or import fails
    class Config:
        WIDTH = 1280
        HEIGHT = 720


class HUD:
    def __init__(self, game):
        """
        Initializes the Heads-Up Display.

        Args:
            game: The main game instance, used to access game state (score, active scene).
        """
        self.game = game  # Reference to the main game instance

        # --- Font Initialization ---
        # Use SysFont for better portability if font files aren't bundled
        try:
            # Try a common sans-serif font
            self.font = pygame.font.SysFont("verdana", 20)
            self.combo_font = pygame.font.SysFont("impact", 36)  # Larger font for combo
        except pygame.error:
            print("Warning: Specified fonts not found, using Pygame default.")
            # Fallback to default font if SysFont fails
            self.font = pygame.font.Font(None, 24)  # Default font, size 24
            self.combo_font = pygame.font.Font(None, 40)  # Default font, size 40

        # --- Internal State Variables ---
        # Initialize with default values
        self._score = 0
        self._combo = 0
        self._wave = 1  # Waves usually start at 1
        self._player_health = 0
        self._player_max_health = 0

        # --- Combo Display Configuration ---
        self.combo_color = (255, 255, 0)  # Yellow for combo
        self.combo_display_threshold = 1  # Show combo if > 1
        self.combo_position = (Config.WIDTH // 2, 50)  # Centered top for combo
        # 添加盾牌计数器变量
        self._shield_count = 0  # 初始化盾牌数量

    def update(self, dt):
        """
        Updates the HUD's internal state by safely fetching data from the game instance.
        This should be called once per frame from the main game loop.
        """
        # --- Update Score and Combo ---
        # Access ScoreManager directly via the game instance (should be reliable)
        try:
            self._score = self.game.score_manager.current_score
            self._combo = self.game.score_manager.combo
        except AttributeError:
            print("Warning: HUD could not find score_manager in game instance.")
            # Keep previous values or reset to 0? Let's keep previous for now.
            pass  # self._score and self._combo retain their last known values

        # --- Update Wave Number (Safely) ---
        current_wave = 1  # Default wave
        try:
            # Check if active_scene exists and has a way to report the wave
            # Option 2: Scene has a 'spawner' with a 'wave' attribute (less ideal coupling)
            if hasattr(self.game.active_scene, "spawner") and hasattr(
                self.game.active_scene.spawner, "wave"
            ):
                current_wave = self.game.active_scene.spawner.wave
            elif self.game.active_scene:
                # Option 1: Scene has a 'current_wave' attribute (preferred)
                if hasattr(self.game.active_scene, "current_wave"):
                    # Add 1 because wave counts often start from 0 internally
                    current_wave = self.game.active_scene.current_wave
            self._wave = current_wave
        except AttributeError:
            # If attributes don't exist, keep the last known wave or default
            self._wave = current_wave  # Reset to default if access fails
            # print("Warning: HUD could not determine current wave from active scene.")
            pass

        # --- Update Player Health (Safely) ---
        player_health = 0
        player_max_health = 0
        try:
            # Check if active_scene exists and has a 'player' attribute
            if self.game.active_scene and hasattr(self.game.active_scene, "player"):
                player = self.game.active_scene.player
                # Check if the player object has 'health' and 'max_health'
                if (
                    player
                    and hasattr(player, "health")
                    and hasattr(player, "max_health")
                ):
                    player_health = player.health
                    player_max_health = player.max_health
            self._player_health = player_health
            self._player_max_health = player_max_health
        except AttributeError:
            # If attributes don't exist, keep last known values or reset
            self._player_health = 0
            self._player_max_health = 0
            # print("Warning: HUD could not determine player health from active scene.")
            pass
        # --- 更新盾牌数量（安全获取）---
        shield_count = 0
        try:
            if self.game.active_scene and hasattr(self.game.active_scene, "player"):
                player = self.game.active_scene.player
                if player and hasattr(player, "shield_count"):
                    shield_count = player.shield_count
            self._shield_count = shield_count
        except AttributeError:
            self._shield_count = 0
            # print("警告：无法从当前场景获取玩家盾牌数量")

    def draw(self, surface):
        """
        Renders the HUD elements onto the given surface using internally stored state.
        """
        # --- Draw Score ---
        score_text_surface = self.font.render(
            f"SCORE: {self._score}", True, (255, 255, 255)
        )
        score_rect = score_text_surface.get_rect(topleft=(20, 20))
        surface.blit(score_text_surface, score_rect)

        # --- Draw Wave ---
        wave_text_surface = self.font.render(
            f"WAVE: {self._wave}", True, (255, 255, 255)
        )
        # Position from top right
        wave_rect = wave_text_surface.get_rect(topright=(Config.WIDTH - 20, 20))
        surface.blit(wave_text_surface, wave_rect)

        # --- Draw Combo (if active) ---
        if self._combo > self.combo_display_threshold:
            combo_text_surface = self.combo_font.render(
                f"{self._combo} COMBO!", True, self.combo_color
            )
            # Center the combo text using get_rect
            combo_rect = combo_text_surface.get_rect(center=self.combo_position)
            surface.blit(combo_text_surface, combo_rect)

        # --- Draw Player Health ---
        # Only draw if max_health is known (greater than 0)
        if self._player_max_health > 0:
            health_bar_start_x = 20
            health_bar_y = Config.HEIGHT - 35  # Position near bottom left
            segment_width = 30  # Width of each health segment
            segment_height = 15
            spacing = 5  # Space between segments

            for i in range(self._player_max_health):
                # Determine color based on current health
                color = (
                    (0, 200, 0) if i < self._player_health else (80, 80, 80)
                )  # Green if healthy, Grey if lost

                # Draw rectangle for health segment
                segment_rect = pygame.Rect(
                    health_bar_start_x + i * (segment_width + spacing),
                    health_bar_y,
                    segment_width,
                    segment_height,
                )
                pygame.draw.rect(surface, color, segment_rect)
                pygame.draw.rect(
                    surface, (200, 200, 200), segment_rect, 1
                )  # Optional border
        # --- 绘制盾牌数量（左下角）---
        shield_text = self.font.render(
            f"SHIELDS: {self._shield_count}", True, (0, 120, 255)  # 使用蓝色突出显示
        )
        # 位置：左下角（生命条上方）
        shield_rect = shield_text.get_rect(bottomleft=(20, Config.HEIGHT - 40))
        surface.blit(shield_text, shield_rect)


# --- How to integrate with Game loop ---
# In your main Game class's run() method, BEFORE rendering the scene:

# # Inside Game.run() loop:
# milliseconds = self.clock.tick(Config.FPS)
# self.dt = milliseconds / 1000.0
# self.handle_events()

# # Update the HUD state BEFORE updating the active scene
# # (or after, depending if you want this frame's or last frame's data)
# # Updating before scene update might show slightly delayed info (score from last frame)
# # Updating after scene update shows this frame's info but before rendering
# # Let's update it AFTER scene update but BEFORE render:
# if self.active_scene:
#     self.active_scene.update(self.dt)

# # <<< Add HUD update here >>>
# if hasattr(self, 'hud'): # Check if HUD exists
#      self.hud.update(self.dt)
# # <<< End HUD update >>>


# # --- Rendering ---
# render_offset = ... # Calculate shake
# if self.active_scene:
#     self.render_surface.fill(Config.BG_COLOR)
#     self.active_scene.render(self.render_surface) # Scene renders game world
# else:
#     self.render_surface.fill(Config.BG_COLOR)

# # <<< Draw HUD onto the render surface AFTER scene render >>>
# if hasattr(self, 'hud'):
#      self.hud.draw(self.render_surface)
# # <<< End HUD draw >>>

# self.screen.blit(self.render_surface, render_offset) # Blit final image
# # ... rest of loop (FPS counter, display.flip)
