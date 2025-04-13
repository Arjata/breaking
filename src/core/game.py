import pygame
from pygame.locals import *
from .config import Config
from random import randint
from ..managers.score import ScoreManager
from OpenGL.GL import *
from OpenGL.GLU import *


# --- Game Class (Provided for context, assuming it has score_manager) ---
# (Using the optimized version from previous steps for context)
class Game:
    def __init__(self):
        pygame.init()
        self.render_texture = None
        try:
            self.screen = pygame.display.set_mode(
                (Config.WIDTH, Config.HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF
            )
            # Initialize OpenGL context
            glViewport(0, 0, Config.WIDTH, Config.HEIGHT)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluOrtho2D(0, Config.WIDTH, Config.HEIGHT, 0)  # Flip Y-axis
            glMatrixMode(GL_MODELVIEW)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glClearColor(*Config.BG_COLOR, 1.0)

            # Create render texture
            self.render_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.render_texture)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # Create render surface with alpha
            self.render_surface = pygame.Surface(
                (Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA
            ).convert_alpha()

            # Initial texture upload
            texture_data = pygame.image.tostring(self.render_surface, "RGBA", True)
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                Config.WIDTH,
                Config.HEIGHT,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                texture_data,
            )
        except pygame.error as e:
            print(f"OpenGL init failed: {e}, using fallback")
            self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
            self.render_surface = pygame.Surface(
                (Config.WIDTH, Config.HEIGHT)
            ).convert()
            self.render_texture = None

        pygame.display.set_caption(Config.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0.0
        self.fps_font = None
        if Config.SHOW_FPS:
            try:
                self.fps_font = pygame.font.SysFont("monospace", 18)
            except:
                self.fps_font = pygame.font.Font(None, 24)
        self.active_scene = None
        self.shake_intensity = 0
        self.shake_duration = 0.0

        try:
            self.score_manager = ScoreManager()
        except ImportError as e:
            print(f"Fatal Error: {e}")
            self.running = False

    def change_scene(self, new_scene):
        self.active_scene = new_scene
        print(f"Changed scene to: {type(new_scene).__name__}")
        # Potentially reset things or transition effects here

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            if self.active_scene:
                self.active_scene.handle_event(event)

    def run(self):
        # Initial scene setup (same as before)
        if not self.active_scene and self.running:
            try:
                initial_scene = GameScene(self)
                self.change_scene(initial_scene)
            except Exception as e:
                print(f"Scene init error: {e}")
                self.running = False

        while self.running:
            milliseconds = self.clock.tick(Config.FPS)
            self.dt = milliseconds / 1000.0
            self.handle_events()

            if self.active_scene:
                self.active_scene.update(self.dt)

            # Calculate screen shake offset
            render_offset = (0, 0)
            if self.shake_duration > 0:
                self.shake_duration -= self.dt
                render_offset = (
                    randint(-self.shake_intensity, self.shake_intensity),
                    randint(-self.shake_intensity, self.shake_intensity),
                )

            # Render to surface
            self.render_surface.fill(Config.BG_COLOR)
            if self.active_scene:
                self.active_scene.render(self.render_surface)

            # FPS rendering
            if Config.SHOW_FPS and self.fps_font:
                self._draw_fps(self.clock.get_fps())

            # OpenGL rendering
            if (
                self.screen.get_flags() & pygame.OPENGL
                and self.render_texture is not None
            ):
                # Upload surface to texture
                texture_data = pygame.image.tostring(self.render_surface, "RGBA", True)
                glBindTexture(GL_TEXTURE_2D, self.render_texture)
                glTexSubImage2D(
                    GL_TEXTURE_2D,
                    0,
                    0,
                    0,
                    Config.WIDTH,
                    Config.HEIGHT,
                    GL_RGBA,
                    GL_UNSIGNED_BYTE,
                    texture_data,
                )

                # Clear and draw textured quad
                glClear(GL_COLOR_BUFFER_BIT)
                glLoadIdentity()
                glTranslatef(render_offset[0], render_offset[1], 0)

                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, self.render_texture)
                glBegin(GL_QUADS)
                glTexCoord2f(0, 1)  # 左上纹理坐标
                glVertex2f(0, 0)  # 左上顶点
                glTexCoord2f(1, 1)  # 右上纹理坐标
                glVertex2f(Config.WIDTH, 0)  # 右上顶点
                glTexCoord2f(1, 0)  # 右下纹理坐标
                glVertex2f(Config.WIDTH, Config.HEIGHT)  # 右下顶点
                glTexCoord2f(0, 0)  # 左下纹理坐标
                glVertex2f(0, Config.HEIGHT)  # 左下顶点
                glEnd()
                glDisable(GL_TEXTURE_2D)
            else:
                # Fallback to software rendering
                self.screen.blit(self.render_surface, render_offset)

            pygame.display.flip()

        pygame.quit()

    def _draw_fps(self, fps):
        # 现在绘制到render_surface而不是直接到屏幕
        text_surface = self.fps_font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        padding = 10
        text_rect.bottomright = (Config.WIDTH - padding, Config.HEIGHT - padding)
        self.render_surface.blit(text_surface, text_rect)

    def apply_screen_shake(self, intensity=5, duration=0.2):
        self.shake_intensity = max(0, intensity)
        self.shake_duration = max(0.0, duration)


# --- Scene Base Class (Provided for context) ---
class Scene:
    """场景基类（抽象类）"""

    def __init__(self, game):  # Ensure base class also accepts game
        self.game = game

    def handle_event(self, event):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def render(self, surface):
        raise NotImplementedError
